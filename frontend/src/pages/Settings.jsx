import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { companies } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Save, Building2 } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

export default function Settings() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const { data: companyData, isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companies.list(),
  })
  const company = companyData?.results?.find((c) => c.id === user?.company) || companyData?.results?.[0]

  const [form, setForm] = useState(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (company && !form) setForm(company)
  }, [company])

  const updateMutation = useMutation({
    mutationFn: (data) => companies.update(company.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  if (isLoading || !form) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  const field = (key, label, type = 'text') => (
    <div>
      <label className="block text-sm text-gray-600 mb-1">{label}</label>
      <input
        type={type} value={form[key] || ''} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="w-full border rounded-lg px-3 py-2 text-sm"
      />
    </div>
  )

  return (
    <div dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">إعدادات الشركة</h2>
        <p className="text-gray-500 text-sm">بيانات ZATCA والمحاسبة الأساسية تُستخدم بكل الفواتير والمستندات المطبوعة</p>
      </div>

      {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-4 border border-red-200">{error}</div>}
      {saved && <div className="bg-green-50 text-green-700 text-sm px-3 py-2 rounded-lg mb-4 border border-green-200">تم الحفظ بنجاح</div>}

      <form
        onSubmit={(e) => { e.preventDefault(); updateMutation.mutate(form) }}
        className="bg-white rounded-xl shadow-sm border p-6 space-y-6 max-w-3xl"
      >
        <div>
          <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2"><Building2 size={16} /> البيانات الأساسية</h3>
          <div className="grid grid-cols-2 gap-4">
            {field('name', 'اسم الشركة')}
            {field('legal_name', 'الاسم القانوني الكامل')}
            {field('commercial_registration', 'رقم السجل التجاري')}
            {field('vat_number', 'الرقم الضريبي (VAT)')}
          </div>
        </div>

        <div>
          <h3 className="font-semibold text-gray-700 mb-3">الإعدادات المالية</h3>
          <div className="grid grid-cols-3 gap-4">
            {field('currency', 'العملة')}
            {field('fiscal_year_start', 'بداية السنة المالية', 'date')}
            {field('fiscal_year_end', 'نهاية السنة المالية', 'date')}
          </div>
        </div>

        <div>
          <h3 className="font-semibold text-gray-700 mb-3">بيانات التواصل</h3>
          <div className="grid grid-cols-2 gap-4">
            {field('phone', 'الهاتف')}
            {field('email', 'البريد الإلكتروني')}
            {field('website', 'الموقع الإلكتروني')}
            {field('city', 'المدينة')}
          </div>
        </div>

        <div>
          <h3 className="font-semibold text-gray-700 mb-3">البيانات البنكية</h3>
          <div className="grid grid-cols-3 gap-4">
            {field('bank_name', 'اسم البنك')}
            {field('bank_account', 'رقم الحساب')}
            {field('iban', 'IBAN')}
          </div>
        </div>

        <div className="flex justify-end pt-2 border-t">
          <button type="submit" disabled={updateMutation.isPending}
            className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
            <Save size={16} /> {updateMutation.isPending ? 'جارِ الحفظ...' : 'حفظ التغييرات'}
          </button>
        </div>
      </form>
    </div>
  )
}
