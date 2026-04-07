import { useState, useEffect } from 'react'
import { Calendar, AlertTriangle, Clock } from 'lucide-react'
import type { ScadenzaItem } from '../../types'
import { api } from '../../services/api'

export default function ScadenzarioPage() {
  const [scadenze, setScadenze] = useState<ScadenzaItem[]>([])
  const [loading, setLoading] = useState(true)
  const [giorni, setGiorni] = useState(30)

  useEffect(() => {
    setLoading(true)
    api.getScadenzario(giorni)
      .then(data => setScadenze(data.scadenze))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [giorni])

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(v)

  const urgencyClass = (days: number) => {
    if (days < 0) return 'border-l-4 border-l-red-500 bg-red-50'
    if (days <= 7) return 'border-l-4 border-l-orange-400 bg-orange-50'
    if (days <= 15) return 'border-l-4 border-l-yellow-400 bg-yellow-50'
    return 'border-l-4 border-l-green-400 bg-green-50'
  }

  const scadute = scadenze.filter(s => s.giorni_alla_scadenza < 0)
  const inScadenza = scadenze.filter(s => s.giorni_alla_scadenza >= 0 && s.giorni_alla_scadenza <= 7)
  const totaleImporto = scadenze.reduce((s, sc) => s + sc.importo_totale, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Scadenzario</h1>
        <select className="input w-48" value={giorni} onChange={e => setGiorni(Number(e.target.value))}>
          <option value={7}>Prossimi 7 giorni</option>
          <option value={15}>Prossimi 15 giorni</option>
          <option value={30}>Prossimi 30 giorni</option>
          <option value={60}>Prossimi 60 giorni</option>
          <option value={90}>Prossimi 90 giorni</option>
        </select>
      </div>

      {/* Alert strip */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Scadute</p>
            <p className="text-lg font-bold text-red-600">{scadute.length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-orange-50 flex items-center justify-center">
            <Clock className="w-5 h-5 text-orange-500" />
          </div>
          <div>
            <p className="text-xs text-gray-500">In scadenza (7gg)</p>
            <p className="text-lg font-bold text-orange-600">{inScadenza.length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
            <Calendar className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Totale da incassare/pagare</p>
            <p className="text-lg font-bold text-primary">{formatCurrency(totaleImporto)}</p>
          </div>
        </div>
      </div>

      {/* Scadenze list */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Caricamento scadenzario...</div>
      ) : scadenze.length === 0 ? (
        <div className="card text-center py-12">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Nessuna scadenza nei prossimi {giorni} giorni.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {scadenze.map(s => (
            <div key={s.id} className={`card flex items-center justify-between ${urgencyClass(s.giorni_alla_scadenza)}`}>
              <div className="flex items-center gap-4">
                <div>
                  <p className="font-semibold text-gray-800">{s.numero}</p>
                  <p className="text-sm text-gray-500">{s.fornitore_o_cliente}</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${s.tipo === 'attiva' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {s.tipo}
                </span>
                <div className="text-right">
                  <p className="font-semibold text-gray-800">{formatCurrency(s.importo_totale)}</p>
                  <p className="text-xs text-gray-500">
                    {s.data_scadenza ? new Date(s.data_scadenza).toLocaleDateString('it-IT') : '-'}
                  </p>
                </div>
                <div className="w-20 text-right">
                  {s.giorni_alla_scadenza < 0 ? (
                    <span className="text-sm font-bold text-red-600">
                      {Math.abs(s.giorni_alla_scadenza)}gg fa
                    </span>
                  ) : s.giorni_alla_scadenza === 0 ? (
                    <span className="text-sm font-bold text-orange-600">Oggi</span>
                  ) : (
                    <span className="text-sm font-medium text-gray-600">
                      tra {s.giorni_alla_scadenza}gg
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
