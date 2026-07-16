import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { getCompanies, getProjects, getInventory, getNeedsReorder, getRegulations } from './api';

const Dashboard = () => {
    const [stats, setStats] = useState({companies: 0, projects: 0, inventory: 0, reorder: 0, regulations: 0});

    useEffect(() => {
        const loadStats = async () => {
            try {
                const [companies, projects, inventory, reorder, regulations] = await Promise.all([
                    getCompanies(), getProjects(), getInventory(), getNeedsReorder(), getRegulations()
                ]);
                setStats({
                    companies: companies.data.length,
                    projects: projects.data.length,
                    inventory: inventory.data.length,
                    reorder: reorder.data.length,
                    regulations: regulations.data.length
                });
            } catch (e) {
                console.error(e);
            }
        };
        loadStats();
    }, []);

    return (
        <div>
            <h1>Nexus Framework Dashboard</h1>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px'}}>
                <div style={{padding: '20px', border: '1px solid #ccc', borderRadius: '8px'}}>
                    <h3>Companies</h3><p style={{fontSize: '2em'}}>{stats.companies}</p>
                </div>
                <div style={{padding: '20px', border: '1px solid #ccc', borderRadius: '8px'}}>
                    <h3>Projects</h3><p style={{fontSize: '2em'}}>{stats.projects}</p>
                </div>
                <div style={{padding: '20px', border: '1px solid #ccc', borderRadius: '8px'}}>
                    <h3>Inventory Items</h3><p style={{fontSize: '2em'}}>{stats.inventory}</p>
                </div>
                <div style={{padding: '20px', border: '1px solid red', borderRadius: '8px', background: '#ffebee'}}>
                    <h3>Needs Reorder</h3><p style={{fontSize: '2em', color: 'red'}}>{stats.reorder}</p>
                </div>
                <div style={{padding: '20px', border: '1px solid #ccc', borderRadius: '8px'}}>
                    <h3>Regulations</h3><p style={{fontSize: '2em'}}>{stats.regulations}</p>
                </div>
            </div>
        </div>
    );
};

const App = () => {
    return (
        <BrowserRouter>
            <div>
                <nav style={{padding: '10px', background: '#333', color: 'white'}}>
                    <Link to="/" style={{color: 'white', marginRight: '20px'}}>Dashboard</Link>
                    <Link to="/companies" style={{color: 'white', marginRight: '20px'}}>Companies</Link>
                    <Link to="/inventory" style={{color: 'white', marginRight: '20px'}}>Inventory</Link>
                    <Link to="/ai" style={{color: 'white'}}>AI Chat</Link>
                </nav>
                <div style={{padding: '20px'}}>
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/companies" element={<div><h2>Companies</h2></div>} />
                        <Route path="/inventory" element={<div><h2>Inventory</h2></div>} />
                        <Route path="/ai" element={<div><h2>AI Chat</h2></div>} />
                    </Routes>
                </div>
            </div>
        </BrowserRouter>
    );
};

export default App;
