import { useState, useEffect } from 'react'
import { Plus, FileText, X, Users } from 'lucide-react'
import type { Contenuto, ContattoEvento } from '../../types'
import { api } from '../../services/api'

const TIPO_LABELS: Record<string, { label: string; color: string }> = {
  post_linkedin: { label: 'LinkedIn', color: 'bg-blue-100 text-blue-700' },
  articolo_blog: { label: 'Blog', color: 'bg-purple-100 text-purple-700' },
  case_study: { label: 'Case Study', color: 'bg-orange-100 text-orange-700' },
}

const STATO_LABELS: Record<string, { label: string; color: string }> = {
  bozza: { label: 'Bozza', color: 'bg-gray-100 text-gray-600' },
  in_revisione: { label: 'In Revisione', color: 'bg-yellow-100 text-yellow-700' },
  pubblicato: { label: 'Pubblicato', color: 'bg-green-100 text-green-700' },
}

type TabView = 'contenuti' | 'contatti'

export default function CalendarioPage() {
  const [tab, setTab] = useState<TabView>('contenuti')
  const [contenuti, setContenuti] = useState<Contenuto[]>([])
  const [contatti, setContatti] = useState<ContattoEvento[]>([])
  const [loading, setLoading] = useState(true)
  const [filterTipo, setFilterTipo] = useState('')
  const [filterStato, setFilterStato] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [showContattoForm, setShowContattoForm] = useState(false)

  const loadContenuti = () => {
    setLoading(true)
    api.getContenuti(filterTipo || undefined, filterStato || undefined)
      .then(setContenuti)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  const loadContatti = () => {
    setLoading(true)
    api.getContattiEvento()
      .then(setContatti)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (tab === 'contenuti') loadContenuti()
    else loadContatti()
  }, [tab, filterTipo, filterStato])

  const formatDate = (d: string | null) =>
    d ? new Date(d).toLocaleDateString('it-IT') : '—'

  const kpiBozze = contenuti.filter(c => c.stato === 'bozza').length
  const kpiRevisione = contenuti.filter(c => c.stato === 'in_revisione').length
  const kpiPubblicati = contenuti.filter(c => c.stato === 'pubblicato').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Marketing</h1>
          <p className="text-sm text-gray-500">Calendario editoriale e contatti eventi</p>
        </div>
        <div className="flex gap-2">
          {tab === 'contenuti' ? (
            <button onClick={() => setShowForm(true)} className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 text-sm">
              <Plus className="w-4 h-4" /> Nuovo Contenuto
            </button>
          ) : (
            <button onClick={() => setShowContattoForm(true)} className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 text-sm">
              <Plus className="w-4 h-4" /> Nuovo Contatto
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setTab('contenuti')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition ${tab === 'contenuti' ? 'bg-white shadow text-primary' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <FileText className="w-4 h-4 inline mr-1" /> Contenuti
        </button>
        <button
          onClick={() => setTab('contatti')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition ${tab === 'contatti' ? 'bg-white shadow text-primary' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <Users className="w-4 h-4 inline mr-1" /> Contatti Evento
        </button>
      </div>

      {tab === 'contenuti' && (
        <>
          {/* KPI Strip */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 uppercase">Bozze</p>
              <p className="text-2xl font-bold text-gray-700">{kpiBozze}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 uppercase">In Revisione</p>
              <p className="text-2xl font-bold text-yellow-600">{kpiRevisione}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 uppercase">Pubblicati</p>
              <p className="text-2xl font-bold text-green-600">{kpiPubblicati}</p>
            </div>
          </div>

          {/* Filters */}
          <div className="flex gap-3">
            <select value={filterTipo} onChange={e => setFilterTipo(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-white">
              <option value="">Tutti i tipi</option>
              <option value="post_linkedin">LinkedIn</option>
              <option value="articolo_blog">Blog</option>
              <option value="case_study">Case Study</option>
            </select>
            <select value={filterStato} onChange={e => setFilterStato(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-white">
              <option value="">Tutti gli stati</option>
              <option value="bozza">Bozza</option>
              <option value="in_revisione">In Revisione</option>
              <option value="pubblicato">Pubblicato</option>
            </select>
          </div>

          {/* Content Cards */}
          {loading ? (
            <div className="text-center py-12 text-gray-400">Caricamento...</div>
          ) : contenuti.length === 0 ? (
            <div className="text-center py-12 text-gray-400">Nessun contenuto trovato</div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {contenuti.map(c => (
                <ContentCard key={c.id} contenuto={c} onUpdate={loadContenuti} />
              ))}
            </div>
          )}
        </>
      )}

      {tab === 'contatti' && (
        <>
          <div className="bg-white rounded-xl border p-4">
            <p className="text-xs text-gray-500 uppercase">Totale Contatti Evento</p>
            <p className="text-2xl font-bold text-primary">{contatti.length}</p>
          </div>

          {loading ? (
            <div className="text-center py-12 text-gray-400">Caricamento...</div>
          ) : contatti.length === 0 ? (
            <div className="text-center py-12 text-gray-400">Nessun contatto evento registrato</div>
          ) : (
            <div className="bg-white rounded-xl border overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                  <tr>
                    <th className="text-left px-4 py-3">Nome</th>
                    <th className="text-left px-4 py-3">Azienda</th>
                    <th className="text-left px-4 py-3">Evento</th>
                    <th className="text-left px-4 py-3">Data</th>
                    <th className="text-left px-4 py-3">Interesse</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {contatti.map(ce => (
                    <tr key={ce.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{ce.nome}</td>
                      <td className="px-4 py-3 text-gray-600">{ce.azienda || '—'}</td>
                      <td className="px-4 py-3">{ce.evento}</td>
                      <td className="px-4 py-3 text-gray-500">{formatDate(ce.data_evento)}</td>
                      <td className="px-4 py-3 text-gray-500">{ce.interesse || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Create Contenuto Modal */}
      {showForm && <ContenutoModal onClose={() => setShowForm(false)} onCreated={loadContenuti} />}
      {showContattoForm && <ContattoEventoModal onClose={() => setShowContattoForm(false)} onCreated={loadContatti} />}
    </div>
  )
}

function ContentCard({ contenuto: c, onUpdate }: { contenuto: Contenuto; onUpdate: () => void }) {
  const tipo = TIPO_LABELS[c.tipo] || { label: c.tipo, color: 'bg-gray-100 text-gray-600' }
  const stato = STATO_LABELS[c.stato] || { label: c.stato, color: 'bg-gray-100 text-gray-600' }
  const formatDate = (d: string | null) => d ? new Date(d).toLocaleDateString('it-IT') : null

  const nextStato = c.stato === 'bozza' ? 'in_revisione' : c.stato === 'in_revisione' ? 'pubblicato' : null
  const nextLabel = c.stato === 'bozza' ? 'Invia a Revisione' : c.stato === 'in_revisione' ? 'Pubblica' : null

  const advance = () => {
    if (!nextStato) return
    api.updateContenuto(c.id, { stato: nextStato }).then(onUpdate).catch(() => {})
  }

  return (
    <div className="bg-white rounded-xl border p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900 leading-tight">{c.titolo}</h3>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${tipo.color}`}>
          {tipo.label}
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-500">
        {c.autore && <span>di {c.autore}</span>}
        {c.data_pubblicazione && <span>| {formatDate(c.data_pubblicazione)}</span>}
      </div>
      {c.contenuto_testo && (
        <p className="text-sm text-gray-600 line-clamp-3">{c.contenuto_testo}</p>
      )}
      <div className="flex items-center justify-between mt-auto pt-2 border-t">
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${stato.color}`}>
          {stato.label}
        </span>
        {nextLabel && (
          <button onClick={advance} className="text-xs text-primary hover:underline font-medium">
            {nextLabel} &rarr;
          </button>
        )}
      </div>
    </div>
  )
}

function ContenutoModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ titolo: '', tipo: 'post_linkedin', autore: '', data_pubblicazione: '', contenuto_testo: '', note: '' })
  const [saving, setSaving] = useState(false)

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.titolo.trim()) return
    setSaving(true)
    api.createContenuto({
      titolo: form.titolo,
      tipo: form.tipo,
      autore: form.autore || undefined,
      data_pubblicazione: form.data_pubblicazione || undefined,
      contenuto_testo: form.contenuto_testo || undefined,
      note: form.note || undefined,
    }).then(() => { onCreated(); onClose() })
      .catch(() => {})
      .finally(() => setSaving(false))
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Nuovo Contenuto</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-gray-400" /></button>
        </div>
        <form onSubmit={submit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Titolo *</label>
            <input value={form.titolo} onChange={e => setForm({ ...form, titolo: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
              <select value={form.tipo} onChange={e => setForm({ ...form, tipo: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm bg-white">
                <option value="post_linkedin">Post LinkedIn</option>
                <option value="articolo_blog">Articolo Blog</option>
                <option value="case_study">Case Study</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Autore</label>
              <input value={form.autore} onChange={e => setForm({ ...form, autore: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Pubblicazione</label>
            <input type="date" value={form.data_pubblicazione} onChange={e => setForm({ ...form, data_pubblicazione: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contenuto</label>
            <textarea value={form.contenuto_testo} onChange={e => setForm({ ...form, contenuto_testo: e.target.value })} rows={4} className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Note</label>
            <input value={form.note} onChange={e => setForm({ ...form, note: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Annulla</button>
            <button type="submit" disabled={saving} className="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary/90 disabled:opacity-50">
              {saving ? 'Salvataggio...' : 'Crea Contenuto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ContattoEventoModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ nome: '', email: '', azienda: '', evento: '', data_evento: '', interesse: '', note: '' })
  const [saving, setSaving] = useState(false)

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.nome.trim() || !form.evento.trim()) return
    setSaving(true)
    api.createContattoEvento({
      nome: form.nome,
      evento: form.evento,
      email: form.email || undefined,
      azienda: form.azienda || undefined,
      data_evento: form.data_evento || undefined,
      interesse: form.interesse || undefined,
      note: form.note || undefined,
    }).then(() => { onCreated(); onClose() })
      .catch(() => {})
      .finally(() => setSaving(false))
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Nuovo Contatto Evento</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-gray-400" /></button>
        </div>
        <form onSubmit={submit} className="p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
              <input value={form.nome} onChange={e => setForm({ ...form, nome: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Azienda</label>
              <input value={form.azienda} onChange={e => setForm({ ...form, azienda: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Evento *</label>
              <input value={form.evento} onChange={e => setForm({ ...form, evento: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" required />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Data Evento</label>
              <input type="date" value={form.data_evento} onChange={e => setForm({ ...form, data_evento: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Interesse</label>
              <input value={form.interesse} onChange={e => setForm({ ...form, interesse: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Note</label>
            <input value={form.note} onChange={e => setForm({ ...form, note: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Annulla</button>
            <button type="submit" disabled={saving} className="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary/90 disabled:opacity-50">
              {saving ? 'Salvataggio...' : 'Registra Contatto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
