import React, { useState } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Alert,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Collapse
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Code as CodeIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { toast } from 'react-toastify';

import { apiService } from '../services/api';

const ScanResults = () => {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [expandedRow, setExpandedRow] = useState(null);

  const { data: scanStatus, isLoading: statusLoading } = useQuery(
    ['scan-status', scanId],
    () => apiService.getScanStatus(scanId),
    {
      refetchInterval: (data) => {
        return data?.status === 'running' ? 2000 : false;
      },
      enabled: !!scanId
    }
  );

  const { data: scanResults, isLoading: resultsLoading } = useQuery(
    ['scan-results', scanId],
    () => apiService.getScanResults(scanId),
    {
      enabled: scanStatus?.status === 'completed'
    }
  );

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount || 0);
  };

  const getSeverityColor = (wasteAmount) => {
    if (wasteAmount > 500) return 'error';
    if (wasteAmount > 100) return 'warning';
    return 'info';
  };

  if (statusLoading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="h6">Loading scan...</Typography>
        </Box>
      </Container>
    );
  }

  if (!scanStatus) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 4 }}>
          Scan not found
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Button onClick={() => navigate('/')} sx={{ mb: 2 }}>
          ← Back to Dashboard
        </Button>
        <Typography variant="h4" gutterBottom>
          Scan Results
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Scan ID: {scanId}
        </Typography>
      </Box>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ mr: 2 }}>
              Scan Status
            </Typography>
            <Chip
              icon={
                scanStatus.status === 'completed' ? <CheckIcon /> :
                scanStatus.status === 'failed' ? <ErrorIcon /> :
                <RefreshIcon />
              }
              label={scanStatus.status.toUpperCase()}
              color={
                scanStatus.status === 'completed' ? 'success' :
                scanStatus.status === 'failed' ? 'error' :
                'warning'
              }
            />
          </Box>

          {scanStatus.status === 'running' && (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {scanStatus.message}
              </Typography>
              <LinearProgress variant="determinate" value={scanStatus.progress} sx={{ mb: 1 }} />
              <Typography variant="caption" color="text.secondary">
                {scanStatus.progress}% complete
              </Typography>
            </>
          )}

          {scanStatus.status === 'failed' && (
            <Alert severity="error">{scanStatus.message}</Alert>
          )}
        </CardContent>
      </Card>

      {scanResults && (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="error">Monthly Waste</Typography>
                  <Typography variant="h4">
                    {formatCurrency(scanResults.total_monthly_waste)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="success.main">Annual Savings</Typography>
                  <Typography variant="h4">
                    {formatCurrency(scanResults.annual_savings)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Issues Found</Typography>
                  <Typography variant="h4">{scanResults.findings.length}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Optimization Opportunities
              </Typography>
              
              {scanResults.findings.length === 0 ? (
                <Alert severity="success">
                  No waste found! Your AWS account is well optimized.
                </Alert>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Type</TableCell>
                        <TableCell>Resource</TableCell>
                        <TableCell>Issue</TableCell>
                        <TableCell align="right">Monthly Waste</TableCell>
                        <TableCell>Recommendation</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {scanResults.findings.map((finding, index) => (
                        <React.Fragment key={index}>
                          <TableRow hover onClick={() => setExpandedRow(expandedRow === index ? null : index)} sx={{ cursor: 'pointer' }}>
                            <TableCell>
                              <Chip
                                label={finding.type}
                                size="small"
                                color={getSeverityColor(finding.monthly_waste)}
                              />
                            </TableCell>
                            <TableCell>{finding.resource}</TableCell>
                            <TableCell>{finding.issue}</TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" color="error">
                                {formatCurrency(finding.monthly_waste)}
                              </Typography>
                            </TableCell>
                            <TableCell>{finding.recommendation}</TableCell>
                            <TableCell align="center">
                              <IconButton size="small">
                                {expandedRow === index ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                              </IconButton>
                            </TableCell>
                          </TableRow>
                          
                          <TableRow>
                            <TableCell colSpan={6} sx={{ py: 0 }}>
                              <Collapse in={expandedRow === index}>
                                <Box sx={{ p: 2, backgroundColor: 'grey.50' }}>
                                  <Typography variant="subtitle2" gutterBottom>Details</Typography>
                                  <Typography variant="body2" paragraph>
                                    <strong>Resource ID:</strong> {finding.resource_id}
                                  </Typography>
                                  <Typography variant="body2" paragraph>
                                    <strong>Annual Impact:</strong> {formatCurrency(finding.monthly_waste * 12)}
                                  </Typography>
                                  {finding.terraform_fix && (
                                    <Box sx={{ mt: 2, p: 2, backgroundColor: 'grey.100', borderRadius: 1 }}>
                                      <Typography variant="subtitle2" gutterBottom>Terraform Fix:</Typography>
                                      <Typography variant="body2" component="pre" sx={{ fontSize: '0.8rem' }}>
                                        {finding.terraform_fix}
                                      </Typography>
                                    </Box>
                                  )}
                                </Box>
                              </Collapse>
                            </TableCell>
                          </TableRow>
                        </React.Fragment>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </Container>
  );
};

export default ScanResults; 