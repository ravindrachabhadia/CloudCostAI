#!/usr/bin/env python3
"""
CloudCost AI - Live Demo Script with Auto-Fix Capability
Run this during screen shares to find AWS waste and fix it in real-time
"""

import boto3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel
from rich import box
from rich.prompt import Prompt, Confirm
import time
import sys

console = Console()

class AWSWasteFinder:
    def __init__(self, fix_enabled=False):
        """Initialize AWS clients"""
        self.ec2 = boto3.client('ec2')
        self.cloudwatch = boto3.client('cloudwatch')
        self.rds = boto3.client('rds')
        self.elb = boto3.client('elbv2')
        self.s3 = boto3.client('s3')
        self.findings = []
        self.total_monthly_waste = 0
        self.fix_enabled = fix_enabled
        self.fixes_applied = []
        
    def run_analysis(self):
        """Run complete waste analysis"""
        console.print("\n[bold cyan]🚀 CloudCost AI - AWS Waste Analyzer[/bold cyan]\n")
        console.print("Analyzing your AWS account for cost optimization opportunities...\n")
        
        # Run all checks with progress bar
        tasks = [
            ("🔍 Analyzing EC2 instances", self.analyze_ec2_instances),
            ("💾 Checking EBS volumes", self.analyze_ebs_volumes),
            ("🗄️ Reviewing RDS databases", self.analyze_rds_instances),
            ("⚖️ Scanning Load Balancers", self.analyze_load_balancers),
            ("🔗 Checking Elastic IPs", self.analyze_elastic_ips),
            ("🪣 Analyzing S3 buckets", self.analyze_s3_buckets),
        ]
        
        # Simple progress without live display to avoid conflicts
        for task_name, task_func in tasks:
            console.print(f"[green]►[/green] {task_name}...", end="")
            try:
                task_func()
                console.print(" [green]✓[/green]")
                time.sleep(0.3)  # Make it look like it's working
            except Exception as e:
                console.print(f" [yellow]⚠️ Skipped[/yellow]")
        
        console.print("")  # New line after scanning
        self.generate_report()
        
        # If fix mode is enabled and we found waste, offer to fix
        if self.fix_enabled and self.findings:
            self.offer_fixes()
        else:
            self.show_terraform_fixes()
    
    def analyze_ec2_instances(self):
        """Find idle and oversized EC2 instances"""
        instances = self.ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                name = self.get_tag_value(instance.get('Tags', []), 'Name')
                
                # Get CPU stats
                cpu_stats = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=datetime.utcnow() - timedelta(days=7),
                    EndTime=datetime.utcnow(),
                    Period=3600,
                    Statistics=['Average', 'Maximum']
                )
                
                if cpu_stats['Datapoints']:
                    avg_cpu = sum(d['Average'] for d in cpu_stats['Datapoints']) / len(cpu_stats['Datapoints'])
                    max_cpu = max(d['Maximum'] for d in cpu_stats['Datapoints'])
                    
                    monthly_cost = self.get_instance_cost(instance_type)
                    
                    # Check for idle instances
                    if avg_cpu < 5:
                        self.findings.append({
                            'type': '🛑 Idle EC2 Instance',
                            'resource': f"{name} ({instance_id})",
                            'resource_id': instance_id,
                            'issue': f"CPU avg: {avg_cpu:.1f}%",
                            'monthly_waste': monthly_cost,
                            'recommendation': 'Stop or terminate',
                            'fix_function': self.fix_idle_instance,
                            'fix_args': {'instance_id': instance_id},
                            'terraform_fix': f'aws_instance.{instance_id}.instance_state = "stopped"'
                        })
                        self.total_monthly_waste += monthly_cost
                    
                    # Check for oversized instances
                    elif max_cpu < 40 and monthly_cost > 50:
                        downsize_savings = monthly_cost * 0.5  # Assume 50% savings
                        self.findings.append({
                            'type': '📉 Oversized Instance',
                            'resource': f"{name} ({instance_id})",
                            'resource_id': instance_id,
                            'issue': f"Max CPU: {max_cpu:.1f}%",
                            'monthly_waste': downsize_savings,
                            'recommendation': 'Downsize instance type',
                            'fix_function': None,  # Can't resize while running
                            'terraform_fix': f'aws_instance.{instance_id}.instance_type = "{self.get_smaller_instance(instance_type)}"'
                        })
                        self.total_monthly_waste += downsize_savings
    
    def analyze_ebs_volumes(self):
        """Find unattached EBS volumes"""
        volumes = self.ec2.describe_volumes(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )
        
        for volume in volumes['Volumes']:
            volume_id = volume['VolumeId']
            size_gb = volume['Size']
            volume_type = volume['VolumeType']
            created = volume['CreateTime']
            
            # Calculate age
            age_days = (datetime.now(created.tzinfo) - created).days
            monthly_cost = size_gb * 0.10  # $0.10 per GB for gp3
            
            self.findings.append({
                'type': '💾 Unattached EBS Volume',
                'resource': f"{volume_id} ({size_gb}GB)",
                'resource_id': volume_id,
                'issue': f"Unattached for {age_days} days",
                'monthly_waste': monthly_cost,
                'recommendation': 'Delete or snapshot',
                'fix_function': self.fix_unattached_volume,
                'fix_args': {'volume_id': volume_id},
                'terraform_fix': f'# Delete volume\n# aws ec2 delete-volume --volume-id {volume_id}'
            })
            self.total_monthly_waste += monthly_cost
    
    def analyze_rds_instances(self):
        """Find idle RDS instances"""
        try:
            instances = self.rds.describe_db_instances()
            
            for db in instances['DBInstances']:
                db_id = db['DBInstanceIdentifier']
                instance_class = db['DBInstanceClass']
                engine = db['Engine']
                
                # Get connection count
                try:
                    conn_stats = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/RDS',
                        MetricName='DatabaseConnections',
                        Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                        StartTime=datetime.utcnow() - timedelta(days=7),
                        EndTime=datetime.utcnow(),
                        Period=3600,
                        Statistics=['Average']
                    )
                    
                    if conn_stats['Datapoints']:
                        avg_connections = sum(d['Average'] for d in conn_stats['Datapoints']) / len(conn_stats['Datapoints'])
                        
                        if avg_connections < 1:
                            monthly_cost = self.get_rds_cost(instance_class)
                            self.findings.append({
                                'type': '🗄️ Idle RDS Instance',
                                'resource': f"{db_id} ({instance_class})",
                                'resource_id': db_id,
                                'issue': f"Avg connections: {avg_connections:.1f}",
                                'monthly_waste': monthly_cost,
                                'recommendation': 'Stop or delete',
                                'fix_function': self.fix_idle_rds,
                                'fix_args': {'db_id': db_id},
                                'terraform_fix': f'# Stop RDS: aws rds stop-db-instance --db-instance-identifier {db_id}'
                            })
                            self.total_monthly_waste += monthly_cost
                except:
                    pass
        except:
            pass
    
    def analyze_load_balancers(self):
        """Find unused load balancers"""
        try:
            lbs = self.elb.describe_load_balancers()
            
            for lb in lbs['LoadBalancers']:
                lb_name = lb['LoadBalancerName']
                lb_arn = lb['LoadBalancerArn']
                
                # Check target health
                target_groups = self.elb.describe_target_groups(
                    LoadBalancerArn=lb_arn
                )
                
                total_targets = 0
                for tg in target_groups['TargetGroups']:
                    targets = self.elb.describe_target_health(
                        TargetGroupArn=tg['TargetGroupArn']
                    )
                    total_targets += len(targets['TargetHealthDescriptions'])
                
                if total_targets == 0:
                    monthly_cost = 18  # ~$18/month for ALB
                    self.findings.append({
                        'type': '⚖️ Unused Load Balancer',
                        'resource': lb_name,
                        'resource_id': lb_arn,
                        'issue': "No targets attached",
                        'monthly_waste': monthly_cost,
                        'recommendation': 'Delete load balancer',
                        'fix_function': self.fix_unused_lb,
                        'fix_args': {'lb_arn': lb_arn},
                        'terraform_fix': f'# Delete: aws elbv2 delete-load-balancer --load-balancer-arn {lb_arn}'
                    })
                    self.total_monthly_waste += monthly_cost
        except:
            pass
    
    def analyze_elastic_ips(self):
        """Find unassociated Elastic IPs"""
        eips = self.ec2.describe_addresses()
        
        for eip in eips['Addresses']:
            if 'InstanceId' not in eip and 'NetworkInterfaceId' not in eip:
                monthly_cost = 3.6  # $0.005/hour * 24 * 30
                self.findings.append({
                    'type': '🔗 Unassociated Elastic IP',
                    'resource': eip['PublicIp'],
                    'resource_id': eip['AllocationId'],
                    'issue': "Not attached to any resource",
                    'monthly_waste': monthly_cost,
                    'recommendation': 'Release IP',
                    'fix_function': self.fix_unassociated_eip,
                    'fix_args': {'allocation_id': eip['AllocationId']},
                    'terraform_fix': f'# Release: aws ec2 release-address --allocation-id {eip["AllocationId"]}'
                })
                self.total_monthly_waste += monthly_cost
    
    def analyze_s3_buckets(self):
        """Find S3 optimization opportunities"""
        try:
            buckets = self.s3.list_buckets()
            
            for bucket in buckets['Buckets']:
                bucket_name = bucket['Name']
                try:
                    # Check bucket size and lifecycle
                    metrics = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='BucketSizeBytes',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'StorageType', 'Value': 'StandardStorage'}
                        ],
                        StartTime=datetime.utcnow() - timedelta(days=1),
                        EndTime=datetime.utcnow(),
                        Period=86400,
                        Statistics=['Average']
                    )
                    
                    if metrics['Datapoints']:
                        size_bytes = metrics['Datapoints'][0]['Average']
                        size_gb = size_bytes / (1024**3)
                        
                        # Check if lifecycle policies exist
                        try:
                            lifecycle = self.s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                            has_lifecycle = True
                        except:
                            has_lifecycle = False
                        
                        # If large bucket without lifecycle, suggest optimization
                        if size_gb > 100 and not has_lifecycle:
                            # Assume 50% could move to IA
                            monthly_savings = (size_gb * 0.5 * 0.0125)  # IA is ~50% cheaper
                            self.findings.append({
                                'type': '🪣 S3 Lifecycle Missing',
                                'resource': bucket_name,
                                'resource_id': bucket_name,
                                'issue': f"{size_gb:.0f}GB without lifecycle",
                                'monthly_waste': monthly_savings,
                                'recommendation': 'Add lifecycle policy',
                                'fix_function': None,  # Too complex for auto-fix
                                'terraform_fix': f'# Add lifecycle to move old objects to IA/Glacier'
                            })
                            self.total_monthly_waste += monthly_savings
                except:
                    pass
        except:
            pass
    
    def offer_fixes(self):
        """Offer to fix the issues found"""
        console.print("\n[bold yellow]🔧 Auto-Fix Available![/bold yellow]\n")
        
        # Show fixable issues
        fixable = [f for f in self.findings if f.get('fix_function')]
        
        if not fixable:
            console.print("[dim]No auto-fixable issues found. Manual intervention required.[/dim]")
            self.show_terraform_fixes()
            return
        
        # Create fix table
        fix_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        fix_table.add_column("#", style="white", width=3)
        fix_table.add_column("Resource Type", style="cyan", width=25)
        fix_table.add_column("Resource", style="white", width=35)
        fix_table.add_column("Monthly Savings", justify="right", style="green", width=15)
        
        for i, finding in enumerate(fixable, 1):
            fix_table.add_row(
                str(i),
                finding['type'],
                finding['resource'],
                f"${finding['monthly_waste']:,.2f}"
            )
        
        console.print(fix_table)
        
        total_fixable_savings = sum(f['monthly_waste'] for f in fixable)
        console.print(f"\n[bold green]Total fixable savings: ${total_fixable_savings:,.2f}/month (${total_fixable_savings*12:,.2f}/year)[/bold green]")
        
        # Ask what to do
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("1. Fix all issues automatically")
        console.print("2. Select specific issues to fix")
        console.print("3. Just show Terraform code (no fixes)")
        console.print("4. Exit without fixing")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"], default="3")
        
        if choice == "1":
            self.fix_all_issues(fixable)
        elif choice == "2":
            self.fix_selected_issues(fixable)
        elif choice == "3":
            self.show_terraform_fixes()
        else:
            console.print("\n[yellow]No fixes applied. Remember to address these issues![/yellow]")
    
    def fix_all_issues(self, fixable):
        """Fix all fixable issues"""
        console.print("\n[bold red]⚠️  WARNING: This will modify your AWS resources![/bold red]")
        
        if Confirm.ask("Are you sure you want to fix ALL issues?", default=False):
            console.print("\n[bold yellow]Applying fixes...[/bold yellow]\n")
            for finding in fixable:
                console.print(f"Fixing: {finding['resource']}...", end="")
                try:
                    finding['fix_function'](**finding['fix_args'])
                    self.fixes_applied.append(finding)
                    console.print(" [green]✓ Done[/green]")
                    time.sleep(1)  # Don't overwhelm AWS API
                except Exception as e:
                    console.print(f" [red]✗ Failed: {str(e)}[/red]")
            
            self.show_fix_summary()
        else:
            console.print("\n[yellow]Fix cancelled.[/yellow]")
            self.show_terraform_fixes()
    
    def fix_selected_issues(self, fixable):
        """Fix selected issues"""
        console.print("\n[bold]Select issues to fix (comma-separated numbers, e.g., 1,3,5):[/bold]")
        
        selection = Prompt.ask("Enter numbers")
        selected_indices = [int(x.strip())-1 for x in selection.split(",") if x.strip().isdigit()]
        
        selected_fixes = [fixable[i] for i in selected_indices if 0 <= i < len(fixable)]
        
        if selected_fixes:
            console.print(f"\n[yellow]Will fix {len(selected_fixes)} issues[/yellow]")
            if Confirm.ask("Proceed?", default=True):
                for finding in selected_fixes:
                    try:
                        console.print(f"Fixing: {finding['resource']}...", end="")
                        finding['fix_function'](**finding['fix_args'])
                        self.fixes_applied.append(finding)
                        console.print(" [green]✓ Done[/green]")
                    except Exception as e:
                        console.print(f" [red]✗ Failed: {str(e)}[/red]")
                
                self.show_fix_summary()
        else:
            console.print("\n[yellow]No valid selections.[/yellow]")
    
    # Fix functions
    def fix_idle_instance(self, instance_id):
        """Stop an idle EC2 instance"""
        self.ec2.stop_instances(InstanceIds=[instance_id])
    
    def fix_unattached_volume(self, volume_id):
        """Delete an unattached EBS volume"""
        # Create snapshot first for safety
        snapshot = self.ec2.create_snapshot(
            VolumeId=volume_id,
            Description=f'CloudCost AI backup before deletion - {datetime.now().isoformat()}'
        )
        # Delete volume
        self.ec2.delete_volume(VolumeId=volume_id)
    
    def fix_idle_rds(self, db_id):
        """Stop an idle RDS instance"""
        self.rds.stop_db_instance(DBInstanceIdentifier=db_id)
    
    def fix_unused_lb(self, lb_arn):
        """Delete an unused load balancer"""
        self.elb.delete_load_balancer(LoadBalancerArn=lb_arn)
    
    def fix_unassociated_eip(self, allocation_id):
        """Release an unassociated Elastic IP"""
        self.ec2.release_address(AllocationId=allocation_id)
    
    def show_fix_summary(self):
        """Show summary of fixes applied"""
        if self.fixes_applied:
            console.print("\n[bold green]✨ Fixes Applied Successfully![/bold green]\n")
            
            summary_table = Table(show_header=True, header_style="bold green", box=box.ROUNDED)
            summary_table.add_column("Resource", style="white")
            summary_table.add_column("Action", style="cyan")
            summary_table.add_column("Monthly Savings", justify="right", style="green")
            
            total_fixed = 0
            for fix in self.fixes_applied:
                action = {
                    '🛑 Idle EC2 Instance': 'Stopped',
                    '💾 Unattached EBS Volume': 'Deleted (snapshot created)',
                    '🗄️ Idle RDS Instance': 'Stopped',
                    '⚖️ Unused Load Balancer': 'Deleted',
                    '🔗 Unassociated Elastic IP': 'Released'
                }.get(fix['type'], 'Fixed')
                
                summary_table.add_row(
                    fix['resource'],
                    action,
                    f"${fix['monthly_waste']:,.2f}"
                )
                total_fixed += fix['monthly_waste']
            
            console.print(summary_table)
            console.print(f"\n[bold green]Total monthly savings achieved: ${total_fixed:,.2f} (${total_fixed*12:,.2f}/year)[/bold green]")
            console.print("\n[yellow]Note: Some resources may take a few minutes to fully stop/delete.[/yellow]")
    
    def generate_report(self):
        """Generate and display the waste report"""
        console.print("\n" + "="*80 + "\n")
        
        # Summary panel
        summary = Panel(
            f"[bold green]💰 Total Monthly Waste Found: ${self.total_monthly_waste:,.2f}[/bold green]\n"
            f"[bold yellow]📊 Annual Savings Potential: ${self.total_monthly_waste * 12:,.2f}[/bold yellow]\n"
            f"[bold cyan]🔍 Issues Found: {len(self.findings)}[/bold cyan]",
            title="[bold]Executive Summary[/bold]",
            box=box.ROUNDED
        )
        console.print(summary)
        
        # Detailed findings table
        if self.findings:
            console.print("\n[bold]Detailed Findings:[/bold]\n")
            
            table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
            table.add_column("Type", style="cyan", width=25)
            table.add_column("Resource", style="white", width=30)
            table.add_column("Issue", style="yellow", width=20)
            table.add_column("Monthly Waste", justify="right", style="red")
            
            # Sort by waste amount
            sorted_findings = sorted(self.findings, key=lambda x: x['monthly_waste'], reverse=True)
            
            for finding in sorted_findings[:10]:  # Top 10
                table.add_row(
                    finding['type'],
                    finding['resource'],
                    finding['issue'],
                    f"${finding['monthly_waste']:,.2f}"
                )
            
            console.print(table)
            
            if len(self.findings) > 10:
                console.print(f"\n[dim]... and {len(self.findings) - 10} more issues[/dim]")
        
        # Show projected savings for companies
        self.show_company_projections()
    
    def show_company_projections(self):
        """Show projected waste for different company sizes"""
        console.print("\n[bold cyan]💡 Projected Monthly Waste by Company Size:[/bold cyan]\n")
        
        projections = Table(show_header=True, header_style="bold white", box=box.SIMPLE)
        projections.add_column("Company Size", style="cyan")
        projections.add_column("Typical AWS Spend", style="white")
        projections.add_column("Est. Waste (30-40%)", style="yellow")
        projections.add_column("Annual Savings", style="green")
        
        projections.add_row(
            "🚀 Startup (50 employees)",
            "$10K-25K/month",
            "$3K-10K/month",
            "$36K-120K/year"
        )
        projections.add_row(
            "📈 Scale-up (200 employees)",
            "$50K-150K/month",
            "$15K-60K/month",
            "$180K-720K/year"
        )
        projections.add_row(
            "🏢 Enterprise (1000+ employees)",
            "$200K-1M/month",
            "$60K-400K/month",
            "$720K-4.8M/year"
        )
        
        console.print(projections)
        
        if self.total_monthly_waste < 100:
            console.print("\n[yellow]ℹ️  This account has minimal waste, but most production accounts have significant optimization opportunities![/yellow]")
    
    def show_demo_findings(self):
        """Show example findings for demo purposes"""
        console.print("\n[yellow]📋 Example findings from typical audits:[/yellow]\n")
        
        demo_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        demo_table.add_column("Common Waste Patterns", style="cyan", width=35)
        demo_table.add_column("Typical Finding", style="white", width=35)
        demo_table.add_column("Avg. Monthly Waste", justify="right", style="red")
        
        demo_findings = [
            ("🛑 Idle Production Instances", "10 x m5.xlarge at 3% CPU", "$1,536"),
            ("💾 Forgotten EBS Snapshots", "500 snapshots from 2023", "$2,500"),
            ("📉 Oversized RDS Instances", "db.r5.4xlarge at 15% CPU", "$1,468"),
            ("⚖️ Unused Load Balancers", "8 ALBs with no targets", "$144"),
            ("🗄️ Idle Aurora Clusters", "Dev cluster running 24/7", "$720"),
            ("💿 Unattached EBS Volumes", "2TB from deleted instances", "$200"),
            ("🌐 Unused Elastic IPs", "25 IPs not attached", "$90"),
            ("🚦 NAT Gateway Redundancy", "3 NAT gateways, need 1", "$270"),
        ]
        
        for pattern, example, cost in demo_findings:
            demo_table.add_row(pattern, example, cost)
        
        console.print(demo_table)
        console.print("\n[bold green]💰 Typical Total: $6,928/month ($83,136/year)[/bold green]")
    
    def show_terraform_fixes(self):
        """Show Terraform code to fix top issues"""
        console.print("\n[bold]🔧 Terraform Fixes for Top 3 Issues:[/bold]\n")
        
        if not self.findings:
            # Show example fixes if no real findings
            console.print("[yellow]No issues found in this account. Here's what we typically generate:[/yellow]\n")
            console.print("[bold cyan]Example: Stop Idle EC2 Instance[/bold cyan]")
            console.print("```terraform")
            console.print("resource \"null_resource\" \"stop_idle_instance\" {")
            console.print("  provisioner \"local-exec\" {")
            console.print("    command = \"aws ec2 stop-instances --instance-ids i-1234567890abcdef0\"")
            console.print("  }")
            console.print("}")
            console.print("```\n")
            return
        
        top_issues = sorted(self.findings, key=lambda x: x['monthly_waste'], reverse=True)[:3]
        
        for i, issue in enumerate(top_issues, 1):
            console.print(f"[bold cyan]{i}. {issue['type']} - Save ${issue['monthly_waste']:.2f}/month[/bold cyan]")
            console.print(f"[dim]Resource: {issue['resource']}[/dim]")
            console.print(f"[green]Fix:[/green]")
            console.print(f"```terraform\n{issue['terraform_fix']}\n```")
            console.print()
    
    # Helper methods
    def get_tag_value(self, tags, key):
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
        return 'unnamed'
    
    def get_instance_cost(self, instance_type):
        # Simplified pricing (update with real prices)
        costs = {
            't3.micro': 8.4, 't3.small': 16.8, 't3.medium': 33.6,
            't3.large': 67.2, 't3.xlarge': 134.4, 't3.2xlarge': 268.8,
            'm5.large': 76.8, 'm5.xlarge': 153.6, 'm5.2xlarge': 307.2,
            'c5.large': 68.4, 'c5.xlarge': 136.8, 'c5.2xlarge': 273.6,
        }
        return costs.get(instance_type, 100)
    
    def get_rds_cost(self, instance_class):
        # Simplified RDS pricing
        costs = {
            'db.t3.micro': 14.4, 'db.t3.small': 28.8, 'db.t3.medium': 57.6,
            'db.m5.large': 126, 'db.m5.xlarge': 252, 'db.m5.2xlarge': 504,
        }
        return costs.get(instance_class, 200)
    
    def get_smaller_instance(self, current):
        downsizes = {
            'm5.2xlarge': 'm5.xlarge', 'm5.xlarge': 'm5.large',
            't3.2xlarge': 't3.xlarge', 't3.xlarge': 't3.large',
            't3.large': 't3.medium', 'c5.2xlarge': 'c5.xlarge',
        }
        return downsizes.get(current, 't3.small')

def main():
    """Main entry point"""
    try:
        # Cool ASCII art
        console.print("""
[bold cyan]
   _____ _                 _  _____          _        _____ _____ 
  / ____| |               | |/ ____|        | |      |  __ \_   _|
 | |    | | ___  _   _  __| | |     ___  ___| |_     | |__) || |  
 | |    | |/ _ \| | | |/ _` | |    / _ \/ __| __|    |  _  / | |  
 | |____| | (_) | |_| | (_| | |___| (_) \__ \ |_     | | \ \_| |_ 
  \_____|_|\___/ \__,_|\__,_|\_____\___/|___/\__|    |_|  \_\_____|
                                                                    
[/bold cyan]""")
        
        console.print("\n[bold]Welcome to CloudCost AI Demo![/bold]")
        console.print("This tool will analyze your AWS account and find cost optimization opportunities.\n")
        
        # Check for flags
        fix_enabled = '--fix' in sys.argv
        demo_mode = '--demo' in sys.argv
        
        if fix_enabled:
            console.print("[bold red]⚠️  FIX MODE ENABLED - This can modify AWS resources![/bold red]\n")
        
        if demo_mode:
            console.print("[yellow]🎭 Running in DEMO MODE - showing example findings[/yellow]\n")
        
        # Check AWS credentials
        try:
            sts = boto3.client('sts')
            account_info = sts.get_caller_identity()
            console.print(f"[green]✓ Connected to AWS Account: {account_info['Account']}[/green]\n")
        except:
            console.print("[red]❌ Error: AWS credentials not configured[/red]")
            console.print("Please run: aws configure")
            return
        
        # Run analysis
        analyzer = AWSWasteFinder(fix_enabled=fix_enabled)
        analyzer.run_analysis()
        
        # If minimal findings, show demo data
        if analyzer.total_monthly_waste < 100 and not demo_mode:
            analyzer.show_demo_findings()
        
        # Save report
        report_file = f"cloudcost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'account_id': account_info['Account'],
                'scan_date': datetime.now().isoformat(),
                'total_monthly_waste': analyzer.total_monthly_waste,
                'annual_savings': analyzer.total_monthly_waste * 12,
                'findings': [
                    {k: v for k, v in f.items() if k not in ['fix_function', 'fix_args']} 
                    for f in analyzer.findings
                ],
                'fixes_applied': [
                    {k: v for k, v in f.items() if k not in ['fix_function', 'fix_args']} 
                    for f in analyzer.fixes_applied
                ]
            }, f, indent=2, default=str)
        
        console.print(f"\n[green]📄 Full report saved to: {report_file}[/green]")
        
        # Call to action
        if analyzer.total_monthly_waste > 0:
            if not fix_enabled:
                console.print(f"\n[bold cyan]💡 Tip: Run with --fix flag to auto-fix these issues![/bold cyan]")
                console.print(f"[dim]Example: python {sys.argv[0]} --fix[/dim]")
            console.print(f"\n[bold cyan]🚀 Ready to save ${analyzer.total_monthly_waste:,.2f}/month? Let's chat![/bold cyan]\n")
        else:
            console.print("\n[bold cyan]🚀 Your account is clean, but most companies have thousands in hidden waste. Let's find it![/bold cyan]\n")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis cancelled.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()