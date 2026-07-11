// components/Layout.tsx
import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Layout/Sidebar';
import Header from './Header';

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className="min-h-screen bg-[#faf9f8]" dir="rtl">
      <Header onMenuClick={() => setMenuOpen((v) => !v)} />
      <Sidebar isOpen={menuOpen} onClose={() => setMenuOpen(false)} />
      <main className="pt-12 min-h-screen">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
