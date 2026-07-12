// utils/printInvoice.ts — build a ZATCA-style printable invoice and open the print dialog.
import QRCode from 'qrcode';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export async function printInvoice(payload: any) {
  const inv = payload.invoice || {};
  let qrImg = '';
  try { qrImg = await QRCode.toDataURL(payload.qr || '', { width: 130, margin: 1 }); } catch { qrImg = ''; }
  const isSales = inv.invoice_type === 'sales';
  const html = `<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8">
  <title>${inv.invoice_number || ''}</title>
  <style>
    *{font-family:'Segoe UI',Tahoma,Arial,sans-serif;box-sizing:border-box}
    body{margin:0;padding:32px;color:#201f1e}
    .head{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:3px solid #0078d4;padding-bottom:16px}
    .title{font-size:26px;font-weight:800;color:#0078d4;margin:0}
    .sub{font-size:13px;color:#605e5c;margin:2px 0}
    .badge{display:inline-block;background:#eff6fc;color:#0078d4;padding:3px 10px;border-radius:12px;font-size:12px}
    table{width:100%;border-collapse:collapse;margin-top:20px}
    th,td{border:1px solid #e1dfdd;padding:10px;text-align:right;font-size:13px}
    th{background:#f3f2f1}
    .totals{margin-top:16px;width:280px;margin-inline-start:auto}
    .totals td{border:none;padding:4px 8px}
    .grand{font-weight:800;font-size:16px;border-top:2px solid #201f1e!important}
    .foot{display:flex;justify-content:space-between;align-items:flex-end;margin-top:32px}
    .qr{text-align:center}.qr img{border:1px solid #e1dfdd;border-radius:6px}
    .note{font-size:11px;color:#a19f9d}
    @media print{body{padding:0}.noprint{display:none}}
  </style></head><body>
  <div class="head">
    <div>
      <h1 class="title">${payload.seller_name || 'Nexus'}</h1>
      <p class="sub">الرقم الضريبي: ${payload.vat_number || ''}</p>
      <p class="sub">فاتورة ضريبية ${isSales ? 'مبسطة' : 'شراء'}</p>
    </div>
    <div style="text-align:left">
      <p class="sub"><b>رقم الفاتورة:</b> ${inv.invoice_number || ''}</p>
      <p class="sub"><b>التاريخ:</b> ${inv.invoice_date || ''}</p>
      <p class="sub"><b>الاستحقاق:</b> ${inv.due_date || '-'}</p>
      <span class="badge">${inv.zatca_category || 'S'} — ${isSales ? 'بيع' : 'شراء'}</span>
    </div>
  </div>
  <p class="sub" style="margin-top:14px"><b>${isSales ? 'العميل' : 'المورّد'}:</b> ${inv.party_name || ''}</p>
  <table>
    <thead><tr><th>الوصف</th><th>المبلغ الأساسي</th><th>الضريبة (${inv.tax_rate || 15}%)</th><th>الإجمالي</th></tr></thead>
    <tbody><tr><td>${inv.notes || 'قيمة الفاتورة'}</td><td>${fmt(inv.subtotal)}</td><td>${fmt(inv.tax_amount)}</td><td>${fmt(inv.total)}</td></tr></tbody>
  </table>
  <table class="totals">
    <tr><td>المجموع الفرعي</td><td style="text-align:left">${fmt(inv.subtotal)}</td></tr>
    <tr><td>ضريبة القيمة المضافة</td><td style="text-align:left">${fmt(inv.tax_amount)}</td></tr>
    <tr class="grand"><td>الإجمالي شامل الضريبة</td><td style="text-align:left">${fmt(inv.total)} ر.س</td></tr>
    <tr><td>المدفوع</td><td style="text-align:left">${fmt(inv.paid_amount)}</td></tr>
  </table>
  <div class="foot">
    <div class="qr">${qrImg ? `<img src="${qrImg}" alt="ZATCA QR"/><p class="note">رمز ZATCA</p>` : ''}</div>
    <div class="note">فاتورة مُنشأة عبر Nexus ERP — متوافقة مع متطلبات هيئة الزكاة والضريبة والجمارك (المرحلة الأولى)</div>
  </div>
  <div class="noprint" style="text-align:center;margin-top:24px">
    <button onclick="window.print()" style="background:#0078d4;color:#fff;border:none;padding:10px 24px;border-radius:4px;font-size:14px;cursor:pointer">طباعة / حفظ PDF</button>
  </div>
  <script>window.onload=function(){setTimeout(function(){window.print()},400)}</script>
  </body></html>`;
  const w = window.open('', '_blank', 'width=820,height=900');
  if (w) { w.document.write(html); w.document.close(); }
}
