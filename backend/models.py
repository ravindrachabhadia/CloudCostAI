from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ScanStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ResourceType(str, Enum):
    EC2_IDLE = "🛑 Idle EC2 Instance"
    EBS_UNATTACHED = "💾 Unattached EBS Volume"
    RDS_IDLE = "🗄️ Idle RDS Instance"
    LB_UNUSED = "⚖️ Unused Load Balancer"
    EIP_UNASSOCIATED = "🔗 Unassociated Elastic IP"
    S3_LIFECYCLE = "🪣 S3 Lifecycle Missing"
    EC2_OVERSIZED = "📉 Oversized Instance"

class ScanRequest(BaseModel):
    account_name: Optional[str] = Field(default="AWS Account", description="Friendly name for the AWS account")
    include_fixes: bool = Field(default=False, description="Whether to enable auto-fix capabilities")
    regions: Optional[List[str]] = Field(default=None, description="AWS regions to scan (default: all)")

class Finding(BaseModel):
    id: Optional[str] = None
    type: str = Field(..., description="Type of waste found")
    resource: str = Field(..., description="Resource identifier")
    resource_id: str = Field(..., description="AWS resource ID")
    issue: str = Field(..., description="Description of the issue")
    monthly_waste: float = Field(..., ge=0, description="Monthly cost waste in USD")
    recommendation: str = Field(..., description="Recommended action")
    terraform_fix: Optional[str] = Field(None, description="Terraform code to fix the issue")
    severity: Optional[str] = Field(default="medium", description="Severity level: low, medium, high")
    region: Optional[str] = Field(None, description="AWS region")
    created_date: Optional[datetime] = None

class FixRequest(BaseModel):
    finding_ids: List[str] = Field(..., description="List of finding IDs to fix")
    dry_run: bool = Field(default=True, description="Whether to perform a dry run")

class ScanResultSummary(BaseModel):
    scan_id: str
    account_id: str
    account_name: str
    scan_date: datetime
    status: ScanStatus
    total_monthly_waste: float = Field(..., ge=0)
    annual_savings: float = Field(..., ge=0)
    findings_count: int = Field(..., ge=0)
    fixes_applied_count: int = Field(default=0, ge=0)

class ScanResult(BaseModel):
    scan_id: str
    account_id: str
    account_name: str
    scan_date: datetime
    status: ScanStatus
    total_monthly_waste: float = Field(..., ge=0)
    annual_savings: float = Field(..., ge=0)
    findings: List[Finding]
    fixes_applied: List[Finding] = []
    scan_duration_seconds: Optional[float] = None
    regions_scanned: List[str] = []

class ScanStatusResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    progress: int = Field(..., ge=0, le=100)
    message: str
    current_task: Optional[str] = None
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

class DashboardSummary(BaseModel):
    total_scans: int = Field(..., ge=0)
    total_monthly_waste: float = Field(..., ge=0)
    total_annual_savings: float = Field(..., ge=0)
    active_scans: int = Field(..., ge=0)
    recent_findings: List[Finding] = []
    waste_trend: List[Dict[str, Any]] = []

class WasteByType(BaseModel):
    type: str
    monthly_waste: float
    count: int
    percentage: float

class RegionAnalysis(BaseModel):
    region: str
    monthly_waste: float
    findings_count: int
    top_waste_type: Optional[str] = None

class HealthCheck(BaseModel):
    status: str
    aws_connected: bool
    account_id: Optional[str] = None
    regions_available: List[str] = []
    error: Optional[str] = None
    timestamp: datetime

class FixResult(BaseModel):
    finding_id: str
    success: bool
    message: str
    resource_id: str
    action_taken: Optional[str] = None
    error: Optional[str] = None

class BulkFixResponse(BaseModel):
    job_id: str
    total_fixes: int
    started_at: datetime
    estimated_duration_minutes: int
    results: List[FixResult] = []

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None 