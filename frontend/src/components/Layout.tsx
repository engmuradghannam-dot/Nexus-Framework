// components/Layout.tsx
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Layout/Sidebar';
import Header from './Header';

export default function Layout() {
  return (
    <div className="min-h-screen bg-[#faf9f8]" dir="rtl">
      <Sidebar />
      <div className="mr-[260px]">
        <Header />
        <main className="pt-12 min-h-screen">
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
