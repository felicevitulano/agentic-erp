import { useState, useEffect } from 'react'
import { Bell, MessageCircle } from 'lucide-react'
import type { User, Notification } from '../../types'
import { api } from '../../services/api'

interface HeaderProps {
  user: User
  onToggleChat: () => void
}

export default function Header({ user, onToggleChat }: HeaderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [showNotifs, setShowNotifs] = useState(false)

  useEffect(() => {
    api.getNotifications().then(setNotifications).catch(() => {})
  }, [])

  const unreadCount = notifications.filter((n) => !n.read).length

  const markRead = async (id: number) => {
    await api.markNotificationRead(id)
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
  }

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 sticky top-0 z-20">
      <div />

      <div className="flex items-center gap-4">
        {/* Chat toggle */}
        <button
          onClick={onToggleChat}
          className="relative p-2 text-gray-500 hover:text-primary rounded-lg hover:bg-gray-100 transition-colors"
          title="Assistente AI"
        >
          <MessageCircle className="w-5 h-5" />
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifs(!showNotifs)}
            className="relative p-2 text-gray-500 hover:text-primary rounded-lg hover:bg-gray-100 transition-colors"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 bg-accent text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-medium">
                {unreadCount}
              </span>
            )}
          </button>

          {showNotifs && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-200 max-h-96 overflow-y-auto">
              <div className="px-4 py-3 border-b border-gray-100">
                <h3 className="font-semibold text-sm">Notifiche</h3>
              </div>
              {notifications.length === 0 ? (
                <p className="px-4 py-6 text-gray-400 text-sm text-center">Nessuna notifica</p>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    onClick={() => markRead(n.id)}
                    className={`px-4 py-3 border-b border-gray-50 cursor-pointer hover:bg-gray-50 ${
                      !n.read ? 'bg-accent-50' : ''
                    }`}
                  >
                    <p className="text-sm font-medium">{n.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{n.message}</p>
                    <p className="text-xs text-gray-400 mt-1">{n.agent}</p>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* User */}
        <div className="flex items-center gap-2 pl-2 border-l border-gray-200">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-sm font-medium">
            {user.full_name.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm font-medium text-gray-700">{user.full_name}</span>
        </div>
      </div>
    </header>
  )
}
