// pages/Security/SecurityPage.tsx
import { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import { ShieldCheck, ShieldOff, RefreshCw, CheckCircle2 } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentFormField, FluentInput } from '../../components/FluentUI';
import { twofaApi } from '../../services/api';

export default function SecurityPage() {
  const [enabled, setEnabled] = useState(false);
  const [setupData, setSetupData] = useState<any>(null);
  const [qr, setQr] = useState('');
  const [code, setCode] = useState('');
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  const loadStatus = () => twofaApi.status().then((s) => setEnabled(s.enabled)).catch(() => {});
  useEffect(() => { loadStatus(); }, []);

  const startSetup = async () => {
    setErr(''); setMsg('');
    const s = await twofaApi.setup();
    setSetupData(s);
    try { setQr(await QRCode.toDataURL(s.otpauth_uri, { width: 200, margin: 1 })); } catch { setQr(''); }
  };

  const confirm = async () => {
    setErr(''); setMsg('');
    try {
      const res = await twofaApi.verify(code);
      setMsg(res.message); setEnabled(true); setSetupData(null); setCode('');
    } catch (e: any) {
      setErr(e?.response?.data?.message || 'رمز غير صحيح');
    }
  };

  const disable = async () => {
    await twofaApi.disable(); setEnabled(false); setSetupData(null); setMsg('تم إيقاف المصادقة الثنائية');
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الأمان" subtitle="Security — المصادقة الثنائية (2FA)"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: loadStatus }]} />
      <div className="p-6 max-w-2xl space-y-6">
        {msg && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle2 size={16} /> {msg}</div>}

        <FluentCard>
          <div className="flex items-center gap-3 mb-4">
            {enabled ? <ShieldCheck size={28} className="text-[#107c10]" /> : <ShieldOff size={28} className="text-[#605e5c]" />}
            <div>
              <h3 className="text-base font-semibold text-[#323130]">المصادقة الثنائية (TOTP)</h3>
              <p className="text-sm text-[#605e5c]">
                {enabled ? 'مفعّلة — حسابك محمي برمز إضافي من تطبيق المصادقة.' : 'غير مفعّلة — أضف طبقة حماية إضافية عند تسجيل الدخول.'}
              </p>
            </div>
            <span className={`mr-auto text-xs px-2 py-1 rounded-full ${enabled ? 'bg-[#dff6dd] text-[#107c10]' : 'bg-[#f3f2f1] text-[#605e5c]'}`}>
              {enabled ? 'مفعّلة' : 'متوقفة'}
            </span>
          </div>

          {!enabled && !setupData && (
            <button onClick={startSetup} className="rounded-md bg-[#0078d4] px-4 py-2 text-sm font-medium text-white hover:bg-[#106ebe]">
              بدء التفعيل
            </button>
          )}

          {!enabled && setupData && (
            <div className="space-y-4 border-t border-[#e1dfdd] pt-4">
              <p className="text-sm text-[#323130]">1. امسح رمز QR بتطبيق مثل Google Authenticator أو Microsoft Authenticator:</p>
              {qr && <img src={qr} alt="QR" className="border border-[#e1dfdd] rounded-md" />}
              <p className="text-xs text-[#605e5c]">أو أدخل المفتاح يدوياً:</p>
              <code className="block bg-[#f3f2f1] rounded px-3 py-2 text-sm font-mono tracking-wider break-all">{setupData.secret}</code>
              <p className="text-sm text-[#323130]">2. أدخل الرمز المكوّن من 6 أرقام من التطبيق:</p>
              <div className="flex items-end gap-2">
                <FluentFormField label="رمز التحقق">
                  <FluentInput value={code} onChange={(e) => setCode(e.target.value)} placeholder="123456" maxLength={6} />
                </FluentFormField>
                <button onClick={confirm} className="rounded-md bg-[#107c10] px-4 py-2 text-sm font-medium text-white hover:bg-[#0e6b0e] h-9">تأكيد وتفعيل</button>
              </div>
              {err && <p className="text-sm text-[#a4262c]">{err}</p>}
            </div>
          )}

          {enabled && (
            <button onClick={disable} className="rounded-md border border-[#a4262c] text-[#a4262c] px-4 py-2 text-sm font-medium hover:bg-[#fdf2f2]">
              إيقاف المصادقة الثنائية
            </button>
          )}
        </FluentCard>
      </div>
    </div>
  );
}
