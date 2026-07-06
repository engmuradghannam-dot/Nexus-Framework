import { useState, useEffect, createContext, useContext } from 'react';
import { api } from '../services/api';

const TenantContext = createContext(null);

export function TenantProvider({ children }) {
  const [tenant, setTenant] = useState(null);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const current = JSON.parse(localStorage.getItem('currentTenant') || 'null');
    if (current) setTenant(current);
    api.get('/tenants/').then((res) => {
      setTenants(res.data.results || []);
      if (!current && res.data.results?.length > 0) {
        setTenant(res.data.results[0]);
        localStorage.setItem('currentTenant', JSON.stringify(res.data.results[0]));
      }
      setLoading(false);
    });
  }, []);

  const switchTenant = (t) => {
    setTenant(t);
    localStorage.setItem('currentTenant', JSON.stringify(t));
    api.defaults.headers['X-Tenant-ID'] = t.id;
  };

  return (
    <TenantContext.Provider value={{ tenant, tenants, switchTenant, loading }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}
