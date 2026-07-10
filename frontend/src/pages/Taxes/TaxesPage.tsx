import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { BarChart3, Calculator, Globe, Percent } from 'lucide-react';
import api from '@/lib/api';

export default function TaxesPage() {
  const [profiles, setProfiles] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [amount, setAmount] = useState('');
  const [isB2B, setIsB2B] = useState(false);
  const [calcResult, setCalcResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    try {
      const res = await api.get('/taxes/profiles/');
      setProfiles(res.data.results || res.data || []);
    } catch (error) {
      console.error('Error fetching tax profiles:', error);
    }
  };

  const calculateTax = async () => {
    if (!selectedCountry || !amount) return;
    setLoading(true);
    try {
      const res = await api.post('/taxes/calculations/calculate/', {
        country_code: selectedCountry,
        amount: parseFloat(amount),
        is_b2b: isB2B,
      });
      setCalcResult(res.data);
    } catch (error) {
      console.error('Error calculating tax:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectedProfile = profiles.find(p => p.country_code === selectedCountry);

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center gap-3">
        <BarChart3 className="w-8 h-8 text-[#0078d4]" />
        <h1 className="text-3xl font-bold">الضرائب</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tax Profiles */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Globe className="w-5 h-5" />
            ملفات الضريبة حسب الدولة
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profiles.map(profile => (
              <Card key={profile.id} className={selectedCountry === profile.country_code ? 'ring-2 ring-[#0078d4]' : ''}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center justify-between">
                    <span>{profile.country_name}</span>
                    <span className="text-sm text-gray-500">{profile.country_code}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">العملة:</span>
                    <span className="font-medium">{profile.currency_code}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">VAT:</span>
                    <span className="font-medium">{profile.vat_enabled ? '✅' : '❌'}</span>
                  </div>
                  {profile.vat_enabled && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">معدل VAT:</span>
                      <span className="font-medium">{profile.vat_standard_rate}%</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">ضريبة المبيعات:</span>
                    <span className="font-medium">{profile.sales_tax_enabled ? '✅' : '❌'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">الفاتورة الإلكترونية:</span>
                    <span className="font-medium">{profile.e_invoicing_mandatory ? '✅ إلزامية' : '❌ اختيارية'}</span>
                  </div>
                  <Button
                    variant={selectedCountry === profile.country_code ? 'default' : 'outline'}
                    className="w-full mt-2"
                    onClick={() => setSelectedCountry(profile.country_code)}
                  >
                    {selectedCountry === profile.country_code ? 'محدد' : 'اختيار'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Tax Calculator */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Calculator className="w-5 h-5" />
            حاسبة الضريبة
          </h2>
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="space-y-2">
                <Label>الدولة</Label>
                <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                  <SelectTrigger>
                    <SelectValue placeholder="اختر دولة" />
                  </SelectTrigger>
                  <SelectContent>
                    {profiles.map(p => (
                      <SelectItem key={p.id} value={p.country_code}>
                        {p.country_name} ({p.country_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>المبلغ الأساسي</Label>
                <Input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="b2b"
                  checked={isB2B}
                  onChange={(e) => setIsB2B(e.target.checked)}
                  className="w-4 h-4"
                />
                <Label htmlFor="b2b">معاملة B2B (تجارية)</Label>
              </div>

              <Button
                className="w-full"
                onClick={calculateTax}
                disabled={!selectedCountry || !amount || loading}
              >
                {loading ? 'جاري الحساب...' : 'احسب الضريبة'}
              </Button>

              {calcResult && (
                <div className="mt-4 p-4 bg-[#eff6fc] rounded-lg space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">المبلغ الأساسي:</span>
                    <span className="font-medium">{calcResult.base_amount} {selectedProfile?.currency_code}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">مبلغ الضريبة:</span>
                    <span className="font-medium text-[#d83b01]">{calcResult.tax_amount} {selectedProfile?.currency_code}</span>
                  </div>
                  <div className="flex justify-between text-sm font-bold border-t pt-2">
                    <span>المجموع:</span>
                    <span>{calcResult.total_amount} {selectedProfile?.currency_code}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    <Percent className="w-3 h-3 inline mr-1" />
                    {calcResult.applied_rates?.map(r => `${r.name}: ${r.rate}%`).join(', ') || 'Standard Rate'}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
