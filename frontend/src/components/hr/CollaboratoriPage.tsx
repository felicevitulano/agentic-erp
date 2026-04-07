import { useState, useEffect } from 'react'
import { Search, Plus, X, UserCog, Briefcase } from 'lucide-react'
import type { Collaboratore } from '../../types'
import { api } from '../../services/api'

export default function CollaboratoriPage() {
  const [collaboratori, setCollaboratori] = useState<Collaboratore[]>([])
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = (q?: string) => {
    setLoading(true)
    api.getCollaboratori(undefined, q || undefined)
      .then(setCollaboratori)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])
  useEffect(() => {
    const t = setTimeout(() => load(search || undefined), 300)
    return () => clearTimeout(t)
  }, [search])

  const tipoColor = (tipo: string) =>
    tipo === 'dipendente' ? 'bg-primary-50 text-primary' : 'bg-accent-50 text-accent'

  const statoColor = (stato: string) =>
    stato === 'attivo' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Collaboratori</h1>
        <button onClick={() => setShowForm(true)} className="btn-accent flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuovo Collaboratore
        </button>
      </div>

      {/* KPI */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
            <UserCog className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Totale Team</p>
            <p className="text-lg font-bold text-primary">{collaboratori.filter(c => c.stato === 'attivo').length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
            <Briefcase className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Dipendenti</p>
            <p className="text-lg font-bold text-blue-600">{collaboratori.filter(c => c.tipo === 'dipendente' && c.stato === 'attivo').length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-accent-50 flex items-center justify-center">
            <UserCog className="w-5 h-5 text-accent" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Consulenti</p>
            <p className="text-lg font-bold text-accent">{collaboratori.filter(c => c.tipo === 'consulente' && c.stato === 'attivo').length}</p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Cerca collaboratore..." className="input pl-10" />
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Nome</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Tipo</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Email</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Tariffa/g</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Competenze</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Scadenza</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Stato</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="px-6 py-12 text-center text-gray-400">Caricamento...</td></tr>
            ) : collaboratori.length === 0 ? (
              <tr><td colSpan={7} className="px-6 py-12 text-center text-gray-400">{search ? 'Nessun risultato' : 'Nessun collaboratore. Creane uno!'}</td></tr>
            ) : collaboratori.map(c => (
              <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-secondary-100 flex items-center justify-center text-secondary font-semibold text-sm">
                      {c.nome[0]}{c.cognome[0]}
                    </div>
                    <span className="font-medium text-gray-800">{c.nome} {c.cognome}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${tipoColor(c.tipo)}`}>{c.tipo}</span>
                </td>
                <td className="px-6 py-4 text-gray-600">{c.email || '-'}</td>
                <td className="px-6 py-4 text-gray-600">{c.tariffa_giornaliera ? `${c.tariffa_giornaliera} EUR` : '-'}</td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {(c.competenze || []).slice(0, 3).map((comp, i) => (
                      <span key={i} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">{comp}</span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-600 text-sm">
                  {c.data_fine_contratto ? new Date(c.data_fine_contratto).toLocaleDateString('it-IT') : '-'}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statoColor(c.stato)}`}>{c.stato}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && <CollaboratoreFormModal onClose={() => setShowForm(false)} onCreated={() => { setShowForm(false); load() }} />}
    </div>
  )
}

function CollaboratoreFormModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    nome: '', cognome: '', tipo: 'consulente', email: '', telefono: '',
    tariffa_giornaliera: '', competenze: '', data_inizio_contratto: '', data_fine_contratto: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.createCollaboratore({
        nome: form.nome,
        cognome: form.cognome,
        tipo: form.tipo as 'dipendente' | 'consulente',
        email: form.email || undefined,
        telefono: form.telefono || undefined,
        tariffa_giornaliera: form.tariffa_giornaliera ? parseFloat(form.tariffa_giornaliera) : undefined,
        competenze: form.competenze ? form.competenze.split(',').map(s => s.trim()) : undefined,
        data_inizio_contratto: form.data_inizio_contratto || undefined,
        data_fine_contratto: form.data_fine_contratto || undefined,
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
          <h2 className="text-lg font-semibold">Nuovo Collaboratore</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">{error}</div>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
              <input className="input" value={form.nome} onChange={e => setForm({ ...form, nome: e.target.value })} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cognome *</label>
              <input className="input" value={form.cognome} onChange={e => setForm({ ...form, cognome: e.target.value })} required />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo *</label>
              <select className="input" value={form.tipo} onChange={e => setForm({ ...form, tipo: e.target.value })}>
                <option value="consulente">Consulente</option>
                <option value="dipendente">Dipendente</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tariffa giornaliera</label>
              <input className="input" type="number" step="10" value={form.tariffa_giornaliera} onChange={e => setForm({ ...form, tariffa_giornaliera: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input className="input" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
              <input className="input" value={form.telefono} onChange={e => setForm({ ...form, telefono: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Competenze (separate da virgola)</label>
            <input className="input" value={form.competenze} onChange={e => setForm({ ...form, competenze: e.target.value })} placeholder="Python, React, FastAPI" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Inizio contratto</label>
              <input className="input" type="date" value={form.data_inizio_contratto} onChange={e => setForm({ ...form, data_inizio_contratto: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fine contratto</label>
              <input className="input" type="date" value={form.data_fine_contratto} onChange={e => setForm({ ...form, data_fine_contratto: e.target.value })} />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Annulla</button>
            <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
              {saving ? 'Salvataggio...' : 'Crea Collaboratore'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
