import { useState, useEffect } from 'react'
import { Plus, FolderKanban, X, ChevronDown, ChevronUp, Clock, CheckCircle2, AlertCircle } from 'lucide-react'
import type { ProgettoOverview, TaskItem } from '../../types'
import { api } from '../../services/api'

const SEMAFORO_COLORS = {
  verde: 'bg-green-500',
  giallo: 'bg-yellow-400',
  rosso: 'bg-red-500',
}

const SEMAFORO_TEXT = {
  verde: 'In tempo',
  giallo: 'Attenzione',
  rosso: 'In ritardo',
}

const PRIORITA_COLORS = {
  alta: 'bg-red-100 text-red-700',
  media: 'bg-yellow-100 text-yellow-700',
  bassa: 'bg-green-100 text-green-700',
}

const STATO_TASK_COLORS = {
  da_fare: 'bg-gray-100 text-gray-600',
  in_corso: 'bg-blue-100 text-blue-700',
  completato: 'bg-green-100 text-green-700',
  bloccato: 'bg-red-100 text-red-700',
}

const STATO_TASK_LABELS: Record<string, string> = {
  da_fare: 'Da fare',
  in_corso: 'In corso',
  completato: 'Completato',
  bloccato: 'Bloccato',
}

export default function ProgettiPage() {
  const [overview, setOverview] = useState<ProgettoOverview[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)

  const load = () => {
    setLoading(true)
    api.getProgettiOverview()
      .then(data => setOverview(data.progetti))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Progetti</h1>
        <button onClick={() => setShowForm(true)} className="btn-accent flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuovo Progetto
        </button>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
            <FolderKanban className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Progetti Attivi</p>
            <p className="text-lg font-bold text-primary">{overview.length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
            <AlertCircle className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <p className="text-xs text-gray-500">In Ritardo</p>
            <p className="text-lg font-bold text-red-600">{overview.filter(p => p.semaforo === 'rosso').length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Task Completati</p>
            <p className="text-lg font-bold text-green-600">
              {overview.reduce((s, p) => s + p.task_completati, 0)}/{overview.reduce((s, p) => s + p.task_totali, 0)}
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Caricamento progetti...</div>
      ) : overview.length === 0 ? (
        <div className="card text-center py-12">
          <FolderKanban className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Nessun progetto attivo. Creane uno!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {overview.map(p => (
            <div key={p.id} className="card">
              <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(expanded === p.id ? null : p.id)}>
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${SEMAFORO_COLORS[p.semaforo]}`} title={SEMAFORO_TEXT[p.semaforo]} />
                  <div>
                    <h3 className="font-semibold text-gray-800">{p.nome}</h3>
                    <p className="text-sm text-gray-500">{p.cliente || 'Interno'} - {p.ore_registrate}h registrate</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {p.budget && <span className="text-sm text-gray-500">{formatCurrency(p.budget)}</span>}
                  <div className="w-24">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-600">{p.avanzamento}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-primary to-accent rounded-full" style={{ width: `${p.avanzamento}%` }} />
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">
                    {p.task_completati}/{p.task_totali} task
                  </span>
                  {expanded === p.id ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                </div>
              </div>

              {expanded === p.id && <TaskSection progettoId={p.id} />}
            </div>
          ))}
        </div>
      )}

      {showForm && <ProgettoFormModal onClose={() => setShowForm(false)} onCreated={() => { setShowForm(false); load() }} />}
    </div>
  )
}

function TaskSection({ progettoId }: { progettoId: number }) {
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newPriorita, setNewPriorita] = useState('media')

  useEffect(() => {
    api.getTasks(progettoId).then(setTasks).catch(() => {}).finally(() => setLoading(false))
  }, [progettoId])

  const handleAdd = async () => {
    if (!newTitle.trim()) return
    await api.createTask({ progetto_id: progettoId, titolo: newTitle, priorita: newPriorita })
    setNewTitle('')
    setShowAdd(false)
    api.getTasks(progettoId).then(setTasks)
  }

  const handleStatusChange = async (taskId: number, stato: string) => {
    await api.updateTask(taskId, { stato })
    api.getTasks(progettoId).then(setTasks)
  }

  return (
    <div className="mt-4 pt-4 border-t border-gray-100">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-sm text-gray-700">Task</h4>
        <button onClick={() => setShowAdd(true)} className="text-accent text-sm font-medium flex items-center gap-1 hover:underline">
          <Plus className="w-4 h-4" /> Aggiungi Task
        </button>
      </div>

      {loading ? (
        <p className="text-gray-400 text-sm">Caricamento...</p>
      ) : tasks.length === 0 ? (
        <p className="text-gray-400 text-sm">Nessun task.</p>
      ) : (
        <div className="space-y-2">
          {tasks.map(t => (
            <div key={t.id} className="flex items-center gap-3 py-2 px-3 bg-gray-50 rounded-lg">
              <select
                className="text-xs border rounded px-1 py-0.5"
                value={t.stato}
                onChange={e => handleStatusChange(t.id, e.target.value)}
              >
                {Object.entries(STATO_TASK_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
              <span className="flex-1 text-sm font-medium text-gray-800">{t.titolo}</span>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITA_COLORS[t.priorita]}`}>
                {t.priorita}
              </span>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATO_TASK_COLORS[t.stato]}`}>
                {STATO_TASK_LABELS[t.stato]}
              </span>
              {t.data_scadenza && (
                <span className="text-xs text-gray-500">
                  <Clock className="w-3 h-3 inline mr-0.5" />
                  {new Date(t.data_scadenza).toLocaleDateString('it-IT')}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {showAdd && (
        <div className="mt-3 flex gap-2">
          <input className="input text-sm flex-1" placeholder="Titolo task..." value={newTitle} onChange={e => setNewTitle(e.target.value)} />
          <select className="input text-sm w-24" value={newPriorita} onChange={e => setNewPriorita(e.target.value)}>
            <option value="alta">Alta</option>
            <option value="media">Media</option>
            <option value="bassa">Bassa</option>
          </select>
          <button onClick={handleAdd} className="btn-accent text-sm py-1.5">Aggiungi</button>
          <button onClick={() => setShowAdd(false)} className="text-sm text-gray-500">Annulla</button>
        </div>
      )}
    </div>
  )
}

function ProgettoFormModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ nome: '', cliente: '', budget: '', data_inizio: '', data_fine_prevista: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.createProgetto({
        nome: form.nome,
        cliente: form.cliente || undefined,
        budget: form.budget ? parseFloat(form.budget) : undefined,
        data_inizio: form.data_inizio || undefined,
        data_fine_prevista: form.data_fine_prevista || undefined,
      } as never)
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore')
    }
    setSaving(false)
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Nuovo Progetto</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">{error}</div>}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome progetto *</label>
            <input className="input" value={form.nome} onChange={e => setForm({ ...form, nome: e.target.value })} required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
              <input className="input" value={form.cliente} onChange={e => setForm({ ...form, cliente: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Budget (EUR)</label>
              <input className="input" type="number" step="100" value={form.budget} onChange={e => setForm({ ...form, budget: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Data inizio</label>
              <input className="input" type="date" value={form.data_inizio} onChange={e => setForm({ ...form, data_inizio: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Data fine prevista</label>
              <input className="input" type="date" value={form.data_fine_prevista} onChange={e => setForm({ ...form, data_fine_prevista: e.target.value })} />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Annulla</button>
            <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
              {saving ? 'Salvataggio...' : 'Crea Progetto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
