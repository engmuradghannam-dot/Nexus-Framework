import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Drawer, List, ListItem,
  ListItemIcon, ListItemText, Box, CssBaseline, IconButton, Divider
} from '@mui/material';
import {
  Dashboard, Business, Inventory, Psychology,
  Gavel, AccountTree, Logout, People, PointOfSale,
  AccountTreeOutlined, Security, PrecisionManufacturing,
  AccountBalance, ShoppingCart, Apartment, History
} from '@mui/icons-material';
import { useAuth } from '../AuthContext';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/' },
  { text: 'Companies', icon: <Business />, path: '/companies' },
  { text: 'Inventory', icon: <Inventory />, path: '/inventory' },
  { text: 'Projects', icon: <AccountTree />, path: '/projects' },
  { text: 'HR', icon: <People />, path: '/hr' },
  { text: 'CRM', icon: <People />, path: '/crm' },
  { text: 'Sales', icon: <ShoppingCart />, path: '/sales' },
  { text: 'POS', icon: <PointOfSale />, path: '/pos' },
  { text: 'Accounting', icon: <AccountBalance />, path: '/accounting' },
  { text: 'Manufacturing', icon: <PrecisionManufacturing />, path: '/manufacturing' },
  { text: 'Workflow', icon: <AccountTreeOutlined />, path: '/workflow' },
  { text: 'Permissions', icon: <Security />, path: '/permissions' },
  { text: 'Regulations', icon: <Gavel />, path: '/regulations' },
  { text: 'AI Chat', icon: <Psychology />, path: '/ai' },
];

const adminMenuItems = [
  { text: 'Tenants', icon: <Apartment />, path: '/tenants' },
  { text: 'Audit Log', icon: <History />, path: '/audit' },
];

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Nexus Framework
          </Typography>
          {user && (
            <Typography variant="body2" sx={{ mr: 2 }}>
              {user.username}
            </Typography>
          )}
          <IconButton color="inherit" onClick={handleLogout} title="Sign out">
            <Logout />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <List>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.text}
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
          {user?.is_staff && (
            <>
              <Divider sx={{ my: 1 }} />
              {adminMenuItems.map((item) => (
                <ListItem
                  button
                  key={item.text}
                  component={Link}
                  to={item.path}
                  selected={location.pathname === item.path}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItem>
              ))}
            </>
          )}
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
