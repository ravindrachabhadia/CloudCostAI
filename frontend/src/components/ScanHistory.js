import React from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import moment from 'moment';

import { apiService } from '../services/api';

const ScanHistory = () => {
  const navigate = useNavigate();

  const { data: scans, isLoading, error } = useQuery(
    'scans-history',
    apiService.listScans,
    {
      refetchInterval: 10000 // Refresh every 10 seconds
    }
  );

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckIcon />;
      case 'failed':
        return <ErrorIcon />;
      case 'running':
        return <RefreshIcon />;
      default:
        return <RefreshIcon />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (error) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 4 }}>
          Error loading scan history: {error.message}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Scan History
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View all your previous AWS cost analysis scans
        </Typography>
      </Box>

      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Recent Scans
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate('/')}
            >
              Start New Scan
            </Button>
          </Box>

          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : !scans || scans.length === 0 ? (
            <Alert severity="info">
              No scans found. Start your first scan from the dashboard.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Scan ID</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Started</TableCell>
                    <TableCell align="right">Monthly Waste</TableCell>
                    <TableCell align="right">Findings</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scans.map((scan) => (
                    <TableRow key={scan.scan_id} hover>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {scan.scan_id.slice(0, 8)}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getStatusIcon(scan.status)}
                          label={scan.status.toUpperCase()}
                          color={getStatusColor(scan.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {moment(scan.started_at).format('MMM DD, YYYY HH:mm')}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {moment(scan.started_at).fromNow()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {scan.total_monthly_waste !== undefined ? (
                          <Typography variant="body2" color="error">
                            {formatCurrency(scan.total_monthly_waste)}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {scan.findings_count !== undefined ? (
                          <Typography variant="body2">
                            {scan.findings_count}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<ViewIcon />}
                          onClick={() => navigate(`/scan/${scan.scan_id}`)}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

export default ScanHistory; 