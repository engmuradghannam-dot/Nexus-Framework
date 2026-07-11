// utils/exportCsv.js
// Export an array of plain objects to a downloadable CSV file (Excel-friendly).
export function exportToCsv(rows, filename = 'export.csv') {
  if (!rows || rows.length === 0) {
    alert('لا توجد بيانات للتصدير');
    return;
  }
  const headers = Object.keys(rows[0]);
  const escape = (v) => {
    if (v === null || v === undefined) return '';
    const s = typeof v === 'object' ? JSON.stringify(v) : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const csv = [
    headers.join(','),
    ...rows.map((r) => headers.map((h) => escape(r[h])).join(',')),
  ].join('\n');
  // Prepend BOM so Arabic renders correctly in Excel
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default exportToCsv;
