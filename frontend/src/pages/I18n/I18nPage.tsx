import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Zap, Globe, Upload, Download, Search, Languages, CheckCircle } from 'lucide-react';
import api from '@/lib/api';

export default function I18nPage() {
  const [languages, setLanguages] = useState([]);
  const [translations, setTranslations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLang, setSelectedLang] = useState('');
  const [bulkData, setBulkData] = useState('');
  const [uploadResult, setUploadResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchLanguages();
    fetchTranslations();
  }, []);

  const fetchLanguages = async () => {
    try {
      const res = await api.get('/i18n/languages/');
      setLanguages(res.data.results || res.data || []);
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const fetchTranslations = async (lang = '') => {
    try {
      const params = lang ? { language: lang } : {};
      const res = await api.get('/i18n/translations/', { params });
      setTranslations(res.data.results || res.data || []);
    } catch (error) {
      console.error('Error fetching translations:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery) {
      fetchTranslations(selectedLang);
      return;
    }
    try {
      const res = await api.get(`/i18n/translations/search/?q=${searchQuery}`);
      setTranslations(res.data.results || res.data || []);
    } catch (error) {
      console.error('Error searching translations:', error);
    }
  };

  const handleBulkUpload = async () => {
    if (!selectedLang || !bulkData.trim()) return;
    setLoading(true);
    try {
      // Parse CSV-like format: key,value,context
      const lines = bulkData.trim().split('\n');
      const translations = lines.map(line => {
        const parts = line.split(',');
        return {
          key: parts[0]?.trim(),
          value: parts[1]?.trim(),
          context: parts[2]?.trim() || 'general',
        };
      }).filter(t => t.key && t.value);

      const res = await api.post('/i18n/translations/bulk/', {
        language_code: selectedLang,
        translations,
      });
      setUploadResult(res.data);
      fetchTranslations(selectedLang);
    } catch (error) {
      console.error('Error uploading translations:', error);
      setUploadResult({ error: 'Failed to upload translations' });
    } finally {
      setLoading(false);
    }
  };

  const exportTranslations = () => {
    const csv = translations.map(t => `${t.key},${t.value},${t.context}`).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translations_${selectedLang || 'all'}.csv`;
    a.click();
  };

  const filteredTranslations = translations.filter(t =>
    !searchQuery ||
    t.key?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.value?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center gap-3">
        <Zap className="w-8 h-8 text-[#0078d4]" />
        <h1 className="text-3xl font-bold">التوطين (i18n)</h1>
      </div>

      <Tabs defaultValue="languages" className="w-full">
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="languages">اللغات</TabsTrigger>
          <TabsTrigger value="translations">الترجمات</TabsTrigger>
          <TabsTrigger value="bulk">رفع جماعي</TabsTrigger>
        </TabsList>

        {/* Languages Tab */}
        <TabsContent value="languages" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {languages.map(lang => (
              <Card key={lang.id} className={lang.is_default ? 'ring-2 ring-[#0078d4]' : ''}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <span className="text-2xl">{lang.flag_emoji}</span>
                    <span>{lang.name_local}</span>
                    {lang.is_default && (
                      <span className="text-xs bg-[#0078d4] text-white px-2 py-0.5 rounded">افتراضي</span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">الكود:</span>
                    <span className="font-medium">{lang.code}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">الاتجاه:</span>
                    <span className="font-medium">{lang.direction === 'rtl' ? 'RTL (من اليمين)' : 'LTR (من اليسار)'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">الحالة:</span>
                    <span className="font-medium">{lang.is_active ? '✅ نشط' : '❌ معطل'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">التاريخ:</span>
                    <span className="font-medium">{lang.date_format}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">الفاصل العشري:</span>
                    <span className="font-medium">{lang.decimal_separator}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Translations Tab */}
        <TabsContent value="translations" className="space-y-4">
          <div className="flex gap-4 items-end">
            <div className="flex-1 space-y-2">
              <Label>بحث</Label>
              <div className="flex gap-2">
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="ابحث بـ key أو value..."
                  className="flex-1"
                />
                <Button onClick={handleSearch} variant="outline">
                  <Search className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              <Label>اللغة</Label>
              <select
                value={selectedLang}
                onChange={(e) => {
                  setSelectedLang(e.target.value);
                  fetchTranslations(e.target.value);
                }}
                className="border rounded px-3 py-2"
              >
                <option value="">جميع اللغات</option>
                {languages.map(l => (
                  <option key={l.id} value={l.code}>{l.name_local}</option>
                ))}
              </select>
            </div>
            <Button onClick={exportTranslations} variant="outline">
              <Download className="w-4 h-4 mr-2" />
              تصدير CSV
            </Button>
          </div>

          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">اللغة</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">المفتاح (Key)</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">الترجمة</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">السياق</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">الحالة</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredTranslations.map(t => (
                  <tr key={t.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">{t.language_code}</td>
                    <td className="px-4 py-3 font-mono text-xs">{t.key}</td>
                    <td className="px-4 py-3">{t.value}</td>
                    <td className="px-4 py-3">
                      <span className="bg-gray-100 px-2 py-1 rounded text-xs">{t.context}</span>
                    </td>
                    <td className="px-4 py-3">
                      {t.is_reviewed ? (
                        <span className="flex items-center gap-1 text-green-600 text-xs">
                          <CheckCircle className="w-3 h-3" /> تم المراجعة
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">قيد المراجعة</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredTranslations.length === 0 && (
              <div className="p-8 text-center text-gray-500">
                <Languages className="w-8 h-8 mx-auto mb-2 opacity-50" />
                لا توجد ترجمات
              </div>
            )}
          </div>
        </TabsContent>

        {/* Bulk Upload Tab */}
        <TabsContent value="bulk" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                رفع ترجمات جماعية
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>اللغة المستهدفة</Label>
                <select
                  value={selectedLang}
                  onChange={(e) => setSelectedLang(e.target.value)}
                  className="border rounded px-3 py-2 w-full"
                >
                  <option value="">اختر لغة...</option>
                  {languages.map(l => (
                    <option key={l.id} value={l.code}>{l.name_local} ({l.code})</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label>بيانات الترجمات (CSV format: key,value,context)</Label>
                <textarea
                  value={bulkData}
                  onChange={(e) => setBulkData(e.target.value)}
                  placeholder={`dashboard,لوحة المعلومات,navigation\nusers,المستخدمين,navigation\nsettings,الإعدادات,navigation`}
                  className="border rounded px-3 py-2 w-full h-64 font-mono text-sm"
                />
              </div>

              <Button
                onClick={handleBulkUpload}
                disabled={!selectedLang || !bulkData.trim() || loading}
                className="w-full"
              >
                {loading ? 'جاري الرفع...' : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    رفع الترجمات
                  </>
                )}
              </Button>

              {uploadResult && (
                <div className="p-4 bg-[#eff6fc] rounded-lg space-y-2">
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="w-5 h-5" />
                    <span className="font-medium">تم الرفع بنجاح!</span>
                  </div>
                  <div className="text-sm space-y-1">
                    <p>تم الإنشاء: {uploadResult.created || 0}</p>
                    <p>تم التحديث: {uploadResult.updated || 0}</p>
                    {uploadResult.failed > 0 && (
                      <p className="text-red-600">فشل: {uploadResult.failed}</p>
                    )}
                  </div>
                </div>
              )}

              <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-600">
                <p className="font-medium mb-2">تنسيق الملف:</p>
                <code className="block bg-white p-2 rounded border font-mono text-xs">
                  key,value,context<br/>
                  dashboard,لوحة المعلومات,navigation<br/>
                  users,المستخدمين,navigation<br/>
                  save,حفظ,actions
                </code>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
