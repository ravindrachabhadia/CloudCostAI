import React from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box, 
  IconButton,
  Chip
} from '@mui/material';
import { 
  CloudQueue as CloudIcon,
  AttachMoney as MoneyIcon,
  History as HistoryIcon,
  Home as HomeIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Get health status
  const { data: healthData } = useQuery(
    'health',
    apiService.healthCheck,
    {
      refetchInterval: 30000, // Check every 30 seconds
      retry: false
    }
  );

  const navigationItems = [
    { 
      label: 'Dashboard', 
      path: '/', 
      icon: <HomeIcon />,
      active: location.pathname === '/'
    },
    { 
      label: 'Scan History', 
      path: '/history', 
      icon: <HistoryIcon />,
      active: location.pathname === '/history'
    }
  ];

  return (
    <AppBar position="static" elevation={2}>
      <Toolbar>
        {/* Logo and Title */}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <CloudIcon sx={{ mr: 2, fontSize: 32 }} />
          <Typography variant="h6" component="div" sx={{ fontWeight: 700 }}>
            CloudCost AI
          </Typography>
          <Chip 
            label="BETA" 
            color="secondary" 
            size="small" 
            sx={{ ml: 1, fontSize: '0.7rem' }}
          />
        </Box>

        {/* Navigation Items */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {navigationItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              sx={{
                backgroundColor: item.active ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                },
                borderRadius: 2,
                px: 2
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        {/* AWS Connection Status */}
        <Box sx={{ ml: 2 }}>
          <Chip
            icon={<CloudIcon />}
            label={
              healthData?.aws_connected 
                ? `AWS: ${healthData.account_id?.slice(-4) || 'Connected'}` 
                : 'AWS: Disconnected'
            }
            color={healthData?.aws_connected ? 'success' : 'error'}
            variant="outlined"
            size="small"
            sx={{ 
              color: 'white',
              borderColor: 'rgba(255, 255, 255, 0.3)',
              '& .MuiChip-icon': {
                color: 'white'
              }
            }}
          />
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar; 