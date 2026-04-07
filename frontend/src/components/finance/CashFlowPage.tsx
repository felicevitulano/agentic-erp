import { useState, useEffect } from 'react'
import { TrendingUp, ArrowUpRight, ArrowDownLeft } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts'
import type { CashFlowItem } from '../../types'
import { api } from '../../services/api'

export default function CashFlowPage() {
  const [cashFlow, setCashFlow] = useState<CashFlowItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getCashFlow(6)
      .then(data => setCashFlow(data.cash_flow))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v)

  const totEntrate = cashFlow.reduce((s, c) => s + c.entrate, 0)
  const totUscite = cashFlow.reduce((s, c) => s + c.uscite, 0)
  const saldoTotale = totEntrate - totUscite

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Cash Flow Previsionale</h1>

      {/* KPI */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
            <ArrowUpRight className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Entrate previste</p>
            <p className="text-lg font-bold text-green-600">{formatCurrency(totEntrate)}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
            <ArrowDownLeft className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Uscite previste</p>
            <p className="text-lg font-bold text-red-600">{formatCurrency(totUscite)}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Saldo netto</p>
            <p className={`text-lg font-bold ${saldoTotale >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(saldoTotale)}
            </p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="card">
        <h2 className="font-semibold text-gray-700 mb-4">Andamento Cash Flow</h2>
        {loading ? (
          <div className="h-80 flex items-center justify-center text-gray-400">Caricamento...</div>
        ) : cashFlow.length === 0 ? (
          <div className="h-80 flex items-center justify-center text-gray-400 text-sm">
            Il grafico apparira' quando ci saranno fatture registrate
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={cashFlow} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#6B7280' }} />
              <YAxis tick={{ fontSize: 12, fill: '#6B7280' }} tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip
                formatter={(value: number, name: string) => [formatCurrency(value), name === 'entrate' ? 'Entrate' : name === 'uscite' ? 'Uscite' : 'Saldo']}
                contentStyle={{ borderRadius: '12px', border: '1px solid #E5E7EB' }}
              />
              <Legend formatter={(value: string) => value === 'entrate' ? 'Entrate' : value === 'uscite' ? 'Uscite' : 'Saldo'} />
              <ReferenceLine y={0} stroke="#9CA3AF" strokeDasharray="3 3" />
              <Bar dataKey="entrate" fill="#22C55E" radius={[4, 4, 0, 0]} />
              <Bar dataKey="uscite" fill="#EF4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Monthly breakdown table */}
      {cashFlow.length > 0 && (
        <div className="card mt-6 p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Mese</th>
                <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Entrate</th>
                <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Uscite</th>
                <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Saldo</th>
              </tr>
            </thead>
            <tbody>
              {cashFlow.map(cf => (
                <tr key={cf.mese} className={`border-b border-gray-100 ${cf.is_past ? 'opacity-60' : ''}`}>
                  <td className="px-6 py-3 font-medium text-gray-800">
                    {cf.label} {cf.is_past && <span className="text-xs text-gray-400">(passato)</span>}
                  </td>
                  <td className="px-6 py-3 text-right text-green-600 font-medium">{formatCurrency(cf.entrate)}</td>
                  <td className="px-6 py-3 text-right text-red-600 font-medium">{formatCurrency(cf.uscite)}</td>
                  <td className={`px-6 py-3 text-right font-bold ${cf.saldo >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    {formatCurrency(cf.saldo)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
