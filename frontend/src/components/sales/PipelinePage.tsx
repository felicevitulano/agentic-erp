import { useState, useEffect } from 'react'
import { Plus, ChevronRight, Euro, X } from 'lucide-react'
import type { Opportunity, Contact, PipelineState } from '../../types'
import { PIPELINE_LABELS, PIPELINE_COLORS } from '../../types'
import { api } from '../../services/api'

const ACTIVE_STATES: PipelineState[] = ['lead', 'qualificato', 'proposta', 'negoziazione']
const CLOSED_STATES: PipelineState[] = ['vinto', 'perso']

const VALID_TRANSITIONS: Record<string, string[]> = {
  lead: ['qualificato', 'perso'],
  qualificato: ['proposta', 'perso'],
  proposta: ['negoziazione', 'perso'],
  negoziazione: ['vinto', 'perso'],
}

export default function PipelinePage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [movingOpp, setMovingOpp] = useState<{ opp: Opportunity; targets: string[] } | null>(null)

  const load = async () => {
    setLoading(true)
    try {
      const [opps, cts] = await Promise.all([api.getOpportunities(), api.getContacts()])
      setOpportunities(opps)
      setContacts(cts)
    } catch { /* ignore */ }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v)

  const oppsByState = (state: string) => opportunities.filter((o) => o.stato === state)

  const stateTotal = (state: string) =>
    oppsByState(state).reduce((sum, o) => sum + o.valore_stimato, 0)

  const moveOpportunity = async (opp: Opportunity, newState: string) => {
    try {
      const data: Partial<Opportunity> = { stato: newState }
      if (newState === 'perso') {
        const motivo = prompt('Motivo della perdita: competitor, prezzo, timing, budget, altro')
        if (!motivo) return
        data.motivo_perdita = motivo
      }
      await api.updateOpportunity(opp.id, data)
      setMovingOpp(null)
      load()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Errore')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Pipeline Vendite</h1>
        <button onClick={() => setShowForm(true)} className="btn-accent flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuova Opportunita
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Caricamento pipeline...</div>
      ) : (
        <>
          {/* Kanban Board */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            {ACTIVE_STATES.map((state) => (
              <div key={state} className="bg-gray-50 rounded-xl p-3">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PIPELINE_COLORS[state] }} />
                    <h3 className="font-semibold text-sm text-gray-700">{PIPELINE_LABELS[state]}</h3>
                  </div>
                  <span className="text-xs text-gray-500 bg-white px-2 py-0.5 rounded-full">
                    {oppsByState(state).length}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-3 font-medium">{formatCurrency(stateTotal(state))}</p>

                <div className="space-y-2">
                  {oppsByState(state).map((opp) => (
                    <div
                      key={opp.id}
                      className="bg-white rounded-lg p-3 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => {
                        const targets = VALID_TRANSITIONS[opp.stato] || []
                        if (targets.length > 0) setMovingOpp({ opp, targets })
                      }}
                    >
                      <p className="font-medium text-sm text-gray-800 mb-1">{opp.titolo}</p>
                      {opp.contact && (
                        <p className="text-xs text-gray-500">{opp.contact.nome} {opp.contact.cognome} - {opp.contact.azienda}</p>
                      )}
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-sm font-semibold text-accent flex items-center gap-0.5">
                          <Euro className="w-3.5 h-3.5" />
                          {formatCurrency(opp.valore_stimato)}
                        </span>
                        <span className="text-xs text-gray-400">{opp.probabilita_chiusura}%</span>
                      </div>
                    </div>
                  ))}
                  {oppsByState(state).length === 0 && (
                    <p className="text-xs text-gray-400 text-center py-4">Vuoto</p>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Closed deals summary */}
          <div className="grid grid-cols-2 gap-4">
            {CLOSED_STATES.map((state) => (
              <div key={state} className="card">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PIPELINE_COLORS[state] }} />
                  <h3 className="font-semibold text-sm">{PIPELINE_LABELS[state]}</h3>
                  <span className="text-xs text-gray-500 ml-auto">{oppsByState(state).length} deal</span>
                </div>
                <p className="text-lg font-bold">{formatCurrency(stateTotal(state))}</p>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Move modal */}
      {movingOpp && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setMovingOpp(null)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold mb-1">Sposta: {movingOpp.opp.titolo}</h3>
            <p className="text-sm text-gray-500 mb-4">Stato attuale: {PIPELINE_LABELS[movingOpp.opp.stato as PipelineState]}</p>
            <div className="space-y-2">
              {movingOpp.targets.map((target) => (
                <button
                  key={target}
                  onClick={() => moveOpportunity(movingOpp.opp, target)}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-lg border hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PIPELINE_COLORS[target as PipelineState] }} />
                    <span className="font-medium text-sm">{PIPELINE_LABELS[target as PipelineState]}</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </button>
              ))}
            </div>
            <button onClick={() => setMovingOpp(null)} className="w-full mt-3 text-sm text-gray-500 hover:text-gray-700">Annulla</button>
          </div>
        </div>
      )}

      {/* Create Form */}
      {showForm && (
        <OpportunityFormModal
          contacts={contacts}
          onClose={() => setShowForm(false)}
          onCreated={() => { setShowForm(false); load() }}
        />
      )}
    </div>
  )
}

function OpportunityFormModal({ contacts, onClose, onCreated }: {
  contacts: Contact[]
  onClose: () => void
  onCreated: () => void
}) {
  const [form, setForm] = useState({ contact_id: 0, titolo: '', valore_stimato: '', probabilita_chiusura: '10', data_chiusura_prevista: '', note: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.createOpportunity({
        contact_id: form.contact_id,
        titolo: form.titolo,
        valore_stimato: parseFloat(form.valore_stimato),
        probabilita_chiusura: parseInt(form.probabilita_chiusura),
        data_chiusura_prevista: form.data_chiusura_prevista || undefined,
        note: form.note || undefined,
      } as never)
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore')
    }
    setSaving(false)
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Nuova Opportunita</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">{error}</div>}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contatto *</label>
            <select
              className="input"
              value={form.contact_id}
              onChange={(e) => setForm({ ...form, contact_id: parseInt(e.target.value) })}
              required
            >
              <option value={0}>Seleziona contatto...</option>
              {contacts.map((c) => (
                <option key={c.id} value={c.id}>{c.nome} {c.cognome} - {c.azienda}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Titolo *</label>
            <input className="input" value={form.titolo} onChange={(e) => setForm({ ...form, titolo: e.target.value })} required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Valore stimato (EUR) *</label>
              <input className="input" type="number" step="100" value={form.valore_stimato} onChange={(e) => setForm({ ...form, valore_stimato: e.target.value })} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Probabilita (%)</label>
              <input className="input" type="number" min="0" max="100" value={form.probabilita_chiusura} onChange={(e) => setForm({ ...form, probabilita_chiusura: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data chiusura prevista</label>
            <input className="input" type="date" value={form.data_chiusura_prevista} onChange={(e) => setForm({ ...form, data_chiusura_prevista: e.target.value })} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Annulla</button>
            <button type="submit" disabled={saving || !form.contact_id} className="btn-primary disabled:opacity-50">
              {saving ? 'Salvataggio...' : 'Crea Opportunita'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
