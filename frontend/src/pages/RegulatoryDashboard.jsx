import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import api from '@/lib/api';

export default function RegulatoryDashboard() {
  const [frameworks, setFrameworks] = useState([]);
  const [rules, setRules] = useState([]);
  const [audits, setAudits] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [fwRes, ruleRes, auditRes] = await Promise.all([
        api.get('/regulatory/regulations/'),
        api.get('/regulatory/compliance-checks/'),
        api.get('/regulatory/risks/')
      ]);
      setFrameworks(fwRes.data.results || fwRes.data);
      setRules(ruleRes.data.results || ruleRes.data);
      setAudits(auditRes.data.results || auditRes.data);
    } catch (error) {
      console.error('Error fetching regulatory data:', error);
    }
  };

  const getComplianceStatus = (rate) => {
    if (rate >= 90) return 'bg-green-500';
    if (rate >= 70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Regulatory Compliance Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader><CardTitle>Regulations</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{frameworks.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Compliance Checks</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{rules.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Active Rules</CardTitle></CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-green-600">{rules.filter(r => r.is_active).length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Risks</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{audits.length}</p></CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>Compliance Frameworks</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {frameworks.map(fw => (
              <div key={fw.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium">{fw.name}</p>
                  <p className="text-sm text-gray-500">{fw.jurisdiction}</p>
                </div>
                <Badge className={getComplianceStatus(fw.compliance_rate || 0)}>{fw.compliance_rate || 0}%</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Recent Audit Logs</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {audits.slice(0, 5).map(audit => (
              <Alert key={audit.id} variant={audit.severity === 'high' ? 'destructive' : 'default'}>
                <AlertDescription>
                  <span className="font-medium">{audit.action}</span>
                  <span className="text-sm text-gray-500 ml-2">{audit.timestamp}</span>
                  <p className="text-sm">{audit.details}</p>
                </AlertDescription>
              </Alert>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
