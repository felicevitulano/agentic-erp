import { useState, useEffect } from 'react'
import { Plus, Receipt, X, ArrowUpRight, ArrowDownLeft } from 'lucide-react'
import type { Fattura } from '../../types'
import { api } from '../../services/api'

export default function FatturePage() {
  const [fatture, setFatture] = useState<Fattura[]>([])
  const [loading, setLoading] = useState(true)
  const [filterTipo, setFilterTipo] = useState<string>('')
  const [filterStato, setFilterStato] = useState<string>('')
  const [showForm, setShowForm] = useState(false)

  const load = () => {
    setLoading(true)
    api.getFatture(filterTipo || undefined, filterStato || undefined)
      .then(setFatture)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filterTipo, filterStato])

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(v)

  const statusColor = (stato: string) => {
    switch (stato) {
      case 'emessa': return 'bg-blue-100 text-blue-700'
      case 'pagata': return 'bg-green-100 text-green-700'
      case 'scaduta': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const totaleAttive = fatture.filter(f => f.tipo === 'attiva').reduce((s, f) => s + f.importo_totale, 0)
  const totalePassive = fatture.filter(f => f.tipo === 'passiva').reduce((s, f) => s + f.importo_totale, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Fatture</h1>
        <button onClick={() => setShowForm(true)} className="btn-accent flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuova Fattura
        </button>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
            <ArrowUpRight className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Totale Attive</p>
            <p className="text-lg font-bold text-green-600">{formatCurrency(totaleAttive)}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
            <ArrowDownLeft className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Totale Passive</p>
            <p className="text-lg font-bold text-red-600">{formatCurrency(totalePassive)}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
            <Receipt className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Saldo</p>
            <p className="text-lg font-bold text-primary">{formatCurrency(totaleAttive - totalePassive)}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select className="input w-40" value={filterTipo} onChange={e => setFilterTipo(e.target.value)}>
          <option value="">Tutti i tipi</option>
          <option value="attiva">Attive</option>
          <option value="passiva">Passive</option>
        </select>
        <select className="input w-40" value={filterStato} onChange={e => setFilterStato(e.target.value)}>
          <option value="">Tutti gli stati</option>
          <option value="emessa">Emesse</option>
          <option value="pagata">Pagate</option>
          <option value="scaduta">Scadute</option>
        </select>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Numero</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Tipo</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Cliente/Fornitore</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Importo</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Totale (IVA)</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Scadenza</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Stato</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Azioni</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="px-6 py-12 text-center text-gray-400">Caricamento...</td></tr>
            ) : fatture.length === 0 ? (
              <tr><td colSpan={8} className="px-6 py-12 text-center text-gray-400">Nessuna fattura trovata</td></tr>
            ) : (
              fatture.map(f => (
                <tr key={f.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-800">{f.numero}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1 text-xs font-medium ${f.tipo === 'attiva' ? 'text-green-600' : 'text-red-600'}`}>
                      {f.tipo === 'attiva' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownLeft className="w-3 h-3" />}
                      {f.tipo}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-600">{f.fornitore_o_cliente}</td>
                  <td className="px-6 py-4 text-gray-600">{formatCurrency(f.importo)}</td>
                  <td className="px-6 py-4 font-semibold text-gray-800">{formatCurrency(f.importo_totale)}</td>
                  <td className="px-6 py-4 text-gray-600">
                    {f.data_scadenza ? new Date(f.data_scadenza).toLocaleDateString('it-IT') : '-'}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusColor(f.stato)}`}>
                      {f.stato}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {f.stato === 'emessa' && (
                      <button
                        className="text-xs text-accent font-medium hover:underline"
                        onClick={async () => {
                          await api.updateFattura(f.id, { stato: 'pagata', data_pagamento: new Date().toISOString().split('T')[0] })
                          load()
                        }}
                      >
                        Segna Pagata
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showForm && <FatturaFormModal onClose={() => setShowForm(false)} onCreated={() => { setShowForm(false); load() }} />}
    </div>
  )
}

function FatturaFormModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    tipo: 'attiva', numero: '', importo: '', iva: '22',
    data_scadenza: '', fornitore_o_cliente: '', note: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.createFattura({
        tipo: form.tipo,
        numero: form.numero,
        importo: parseFloat(form.importo),
        iva: parseFloat(form.iva),
        data_scadenza: form.data_scadenza,
        fornitore_o_cliente: form.fornitore_o_cliente,
        note: form.note || undefined,
      })
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore')
    }
    setSaving(false)
  }

  const importoNetto = parseFloat(form.importo) || 0
  const ivaPerc = parseFloat(form.iva) || 0
  const totale = importoNetto * (1 + ivaPerc / 100)

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Nuova Fattura</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">{error}</div>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo *</label>
              <select className="input" value={form.tipo} onChange={e => setForm({ ...form, tipo: e.target.value })}>
                <option value="attiva">Attiva (emessa)</option>
                <option value="passiva">Passiva (ricevuta)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Numero *</label>
              <input className="input" value={form.numero} onChange={e => setForm({ ...form, numero: e.target.value })} placeholder="FT-2026-001" required />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{form.tipo === 'attiva' ? 'Cliente' : 'Fornitore'} *</label>
            <input className="input" value={form.fornitore_o_cliente} onChange={e => setForm({ ...form, fornitore_o_cliente: e.target.value })} required />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Importo netto *</label>
              <input className="input" type="number" step="0.01" value={form.importo} onChange={e => setForm({ ...form, importo: e.target.value })} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">IVA %</label>
              <input className="input" type="number" step="1" value={form.iva} onChange={e => setForm({ ...form, iva: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Totale</label>
              <div className="input bg-gray-50 flex items-center font-semibold text-primary">
                {new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(totale)}
              </div>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data scadenza *</label>
            <input className="input" type="date" value={form.data_scadenza} onChange={e => setForm({ ...form, data_scadenza: e.target.value })} required />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Annulla</button>
            <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
              {saving ? 'Salvataggio...' : 'Registra Fattura'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
