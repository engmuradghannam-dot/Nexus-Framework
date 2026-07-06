import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Check, ChevronDown, Plus } from 'lucide-react';
import { useTenant } from '../../hooks/useTenant';
import { api } from '../../services/api';

export default function TenantSwitcher() {
  const { tenant, tenants, switchTenant } = useTenant();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const handleSwitch = (t) => {
    switchTenant(t);
    setOpen(false);
    window.location.reload();
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <Building2 className="w-5 h-5 text-blue-600" />
        <div className="text-left">
          <p className="text-sm font-semibold text-gray-900">{tenant?.name || 'Select Tenant'}</p>
          <p className="text-xs text-gray-500">{tenant?.tier || 'Free'} Plan</p>
        </div>
        <ChevronDown className="w-4 h-4 text-gray-400" />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-72 bg-white rounded-xl shadow-xl border border-gray-200 z-50">
          <div className="p-2">
            <p className="text-xs font-medium text-gray-500 px-3 py-2">Your Organizations</p>
            {tenants.map((t) => (
              <button
                key={t.id}
                onClick={() => handleSwitch(t)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  t.id === tenant?.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'
                }`}
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-sm font-bold">
                  {t.name?.[0]}
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium">{t.name}</p>
                  <p className="text-xs text-gray-500">{t.slug}.nexus-erp.com</p>
                </div>
                {t.id === tenant?.id && <Check className="w-4 h-4 text-blue-600" />}
              </button>
            ))}
            <hr className="my-2" />
            <button
              onClick={() => navigate('/onboarding')}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 text-blue-600"
            >
              <Plus className="w-4 h-4" />
              <span className="text-sm font-medium">Create New Organization</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
