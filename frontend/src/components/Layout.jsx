import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Drawer, List, ListItem,
  ListItemIcon, ListItemText, Box, CssBaseline, IconButton,
  Avatar, Menu, MenuItem, Divider, Badge, Tooltip
} from '@mui/material';
import {
  Dashboard, Business, Inventory, Psychology,
  Gavel, AccountTree, Logout, Person, Notifications,
  PointOfSale, Groups, AccountBalance, Engineering,
  AssignmentTurnedIn, Security, Assessment,
  DarkMode, LightMode
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { useThemeMode } from '../context/ThemeContext';

const drawerWidth = 260;

const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/' },
  { text: 'Companies', icon: <Business />, path: '/companies' },
  { text: 'Inventory', icon: <Inventory />, path: '/inventory' },
  { text: 'Projects', icon: <AccountTree />, path: '/projects' },
  { text: 'AI Chat', icon: <Psychology />, path: '/ai' },
  { text: 'Regulations', icon: <Gavel />, path: '/regulations' },
  { text: 'HR', icon: <Groups />, path: '/hr' },
  { text: 'POS', icon: <PointOfSale />, path: '/pos' },
  { text: 'Workflow', icon: <AssignmentTurnedIn />, path: '/workflow' },
  { text: 'Permissions', icon: <Security />, path: '/permissions' },
  { text: 'Manufacturing', icon: <Engineering />, path: '/manufacturing' },
  { text: 'Accounting', icon: <AccountBalance />, path: '/accounting' },
  { text: 'Reports', icon: <Assessment />, path: '/reports' },
];

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { mode, toggleTheme } = useThemeMode();
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleMenuOpen = (event) => setAnchorEl(event.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleMenuClose();
  };

  const userInitials = user?.username ? user.username.substring(0, 2).toUpperCase() : 'U';
  const isDark = mode === 'dark';

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar position="fixed" sx={{ 
        zIndex: (theme) => theme.zIndex.drawer + 1, 
        bgcolor: isDark ? '#1a1a2e' : '#1a237e',
        transition: 'background-color 0.3s ease'
      }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            ⚡ Nexus Framework
          </Typography>

          <Tooltip title={isDark ? "Light Mode" : "Dark Mode"}>
            <IconButton color="inherit" onClick={toggleTheme} sx={{ mr: 1 }}>
              {isDark ? <LightMode /> : <DarkMode />}
            </IconButton>
          </Tooltip>

          <IconButton color="inherit" sx={{ mr: 1 }}>
            <Badge badgeContent={3} color="error">
              <Notifications />
            </Badge>
          </IconButton>

          <IconButton onClick={handleMenuOpen} color="inherit" sx={{ ml: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: '#764ba2', fontSize: 14 }}>
              {userInitials}
            </Avatar>
          </IconButton>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          >
            <MenuItem disabled>
              <Person sx={{ mr: 1 }} /> {user?.username || 'User'}
            </MenuItem>
            <Divider />
            <MenuItem onClick={toggleTheme}>
              {isDark ? <LightMode sx={{ mr: 1 }} /> : <DarkMode sx={{ mr: 1 }} />}
              {isDark ? 'Light Mode' : 'Dark Mode'}
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <Logout sx={{ mr: 1, color: 'error.main' }} /> 
              <Typography color="error">Logout</Typography>
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { 
            width: drawerWidth, 
            boxSizing: 'border-box',
            bgcolor: isDark ? '#1e1e1e' : '#f8f9fa',
            borderRight: isDark ? '1px solid #333' : '1px solid #e0e0e0',
            transition: 'background-color 0.3s ease'
          },
        }}
      >
        <Toolbar />
        <List sx={{ px: 1 }}>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.text}
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                color: isDark ? '#e0e0e0' : 'inherit',
                '&.Mui-selected': {
                  bgcolor: 'primary.main',
                  color: 'white',
                  '& .MuiListItemIcon-root': { color: 'white' },
                },
                '&:hover': {
                  bgcolor: location.pathname === item.path ? 'primary.main' : (isDark ? '#333' : '#e3f2fd'),
                }
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: location.pathname === item.path ? 'white' : 'primary.main' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text} 
                primaryTypographyProps={{ fontWeight: location.pathname === item.path ? 'bold' : 'medium' }}
              />
            </ListItem>
          ))}
        </List>
      </Drawer>

      <Box component="main" sx={{ 
        flexGrow: 1, 
        p: 3, 
        bgcolor: isDark ? '#121212' : '#f5f5f5', 
        minHeight: '100vh',
        transition: 'background-color 0.3s ease'
      }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
