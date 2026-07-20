import React, { createContext, useContext, useEffect, useState } from 'react';
import { getSession, login as loginRequest, logoutSession } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getSession()
            .then((res) => setUser(res.data.authenticated ? res.data : null))
            .catch(() => setUser(null))
            .finally(() => setLoading(false));
    }, []);

    const login = async (username, password) => {
        const res = await loginRequest(username, password);
        setUser(res.data);
        return res.data;
    };

    const logout = async () => {
        await logoutSession();
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
    return ctx;
}
