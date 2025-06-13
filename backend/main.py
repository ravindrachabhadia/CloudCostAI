from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import boto3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import sys
import os

# Add parent directory to path to import cloudcost_demo
sys.path.append('..')

app = FastAPI(
    title="CloudCost AI API",
    description="AWS Cost Optimization Analysis API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use database in production)
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

@app.get("/")
async def root():
    return {
        "message": "CloudCost AI API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    try:
        sts = boto3.client('sts')
        account_info = sts.get_caller_identity()
        return {
            "status": "healthy",
            "aws_connected": True,
            "account_id": account_info['Account'],
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "aws_connected": False,
            "error": str(e),
            "timestamp": datetime.now()
        }

@app.post("/scans")
async def start_scan(scan_request: ScanRequest, background_tasks: BackgroundTasks):
    scan_id = str(uuid.uuid4())
    
    # Initialize scan status
    scan_status[scan_id] = {
        "scan_id": scan_id,
        "status": "running",
        "progress": 0,
        "message": "Starting analysis...",
        "started_at": datetime.now()
    }
    
    # Start background task
    background_tasks.add_task(run_analysis_task, scan_id, scan_request)
    
    return {"scan_id": scan_id, "message": "Scan started"}

@app.get("/scans/{scan_id}/status")
async def get_scan_status(scan_id: str):
    if scan_id not in scan_status:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan_status[scan_id]

@app.get("/scans/{scan_id}/results")
async def get_scan_results(scan_id: str):
    if scan_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Scan results not found")
    
    if scan_status.get(scan_id, {}).get("status") != "completed":
        raise HTTPException(status_code=400, detail="Scan not completed yet")
    
    return analysis_results[scan_id]

@app.get("/scans")
async def list_scans():
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
    
    return sorted(scans, key=lambda x: x.get("started_at", ""), reverse=True)

@app.get("/dashboard/summary")
async def get_dashboard_summary():
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
    waste_by_type = defaultdict(float)
    
    for result in analysis_results.values():
        for finding in result["findings"]:
            waste_by_type[finding["type"]] += finding["monthly_waste"]
    
    return dict(waste_by_type)

async def run_analysis_task(scan_id: str, scan_request: ScanRequest):
    try:
        # Import here to avoid circular imports
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from cloudcost_demo import AWSWasteFinder
        
        # Update status
        scan_status[scan_id].update({
            "progress": 10,
            "message": "Initializing AWS connections..."
        })
        
        # Get account info
        sts = boto3.client('sts')
        account_info = sts.get_caller_identity()
        
        # Create analyzer
        analyzer = AWSWasteFinder(fix_enabled=scan_request.include_fixes)
        
        scan_status[scan_id].update({
            "progress": 20,
            "message": "Analyzing EC2 instances..."
        })
        
        # Run analysis steps
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
            "message": "Scanning other resources..."
        })
        
        analyzer.analyze_load_balancers()
        analyzer.analyze_elastic_ips()
        analyzer.analyze_s3_buckets()
        
        # Prepare findings
        findings = []
        for finding in analyzer.findings:
            findings.append({
                "type": finding["type"],
                "resource": finding["resource"],
                "resource_id": finding["resource_id"],
                "issue": finding["issue"],
                "monthly_waste": finding["monthly_waste"],
                "recommendation": finding["recommendation"],
                "terraform_fix": finding.get("terraform_fix")
            })
        
        # Store results
        result = {
            "scan_id": scan_id,
            "account_id": account_info['Account'],
            "account_name": scan_request.account_name,
            "scan_date": datetime.now(),
            "status": "completed",
            "total_monthly_waste": analyzer.total_monthly_waste,
            "annual_savings": analyzer.total_monthly_waste * 12,
            "findings": findings
        }
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 