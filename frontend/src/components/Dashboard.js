import React, { useState } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Paper
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  MonetizationOn as MoneyIcon,
  Storage as StorageIcon,
  PlayArrow as PlayIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

import { apiService } from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Dashboard = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [scanDialogOpen, setScanDialogOpen] = useState(false);
  const [scanConfig, setScanConfig] = useState({
    account_name: 'AWS Account',
    include_fixes: false
  });

  // Fetch dashboard data
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery(
    'dashboard-summary',
    apiService.getDashboardSummary,
    {
      refetchInterval: 10000
    }
  );

  const { data: wasteByType, isLoading: wasteLoading } = useQuery(
    'waste-by-type',
    apiService.getWasteByType
  );

  // Start scan mutation
  const startScanMutation = useMutation(
    apiService.startScan,
    {
      onSuccess: (data) => {
        toast.success('Scan started successfully!');
        setScanDialogOpen(false);
        navigate(`/scan/${data.scan_id}`);
        queryClient.invalidateQueries('dashboard-summary');
      },
      onError: (error) => {
        toast.error(`Failed to start scan: ${error.response?.data?.detail || error.message}`);
      }
    }
  );

  const handleStartScan = () => {
    startScanMutation.mutate(scanConfig);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const pieData = wasteByType ? Object.entries(wasteByType).map(([type, amount]) => ({
    name: type.replace(/[🛑💾🗄️⚖️🔗🪣📉]/g, '').trim(),
    value: amount,
    fullName: type
  })) : [];

  if (summaryError) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 2 }}>
          Error loading dashboard: {summaryError.message}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          CloudCost AI Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor and optimize your AWS costs in real-time
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <MoneyIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="h6">Monthly Waste</Typography>
              </Box>
              {summaryLoading ? (
                <CircularProgress size={20} />
              ) : (
                <Typography variant="h4" color="error">
                  {formatCurrency(summary?.total_monthly_waste)}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Annual Savings</Typography>
              </Box>
              {summaryLoading ? (
                <CircularProgress size={20} />
              ) : (
                <Typography variant="h4" color="success.main">
                  {formatCurrency(summary?.total_annual_savings)}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <StorageIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Scans</Typography>
              </Box>
              {summaryLoading ? (
                <CircularProgress size={20} />
              ) : (
                <Typography variant="h4">
                  {summary?.total_scans || 0}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <RefreshIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">Active Scans</Typography>
              </Box>
              {summaryLoading ? (
                <CircularProgress size={20} />
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="h4" sx={{ mr: 1 }}>
                    {summary?.active_scans || 0}
                  </Typography>
                  {(summary?.active_scans || 0) > 0 && (
                    <Chip label="Running" color="warning" size="small" />
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Waste by Resource Type
              </Typography>
              {wasteLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${formatCurrency(value)}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  No data available. Run a scan to see waste breakdown.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Start New Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Run a comprehensive AWS cost analysis to identify optimization opportunities.
              </Typography>
              
              <Button
                variant="contained"
                size="large"
                startIcon={<PlayIcon />}
                onClick={() => setScanDialogOpen(true)}
                disabled={startScanMutation.isLoading}
                fullWidth
                sx={{ mb: 2 }}
              >
                {startScanMutation.isLoading ? 'Starting Scan...' : 'Start New Scan'}
              </Button>

              {summary?.active_scans > 0 && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  {summary.active_scans} scan(s) currently running
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={scanDialogOpen} onClose={() => setScanDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure New Scan</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Account Name"
            value={scanConfig.account_name}
            onChange={(e) => setScanConfig({ ...scanConfig, account_name: e.target.value })}
            margin="normal"
            helperText="Friendly name for this AWS account"
          />
          <FormControlLabel
            control={
              <Switch
                checked={scanConfig.include_fixes}
                onChange={(e) => setScanConfig({ ...scanConfig, include_fixes: e.target.checked })}
              />
            }
            label="Enable Auto-Fix Capabilities"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScanDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleStartScan}
            variant="contained"
            disabled={startScanMutation.isLoading}
          >
            {startScanMutation.isLoading ? 'Starting...' : 'Start Scan'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Dashboard; 