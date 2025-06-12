from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import boto3
import json
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import os
from pathlib import Path

# Import our existing analysis logic
import sys
sys.path.append('..')
from cloudcost_demo import AWSWasteFinder

app = FastAPI(
    title="CloudCost AI API",
    description="AWS Cost Optimization Analysis API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# In-memory storage for demo (use database in production)
analysis_results = {}
scan_status = {}

# Pydantic models
class ScanRequest(BaseModel):
    account_name: Optional[str] = "AWS Account"
    include_fixes: bool = False

class Finding(BaseModel):
    type: str
    resource: str
    resource_id: str
    issue: str
    monthly_waste: float
    recommendation: str
    terraform_fix: Optional[str] = None

class ScanResult(BaseModel):
    scan_id: str
    account_id: str
    account_name: str
    scan_date: datetime
    status: str
    total_monthly_waste: float
    annual_savings: float
    findings: List[Finding]
    fixes_applied: List[Finding] = []

class ScanStatus(BaseModel):
    scan_id: str
    status: str  # 'running', 'completed', 'failed'
    progress: int  # 0-100
    message: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "CloudCost AI API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Detailed health check"""
    try:
        # Try to create AWS client to verify credentials
        sts = boto3.client('sts')
        account_info = sts.get_caller_identity()
        return {
            "status": "healthy",
            "aws_connected": True,
            "account_id": account_info['Account']
        }
    except Exception as e:
        return {
            "status": "degraded",
            "aws_connected": False,
            "error": str(e)
        }

@app.post("/scans", response_model=Dict[str, str])
async def start_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """Start a new AWS cost analysis scan"""
    scan_id = str(uuid.uuid4())
    
    # Initialize scan status
    scan_status[scan_id] = {
        "scan_id": scan_id,
        "status": "running",
        "progress": 0,
        "message": "Starting analysis..."
    }
    
    # Start background task
    background_tasks.add_task(
        run_analysis_task,
        scan_id,
        scan_request.account_name,
        scan_request.include_fixes
    )
    
    return {"scan_id": scan_id, "message": "Scan started"}

@app.get("/scans/{scan_id}/status", response_model=ScanStatus)
async def get_scan_status(scan_id: str):
    """Get the status of a running scan"""
    if scan_id not in scan_status:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return scan_status[scan_id]

@app.get("/scans/{scan_id}/results", response_model=ScanResult)
async def get_scan_results(scan_id: str):
    """Get the results of a completed scan"""
    if scan_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Scan results not found")
    
    if scan_status.get(scan_id, {}).get("status") != "completed":
        raise HTTPException(status_code=400, detail="Scan not completed yet")
    
    return analysis_results[scan_id]

@app.get("/scans", response_model=List[Dict[str, Any]])
async def list_scans():
    """List all scans with their status"""
    scans = []
    for scan_id in scan_status:
        scan_info = scan_status[scan_id].copy()
        if scan_id in analysis_results:
            result = analysis_results[scan_id]
            scan_info.update({
                "total_monthly_waste": result["total_monthly_waste"],
                "findings_count": len(result["findings"])
            })
        scans.append(scan_info)
    
    return sorted(scans, key=lambda x: x.get("scan_date", ""), reverse=True)

@app.post("/scans/{scan_id}/apply-fixes")
async def apply_fixes(
    scan_id: str,
    fix_indices: List[int],
    background_tasks: BackgroundTasks
):
    """Apply selected fixes from a scan"""
    if scan_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Scan results not found")
    
    result = analysis_results[scan_id]
    findings = result["findings"]
    
    # Validate indices
    selected_fixes = []
    for idx in fix_indices:
        if 0 <= idx < len(findings):
            selected_fixes.append(findings[idx])
    
    if not selected_fixes:
        raise HTTPException(status_code=400, detail="No valid fixes selected")
    
    # Start fix application in background
    background_tasks.add_task(apply_fixes_task, scan_id, selected_fixes)
    
    return {"message": f"Applying {len(selected_fixes)} fixes"}

@app.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get dashboard summary data"""
    if not analysis_results:
        return {
            "total_scans": 0,
            "total_monthly_waste": 0,
            "total_annual_savings": 0,
            "active_scans": 0,
            "recent_findings": []
        }
    
    total_waste = sum(result["total_monthly_waste"] for result in analysis_results.values())
    active_scans = sum(1 for status in scan_status.values() if status["status"] == "running")
    
    # Get recent findings
    all_findings = []
    for result in analysis_results.values():
        all_findings.extend(result["findings"])
    
    # Sort by waste amount and take top 5
    recent_findings = sorted(all_findings, key=lambda x: x["monthly_waste"], reverse=True)[:5]
    
    return {
        "total_scans": len(analysis_results),
        "total_monthly_waste": total_waste,
        "total_annual_savings": total_waste * 12,
        "active_scans": active_scans,
        "recent_findings": recent_findings
    }

@app.get("/dashboard/waste-by-type")
async def get_waste_by_type():
    """Get waste breakdown by resource type"""
    waste_by_type = defaultdict(float)
    
    for result in analysis_results.values():
        for finding in result["findings"]:
            waste_by_type[finding["type"]] += finding["monthly_waste"]
    
    return dict(waste_by_type)

async def run_analysis_task(scan_id: str, account_name: str, include_fixes: bool):
    """Background task to run AWS analysis"""
    try:
        # Update status
        scan_status[scan_id].update({
            "status": "running",
            "progress": 10,
            "message": "Initializing AWS connections..."
        })
        
        # Create analyzer
        analyzer = AWSWasteFinder(fix_enabled=include_fixes)
        
        # Get account info
        sts = boto3.client('sts')
        account_info = sts.get_caller_identity()
        
        scan_status[scan_id].update({
            "progress": 20,
            "message": "Analyzing EC2 instances..."
        })
        
        analyzer.analyze_ec2_instances()
        
        scan_status[scan_id].update({
            "progress": 40,
            "message": "Checking EBS volumes..."
        })
        
        analyzer.analyze_ebs_volumes()
        
        scan_status[scan_id].update({
            "progress": 60,
            "message": "Reviewing RDS instances..."
        })
        
        analyzer.analyze_rds_instances()
        
        scan_status[scan_id].update({
            "progress": 80,
            "message": "Scanning Load Balancers and other resources..."
        })
        
        analyzer.analyze_load_balancers()
        analyzer.analyze_elastic_ips()
        analyzer.analyze_s3_buckets()
        
        # Prepare results
        findings = []
        for finding in analyzer.findings:
            findings.append(Finding(
                type=finding["type"],
                resource=finding["resource"],
                resource_id=finding["resource_id"],
                issue=finding["issue"],
                monthly_waste=finding["monthly_waste"],
                recommendation=finding["recommendation"],
                terraform_fix=finding.get("terraform_fix")
            ))
        
        result = {
            "scan_id": scan_id,
            "account_id": account_info['Account'],
            "account_name": account_name,
            "scan_date": datetime.now(),
            "status": "completed",
            "total_monthly_waste": analyzer.total_monthly_waste,
            "annual_savings": analyzer.total_monthly_waste * 12,
            "findings": findings,
            "fixes_applied": []
        }
        
        # Store results
        analysis_results[scan_id] = result
        
        # Update final status
        scan_status[scan_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Analysis complete. Found ${analyzer.total_monthly_waste:.2f}/month in potential savings."
        })
        
    except Exception as e:
        scan_status[scan_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Analysis failed: {str(e)}"
        })

async def apply_fixes_task(scan_id: str, selected_fixes: List[Dict]):
    """Background task to apply fixes"""
    try:
        analyzer = AWSWasteFinder(fix_enabled=True)
        applied_fixes = []
        
        for fix in selected_fixes:
            # This would apply the actual fixes
            # For demo, we'll just simulate
            applied_fixes.append(fix)
        
        # Update results with applied fixes
        if scan_id in analysis_results:
            analysis_results[scan_id]["fixes_applied"] = applied_fixes
            
    except Exception as e:
        print(f"Error applying fixes: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 