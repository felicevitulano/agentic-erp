import { useState, useEffect } from 'react'
import { Shield, Filter } from 'lucide-react'
import type { AuditLogEntry } from '../../types'
import { api } from '../../services/api'

const AGENT_COLORS: Record<string, string> = {
  sales: 'bg-blue-100 text-blue-700',
  finance: 'bg-green-100 text-green-700',
  hr: 'bg-purple-100 text-purple-700',
  operations: 'bg-orange-100 text-orange-700',
  marketing: 'bg-pink-100 text-pink-700',
  system: 'bg-gray-100 text-gray-600',
}

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [filterAgent, setFilterAgent] = useState('')
  const [filterAction, setFilterAction] = useState('')
  const [limit, setLimit] = useState(100)

  const load = () => {
    setLoading(true)
    api.getAuditLog(filterAgent || undefined, filterAction || undefined, limit)
      .then(setLogs)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filterAgent, filterAction, limit])

  const formatTimestamp = (ts: string) => {
    const d = new Date(ts)
    return d.toLocaleString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  const uniqueAgents = [...new Set(logs.map(l => l.agent))].sort()
  const uniqueActions = [...new Set(logs.map(l => l.action))].sort()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary" /> Audit Log
          </h1>
          <p className="text-sm text-gray-500">Registro completo delle azioni degli agenti AI</p>
        </div>
        <div className="text-sm text-gray-400">
          {logs.length} {logs.length === 1 ? 'voce' : 'voci'}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <Filter className="w-4 h-4 text-gray-400" />
        <select value={filterAgent} onChange={e => setFilterAgent(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-white">
          <option value="">Tutti gli agenti</option>
          {uniqueAgents.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <select value={filterAction} onChange={e => setFilterAction(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-white">
          <option value="">Tutte le azioni</option>
          {uniqueActions.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <select value={limit} onChange={e => setLimit(Number(e.target.value))} className="border rounded-lg px-3 py-2 text-sm bg-white">
          <option value={50}>Ultime 50</option>
          <option value={100}>Ultime 100</option>
          <option value={200}>Ultime 200</option>
          <option value={500}>Ultime 500</option>
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Caricamento...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 text-gray-400">Nessuna voce nel log</div>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-3">Timestamp</th>
                  <th className="text-left px-4 py-3">Agente</th>
                  <th className="text-left px-4 py-3">Azione</th>
                  <th className="text-left px-4 py-3">Entita</th>
                  <th className="text-left px-4 py-3">Dettagli</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {logs.map(log => {
                  const agentColor = AGENT_COLORS[log.agent] || AGENT_COLORS.system
                  return (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap text-xs font-mono">
                        {formatTimestamp(log.timestamp)}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${agentColor}`}>
                          {log.agent}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium">{log.action}</td>
                      <td className="px-4 py-3 text-gray-500">
                        {log.entity_type ? `${log.entity_type}${log.entity_id ? ` #${log.entity_id}` : ''}` : '—'}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs max-w-xs truncate">
                        {log.details ? JSON.stringify(log.details) : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
