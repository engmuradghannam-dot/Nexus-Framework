import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Companies from './pages/Companies';
import Inventory from './pages/Inventory';
import Projects from './pages/Projects';
import AIChat from './pages/AIChat';
import Regulations from './pages/Regulations';
import HR from './pages/HR';
import POS from './pages/POS';
import Workflow from './pages/Workflow';
import Permissions from './pages/Permissions';
import Accounting from './pages/Accounting';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#667eea' },
    secondary: { main: '#764ba2' },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/ai" element={<AIChat />} />
            <Route path="/regulations" element={<Regulations />} />
            <Route path="/hr" element={<HR />} />
            <Route path="/pos" element={<POS />} />
            <Route path="/workflow" element={<Workflow />} />
            <Route path="/permissions" element={<Permissions />} />
            <Route path="/accounting" element={<Accounting />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
