import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import api from '@/lib/api';

const STATUS_STYLES = {
  present: 'text-emerald-400 bg-emerald-500/10',
  missing: 'text-red-400 bg-red-500/10',
  planned: 'text-amber-400 bg-amber-500/10',
};

const PRIORITY_STYLES = {
  High: 'text-red-400',
  Medium: 'text-amber-400',
  Low: 'text-nexus-400',
};

export default function Controls() {
  const [summary, setSummary] = useState(null);
  const [byForm, setByForm] = useState([]);
  const [industries, setIndustries] = useState([]);
  const [categories, setCategories] = useState([]);
  const [library, setLibrary] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [sumRes, formRes, indRes, catRes, libRes] = await Promise.all([
        api.get('/controls/form-controls/summary/'),
        api.get('/controls/form-controls/by_form/'),
        api.get('/controls/industries/'),
        api.get('/controls/industries/categories/'),
        api.get('/controls/industry-controls/'),
      ]);
      setSummary(sumRes.data);
      setByForm(formRes.data || []);
      setIndustries(indRes.data.results || indRes.data);
      setCategories(catRes.data || []);
      setLibrary(libRes.data.results || libRes.data);
    } catch (error) {
      console.error('Error fetching controls data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-nexus-400">Loading controls…</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Controls Library</h1>
        <p className="text-nexus-400 mt-1">
          Industry controls, master entities, and form coverage
        </p>
      </div>

      {/* Coverage KPIs */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader><CardTitle>Total Controls</CardTitle></CardHeader>
            <CardContent><p className="text-4xl font-bold">{summary.total}</p></CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Coverage</CardTitle></CardHeader>
            <CardContent>
              <p className="text-4xl font-bold text-emerald-400">
                {summary.coverage_percent}%
              </p>
              <Progress value={summary.coverage_percent} className="mt-2" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Present / Missing</CardTitle></CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">
                <span className="text-emerald-400">{summary.present}</span>
                <span className="text-nexus-500 text-2xl"> / </span>
                <span className="text-red-400">{summary.missing}</span>
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>High-Priority Missing</CardTitle></CardHeader>
            <CardContent>
              <p className="text-4xl font-bold text-red-400">
                {summary.high_priority_missing}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Industry Control Library */}
      <Card>
        <CardHeader><CardTitle>Industry Control Library</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-nexus-400 border-b border-nexus-800">
                  <th className="py-2 pr-4">Control ID</th>
                  <th className="py-2 pr-4">Control</th>
                  <th className="py-2 pr-4">Industry</th>
                  <th className="py-2 pr-4">Module</th>
                  <th className="py-2 pr-4">AI Agent</th>
                  <th className="py-2 pr-4">Compliance</th>
                </tr>
              </thead>
              <tbody>
                {library.map((c) => (
                  <tr key={c.id} className="border-b border-nexus-800/50">
                    <td className="py-2 pr-4 font-mono text-xs">{c.control_id}</td>
                    <td className="py-2 pr-4 font-medium">{c.control_name}</td>
                    <td className="py-2 pr-4 text-nexus-300">{c.industry}</td>
                    <td className="py-2 pr-4 text-nexus-300">{c.module}</td>
                    <td className="py-2 pr-4 text-nexus-300">{c.ai_agent}</td>
                    <td className="py-2 pr-4">
                      <span className="px-2 py-0.5 rounded bg-accent-primary/10 text-accent-primary text-xs">
                        {c.compliance}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form coverage */}
        <Card>
          <CardHeader><CardTitle>Form Coverage</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {byForm.map((f) => (
              <div key={f.form_name} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{f.form_name}</span>
                  <span className="text-nexus-400">
                    {f.present}/{f.total} ({f.coverage_percent}%)
                  </span>
                </div>
                <Progress value={f.coverage_percent} />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Industries by category */}
        <Card>
          <CardHeader>
            <CardTitle>Industries ({industries.length}) by Category</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {categories.map((cat) => (
              <div
                key={cat.category || 'uncategorized'}
                className="flex justify-between items-center py-1.5 border-b border-nexus-800/50"
              >
                <span className="text-nexus-200">{cat.category || 'Uncategorized'}</span>
                <span className="px-2 py-0.5 rounded-full bg-nexus-800 text-nexus-300 text-xs">
                  {cat.count}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
