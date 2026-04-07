import { useState, useEffect } from 'react'
import { Search, Plus, Mail, Phone, Building2, X } from 'lucide-react'
import type { Contact } from '../../types'
import { api } from '../../services/api'

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([])
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)

  const loadContacts = async (q?: string) => {
    setLoading(true)
    try {
      const data = await api.getContacts(q)
      setContacts(data)
    } catch { /* ignore */ }
    setLoading(false)
  }

  useEffect(() => {
    loadContacts()
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => loadContacts(search || undefined), 300)
    return () => clearTimeout(timer)
  }, [search])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Contatti</h1>
        <button onClick={() => setShowForm(true)} className="btn-accent flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nuovo Contatto
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Cerca per nome, azienda o email..."
          className="input pl-10"
        />
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Nome</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Azienda</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Email</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Telefono</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Ruolo</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Fonte</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-400">Caricamento...</td>
              </tr>
            ) : contacts.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                  {search ? 'Nessun contatto trovato' : 'Nessun contatto. Creane uno!'}
                </td>
              </tr>
            ) : (
              contacts.map((c) => (
                <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center text-primary font-semibold text-sm">
                        {c.nome[0]}{c.cognome[0]}
                      </div>
                      <span className="font-medium text-gray-800">{c.nome} {c.cognome}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    <div className="flex items-center gap-1.5">
                      <Building2 className="w-4 h-4 text-gray-400" />
                      {c.azienda}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    {c.email && (
                      <div className="flex items-center gap-1.5">
                        <Mail className="w-4 h-4 text-gray-400" />
                        {c.email}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    {c.telefono && (
                      <div className="flex items-center gap-1.5">
                        <Phone className="w-4 h-4 text-gray-400" />
                        {c.telefono}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-600">{c.ruolo || '-'}</td>
                  <td className="px-6 py-4">
                    {c.fonte && (
                      <span className="px-2 py-1 bg-primary-50 text-primary text-xs font-medium rounded-full">
                        {c.fonte}
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Form Modal */}
      {showForm && (
        <ContactFormModal
          onClose={() => setShowForm(false)}
          onCreated={() => {
            setShowForm(false)
            loadContacts()
          }}
        />
      )}
    </div>
  )
}

function ContactFormModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ nome: '', cognome: '', azienda: '', email: '', telefono: '', ruolo: '', fonte: '', note: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.createContact(form)
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore')
    }
    setSaving(false)
  }

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm({ ...form, [field]: e.target.value })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Nuovo Contatto</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">{error}</div>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
              <input className="input" value={form.nome} onChange={set('nome')} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cognome *</label>
              <input className="input" value={form.cognome} onChange={set('cognome')} required />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Azienda *</label>
            <input className="input" value={form.azienda} onChange={set('azienda')} required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input className="input" type="email" value={form.email} onChange={set('email')} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
              <input className="input" value={form.telefono} onChange={set('telefono')} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ruolo</label>
              <input className="input" value={form.ruolo} onChange={set('ruolo')} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fonte</label>
              <input className="input" value={form.fonte} onChange={set('fonte')} placeholder="es. LinkedIn, Evento" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Note</label>
            <textarea className="input" rows={2} value={form.note} onChange={set('note')} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Annulla</button>
            <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
              {saving ? 'Salvataggio...' : 'Crea Contatto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
