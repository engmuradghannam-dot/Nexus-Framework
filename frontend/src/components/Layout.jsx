import React from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'

export default function Layout() {
  return (
    <div className="min-h-screen bg-nexus-950">
      <Sidebar />
      <Header />
      <main className="ml-[260px] pt-16 min-h-screen">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
