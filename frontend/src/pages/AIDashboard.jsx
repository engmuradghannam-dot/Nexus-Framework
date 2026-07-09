import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '@/lib/api';

export default function AIDashboard() {
  const [insights, setInsights] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [models, setModels] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [insRes, predRes, modRes] = await Promise.all([
        api.get('/ai/insights/'),
        api.get('/ai/predictions/'),
        api.get('/ai/models/')
      ]);
      setInsights(insRes.data.results || insRes.data);
      setPredictions(predRes.data.results || predRes.data);
      setModels(modRes.data.results || modRes.data);
    } catch (error) {
      console.error('Error fetching AI data:', error);
    }
  };

  const chartData = predictions.map(p => ({
    name: p.target_date || p.created_at?.substring(0, 10),
    value: p.predicted_value || 0,
    confidence: (p.confidence_score || 0) * 100
  }));

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">AI Module Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader><CardTitle>AI Models</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{models.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Insights Generated</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{insights.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Predictions</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{predictions.length}</p></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Prediction Trends</CardTitle></CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#8884d8" />
              <Line type="monotone" dataKey="confidence" stroke="#82ca9d" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Recent Insights</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {insights.slice(0, 5).map(insight => (
            <div key={insight.id} className="p-3 bg-gray-50 rounded-lg">
              <p className="font-medium">{insight.title}</p>
              <p className="text-sm text-gray-600">{insight.description}</p>
              <span className="text-xs text-blue-600">{insight.insight_type}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
