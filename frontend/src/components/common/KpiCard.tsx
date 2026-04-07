import { clsx } from 'clsx'
import type { ReactNode } from 'react'

interface KpiCardProps {
  title: string
  value: string | number
  icon: ReactNode
  color?: 'blue' | 'orange' | 'green' | 'red' | 'purple'
  subtitle?: string
}

const borderColors = {
  blue: 'border-l-primary',
  orange: 'border-l-accent',
  green: 'border-l-green-500',
  red: 'border-l-red-500',
  purple: 'border-l-secondary',
}

const iconBg = {
  blue: 'bg-primary-50 text-primary',
  orange: 'bg-accent-50 text-accent',
  green: 'bg-green-50 text-green-600',
  red: 'bg-red-50 text-red-600',
  purple: 'bg-secondary-50 text-secondary',
}

export default function KpiCard({ title, value, icon, color = 'blue', subtitle }: KpiCardProps) {
  return (
    <div className={clsx('card border-l-4', borderColors[color])}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={clsx('w-12 h-12 rounded-lg flex items-center justify-center', iconBg[color])}>
          {icon}
        </div>
      </div>
    </div>
  )
}
