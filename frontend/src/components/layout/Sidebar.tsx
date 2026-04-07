import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  TrendingUp,
  FileText,
  Receipt,
  Calendar,
  BarChart3,
  UserCog,
  FolderKanban,
  Megaphone,
  ScrollText,
  LogOut,
} from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/sales', icon: TrendingUp, label: 'Pipeline' },
  { to: '/contacts', icon: Users, label: 'Contatti' },
  { to: '/contracts', icon: FileText, label: 'Contratti' },
  { to: '/finance', icon: Receipt, label: 'Fatture' },
  { to: '/scadenzario', icon: Calendar, label: 'Scadenzario' },
  { to: '/cash-flow', icon: BarChart3, label: 'Cash Flow' },
  { to: '/hr', icon: UserCog, label: 'Risorse Umane' },
  { to: '/operations', icon: FolderKanban, label: 'Operations' },
  { to: '/marketing', icon: Megaphone, label: 'Marketing' },
  { to: '/audit', icon: ScrollText, label: 'Audit Log' },
]

interface SidebarProps {
  onLogout: () => void
}

export default function Sidebar({ onLogout }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-primary flex flex-col z-30">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-primary-400/30">
        <h1 className="text-white font-bold text-xl tracking-tight">
          <span className="text-accent">Agentic</span> ERP
        </h1>
        <p className="text-primary-200 text-xs mt-0.5">Think Next S.r.l.</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-white/15 text-white'
                  : 'text-primary-200 hover:bg-white/10 hover:text-white'
              )
            }
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-primary-400/30">
        <button
          onClick={onLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                     text-primary-200 hover:bg-white/10 hover:text-white transition-colors w-full"
        >
          <LogOut className="w-5 h-5" />
          Esci
        </button>
      </div>
    </aside>
  )
}
