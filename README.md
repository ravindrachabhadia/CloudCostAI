# CloudCost AI - AWS Cost Optimization Platform

A modern web application that analyzes your AWS infrastructure and identifies cost optimization opportunities in real-time.

## 🚀 Features

- **Real-time AWS Analysis**: Scan your entire AWS account for cost optimization opportunities
- **Interactive Dashboard**: Beautiful, modern UI built with React and Material-UI
- **Live Progress Tracking**: Watch scans in real-time with progress indicators
- **Detailed Findings**: Comprehensive breakdown of waste by resource type
- **Terraform Integration**: Auto-generate Terraform code to fix issues
- **Cost Projections**: See potential monthly and annual savings
- **Scan History**: Track all your previous analyses

## 🛠 Architecture

- **Backend**: FastAPI (Python) - RESTful API for AWS analysis
- **Frontend**: React.js with Material-UI - Modern, responsive dashboard
- **AWS Integration**: Boto3 for AWS service integration
- **Real-time Updates**: WebSocket-like polling for live scan updates

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- AWS CLI configured with appropriate permissions
- AWS IAM permissions for:
  - EC2 (describe instances, volumes)
  - RDS (describe instances)
  - CloudWatch (get metrics)
  - ELB (describe load balancers)
  - S3 (list buckets, get metrics)

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
python main.py
```

The backend API will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the React development server
npm start
```

The frontend will be available at `http://localhost:3000`

### 3. AWS Configuration

Ensure your AWS credentials are configured:

```bash
aws configure
```

Or set environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## 🎯 Usage

1. **Start a Scan**: Click "Start New Scan" on the dashboard
2. **Monitor Progress**: Watch real-time progress as CloudCost AI analyzes your AWS resources
3. **Review Findings**: See detailed breakdown of optimization opportunities
4. **View Terraform Fixes**: Get auto-generated infrastructure-as-code solutions
5. **Track History**: View all previous scans and their results

## 🔧 API Endpoints

### Health Check
- `GET /health` - Check API and AWS connectivity status

### Scans
- `POST /scans` - Start a new AWS analysis scan
- `GET /scans/{scan_id}/status` - Get scan progress and status
- `GET /scans/{scan_id}/results` - Get detailed scan results
- `GET /scans` - List all scans

### Dashboard
- `GET /dashboard/summary` - Get dashboard metrics
- `GET /dashboard/waste-by-type` - Get waste breakdown by resource type

## 📊 What CloudCost AI Analyzes

### EC2 Instances
- **Idle Instances**: CPU utilization < 5%
- **Oversized Instances**: Max CPU < 40% with high monthly cost

### EBS Volumes
- **Unattached Volumes**: Volumes not attached to any instance
- **Age Analysis**: How long volumes have been unattached

### RDS Instances
- **Idle Databases**: Low connection count over time
- **Underutilized Instances**: Performance vs cost analysis

### Load Balancers
- **Unused Load Balancers**: ALBs/ELBs with no targets

### Elastic IPs
- **Unassociated IPs**: Elastic IPs not attached to resources

### S3 Buckets
- **Missing Lifecycle Policies**: Large buckets without lifecycle management

## 💰 Cost Savings Examples

CloudCost AI typically finds:

- **Idle EC2 Instances**: $1,500+/month in wasted compute
- **Unattached EBS Volumes**: $200-500/month in storage waste  
- **Unused Load Balancers**: $18/month per unused ALB
- **Lifecycle Optimizations**: 30-50% storage cost reduction

## 🔒 Security Best Practices

- Use IAM roles with minimal required permissions
- Never hardcode AWS credentials
- Run scans from secure environments
- Review auto-fix recommendations before applying

## 🚦 Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 📈 Monitoring

The application includes:

- Health check endpoints
- Real-time scan progress tracking
- Error handling and reporting
- AWS connectivity monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (3.8+ required)
- Verify all dependencies are installed
- Ensure AWS credentials are configured

**Frontend won't start:**
- Check Node.js version (16+ required)
- Run `npm install` to install dependencies
- Check for port conflicts (3000)

**AWS Connection Issues:**
- Verify AWS credentials with `aws sts get-caller-identity`
- Check IAM permissions
- Ensure region is properly configured

### Support

For issues and questions:
- Check the GitHub issues page
- Review AWS CloudTrail for permission errors
- Verify network connectivity to AWS services

## 🚀 Production Deployment

For production deployment:

1. **Backend**: Deploy FastAPI with Gunicorn/Uvicorn
2. **Frontend**: Build with `npm run build` and serve static files
3. **Database**: Replace in-memory storage with PostgreSQL/MongoDB
4. **Security**: Add authentication and rate limiting
5. **Monitoring**: Add logging and metrics collection

Example production backend start:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🎉 Demo

Visit our live demo at [cloudcost-ai-demo.com](https://cloudcost-ai-demo.com) to see CloudCost AI in action!

---

**CloudCost AI** - Making AWS cost optimization simple and automated. 💰☁️ 