import { useState, useEffect } from 'react'
import { TrendingUp, Receipt, FolderKanban, AlertTriangle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import type { DashboardData, PipelineStats, PipelineState } from '../../types'
import { PIPELINE_LABELS, PIPELINE_COLORS } from '../../types'
import { api } from '../../services/api'
import KpiCard from '../common/KpiCard'

const ACTIVE_STATES: PipelineState[] = ['lead', 'qualificato', 'proposta', 'negoziazione']

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [pipelineStats, setPipelineStats] = useState<PipelineStats | null>(null)

  useEffect(() => {
    api.getDashboard().then(setData).catch(() => {})
    api.getPipelineStats().then(setPipelineStats).catch(() => {})
  }, [])

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)

  const barData = pipelineStats
    ? ACTIVE_STATES.map((state) => ({
        name: PIPELINE_LABELS[state],
        valore: pipelineStats.per_stato[state]?.value ?? 0,
        count: pipelineStats.per_stato[state]?.count ?? 0,
        fill: PIPELINE_COLORS[state],
      }))
    : []

  const hasBarData = barData.some((d) => d.count > 0)

  const winRate = pipelineStats?.win_rate ?? 0
  const pieData = pipelineStats && (pipelineStats.vinte > 0 || pipelineStats.perse > 0)
    ? [
        { name: 'Vinte', value: pipelineStats.vinte, color: PIPELINE_COLORS.vinto },
        { name: 'Perse', value: pipelineStats.perse, color: PIPELINE_COLORS.perso },
      ]
    : []

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard
          title="Pipeline Value"
          value={formatCurrency(data?.pipeline_value ?? 0)}
          icon={<TrendingUp className="w-6 h-6" />}
          color="blue"
        />
        <KpiCard
          title="Fatturato Mese"
          value={formatCurrency(data?.fatturato_mese ?? 0)}
          icon={<Receipt className="w-6 h-6" />}
          color="green"
        />
        <KpiCard
          title="Progetti Attivi"
          value={data?.progetti_attivi ?? 0}
          icon={<FolderKanban className="w-6 h-6" />}
          color="purple"
        />
        <KpiCard
          title="Task Scaduti"
          value={data?.task_scaduti ?? 0}
          icon={<AlertTriangle className="w-6 h-6" />}
          color={data?.task_scaduti ? 'red' : 'orange'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        {/* Pipeline per Stato - Bar Chart */}
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-4">Pipeline per Stato</h2>
          {!hasBarData ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
              I grafici verranno popolati quando ci saranno dati nella pipeline
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={264}>
              <BarChart data={barData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#6B7280' }} />
                <YAxis tick={{ fontSize: 12, fill: '#6B7280' }} tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), 'Valore']}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #E5E7EB' }}
                />
                <Bar dataKey="valore" radius={[6, 6, 0, 0]}>
                  {barData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Win Rate - Pie Chart */}
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-4">Tasso di Conversione</h2>
          {pieData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
              Le statistiche appariranno dopo la chiusura di opportunita
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="100%" height={264}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    dataKey="value"
                    paddingAngle={4}
                    label={({ name, value }: { name: string; value: number }) => `${name}: ${value}`}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #E5E7EB' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="text-center pr-4 flex-shrink-0">
                <p className="text-4xl font-bold text-primary">{winRate.toFixed(0)}%</p>
                <p className="text-sm text-gray-500 mt-1">Win Rate</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
