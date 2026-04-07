import { useState, useEffect } from 'react'
import { FileText, ChevronDown, ChevronUp, Plus } from 'lucide-react'
import type { Contract, SAL } from '../../types'
import { api } from '../../services/api'

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<number | null>(null)

  useEffect(() => {
    api.getContracts().then(setContracts).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v)

  const statusColor = (stato: string) => {
    switch (stato) {
      case 'attivo': return 'bg-green-100 text-green-700'
      case 'completato': return 'bg-blue-100 text-blue-700'
      case 'sospeso': return 'bg-yellow-100 text-yellow-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Contratti</h1>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Caricamento...</div>
      ) : contracts.length === 0 ? (
        <div className="card text-center py-12">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Nessun contratto. I contratti vengono creati automaticamente quando un'opportunita viene chiusa come "Vinto".</p>
        </div>
      ) : (
        <div className="space-y-4">
          {contracts.map((contract) => (
            <div key={contract.id} className="card">
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(expanded === contract.id ? null : contract.id)}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">{contract.titolo}</h3>
                    <p className="text-sm text-gray-500">
                      Contratto #{contract.id} - {contract.data_inizio ? new Date(contract.data_inizio).toLocaleDateString('it-IT') : 'N/A'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-lg font-bold text-primary">{formatCurrency(contract.valore_totale)}</span>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusColor(contract.stato)}`}>
                    {contract.stato}
                  </span>
                  {expanded === contract.id ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                </div>
              </div>

              {expanded === contract.id && <SALSection contractId={contract.id} contractValue={contract.valore_totale} />}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function SALSection({ contractId, contractValue }: { contractId: number; contractValue: number }) {
  const [salEntries, setSalEntries] = useState<SAL[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    api.getContractSAL(contractId).then(setSalEntries).catch(() => {}).finally(() => setLoading(false))
  }, [contractId])

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v)

  const lastSAL = salEntries.length > 0 ? salEntries[salEntries.length - 1] : null
  const totalMaturato = salEntries.reduce((sum, s) => sum + s.importo_maturato, 0)

  const handleCreateSAL = async (data: { percentuale_avanzamento: number; importo_maturato: number; descrizione: string }) => {
    await api.createSAL({ contract_id: contractId, ...data })
    const updated = await api.getContractSAL(contractId)
    setSalEntries(updated)
    setShowForm(false)
  }

  return (
    <div className="mt-4 pt-4 border-t border-gray-100">
      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-600">Avanzamento</span>
          <span className="text-sm font-bold text-primary">{lastSAL?.percentuale_avanzamento ?? 0}%</span>
        </div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-500"
            style={{ width: `${lastSAL?.percentuale_avanzamento ?? 0}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-1">
          <span className="text-xs text-gray-500">Maturato: {formatCurrency(totalMaturato)}</span>
          <span className="text-xs text-gray-500">Totale: {formatCurrency(contractValue)}</span>
        </div>
      </div>

      {/* SAL entries */}
      {loading ? (
        <p className="text-gray-400 text-sm">Caricamento SAL...</p>
      ) : (
        <>
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-sm text-gray-700">Stati di Avanzamento Lavori</h4>
            <button onClick={() => setShowForm(true)} className="text-accent text-sm font-medium flex items-center gap-1 hover:underline">
              <Plus className="w-4 h-4" /> Aggiungi SAL
            </button>
          </div>

          {salEntries.length === 0 ? (
            <p className="text-gray-400 text-sm">Nessun SAL registrato.</p>
          ) : (
            <div className="space-y-2">
              {salEntries.map((sal) => (
                <div key={sal.id} className="flex items-center gap-4 py-2 px-3 bg-gray-50 rounded-lg">
                  <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold">
                    {sal.numero_sal}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{sal.descrizione || `SAL #${sal.numero_sal}`}</p>
                    <p className="text-xs text-gray-500">{new Date(sal.data_sal).toLocaleDateString('it-IT')}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold">{sal.percentuale_avanzamento}%</p>
                    <p className="text-xs text-gray-500">{formatCurrency(sal.importo_maturato)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* SAL Form */}
      {showForm && (
        <SALForm onSubmit={handleCreateSAL} onCancel={() => setShowForm(false)} />
      )}
    </div>
  )
}

function SALForm({ onSubmit, onCancel }: {
  onSubmit: (data: { percentuale_avanzamento: number; importo_maturato: number; descrizione: string }) => Promise<void>
  onCancel: () => void
}) {
  const [form, setForm] = useState({ percentuale: '', importo: '', descrizione: '' })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    await onSubmit({
      percentuale_avanzamento: parseFloat(form.percentuale),
      importo_maturato: parseFloat(form.importo),
      descrizione: form.descrizione,
    })
    setSaving(false)
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3 p-4 bg-accent-50 rounded-lg space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Avanzamento %</label>
          <input className="input text-sm" type="number" min="0" max="100" value={form.percentuale} onChange={(e) => setForm({ ...form, percentuale: e.target.value })} required />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Importo maturato</label>
          <input className="input text-sm" type="number" step="100" value={form.importo} onChange={(e) => setForm({ ...form, importo: e.target.value })} required />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Descrizione</label>
          <input className="input text-sm" value={form.descrizione} onChange={(e) => setForm({ ...form, descrizione: e.target.value })} />
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onCancel} className="text-sm text-gray-500 hover:text-gray-700">Annulla</button>
        <button type="submit" disabled={saving} className="btn-accent text-sm py-1.5 disabled:opacity-50">
          {saving ? 'Salvataggio...' : 'Registra SAL'}
        </button>
      </div>
    </form>
  )
}
