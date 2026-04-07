import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import type { User } from '../../types'
import Sidebar from './Sidebar'
import Header from './Header'
import ChatPanel from './ChatPanel'

interface LayoutProps {
  user: User
  onLogout: () => void
}

export default function Layout({ user, onLogout }: LayoutProps) {
  const [chatOpen, setChatOpen] = useState(false)

  return (
    <div className="min-h-screen">
      <Sidebar onLogout={onLogout} />
      <div className="ml-64">
        <Header user={user} onToggleChat={() => setChatOpen(!chatOpen)} />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
      <ChatPanel isOpen={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  )
}
