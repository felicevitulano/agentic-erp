import type { AuthTokens, User, DashboardData, Notification, Conversation, ChatMessage, Contact, Opportunity, Contract, SAL, PipelineStats, Fattura, ScadenzaItem, CashFlowItem, Collaboratore, Progetto, TaskItem, ProgettoOverview, Contenuto, ContattoEvento, AuditLogEntry } from '../types'

const API_BASE = '/api'

function getToken(): string | null {
  return localStorage.getItem('access_token')
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (response.status === 401) {
    // Try refresh
    const refreshed = await tryRefresh()
    if (refreshed) {
      headers['Authorization'] = `Bearer ${getToken()}`
      const retry = await fetch(`${API_BASE}${path}`, { ...options, headers })
      if (!retry.ok) throw new Error(`API error: ${retry.status}`)
      return retry.json()
    }
    localStorage.clear()
    window.location.href = '/login'
    throw new Error('Non autenticato')
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Errore sconosciuto' }))
    throw new Error(error.detail || `Errore ${response.status}`)
  }

  return response.json()
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return false
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) return false
    const tokens: AuthTokens = await res.json()
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    return true
  } catch {
    return false
  }
}

export const api = {
  // Auth
  login: (username: string, password: string) =>
    request<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  getMe: () => request<User>('/auth/me'),

  // Dashboard
  getDashboard: () => request<DashboardData>('/dashboard'),

  // Notifications
  getNotifications: () => request<Notification[]>('/notifications'),
  markNotificationRead: (id: number) =>
    request(`/notifications/${id}/read`, { method: 'PUT' }),

  // Chat
  sendMessage: (message: string, conversationId?: number) =>
    request<{ response: string; conversation_id: number; agent_id: string }>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),

  getConversations: () => request<Conversation[]>('/conversations'),
  getMessages: (conversationId: number) =>
    request<ChatMessage[]>(`/conversations/${conversationId}/messages`),

  // Agents
  getAgentsStatus: () => request<{ id: string; name: string; description: string }[]>('/agents/status'),

  // Contacts
  getContacts: (q?: string) => request<Contact[]>(`/contacts${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  getContact: (id: number) => request<Contact>(`/contacts/${id}`),
  createContact: (data: Partial<Contact>) =>
    request<Contact>('/contacts', { method: 'POST', body: JSON.stringify(data) }),
  updateContact: (id: number, data: Partial<Contact>) =>
    request<Contact>(`/contacts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteContact: (id: number) =>
    request(`/contacts/${id}`, { method: 'DELETE' }),

  // Opportunities
  getOpportunities: (stato?: string) =>
    request<Opportunity[]>(`/opportunities${stato ? `?stato=${stato}` : ''}`),
  getOpportunity: (id: number) => request<Opportunity>(`/opportunities/${id}`),
  createOpportunity: (data: Partial<Opportunity>) =>
    request<Opportunity>('/opportunities', { method: 'POST', body: JSON.stringify(data) }),
  updateOpportunity: (id: number, data: Partial<Opportunity>) =>
    request<Opportunity>(`/opportunities/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Pipeline
  getPipelineStats: () => request<PipelineStats>('/pipeline/stats'),

  // Contracts
  getContracts: (stato?: string) =>
    request<Contract[]>(`/contracts${stato ? `?stato=${stato}` : ''}`),
  getContract: (id: number) => request<Contract>(`/contracts/${id}`),

  // SAL
  getContractSAL: (contractId: number) => request<SAL[]>(`/contracts/${contractId}/sal`),
  createSAL: (data: { contract_id: number; percentuale_avanzamento: number; importo_maturato: number; descrizione?: string }) =>
    request<SAL>('/sal', { method: 'POST', body: JSON.stringify(data) }),

  // Fatture
  getFatture: (tipo?: string, stato?: string) => {
    const params = new URLSearchParams()
    if (tipo) params.set('tipo', tipo)
    if (stato) params.set('stato', stato)
    const qs = params.toString()
    return request<Fattura[]>(`/fatture${qs ? `?${qs}` : ''}`)
  },
  getFattura: (id: number) => request<Fattura>(`/fatture/${id}`),
  createFattura: (data: {
    tipo: string; numero: string; importo: number; iva?: number;
    data_scadenza: string; fornitore_o_cliente: string;
    contract_id?: number; data_emissione?: string; note?: string
  }) => request<Fattura>('/fatture', { method: 'POST', body: JSON.stringify(data) }),
  updateFattura: (id: number, data: { stato?: string; data_pagamento?: string; note?: string }) =>
    request<Fattura>(`/fatture/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Scadenzario
  getScadenzario: (giorni?: number, tipo?: string) => {
    const params = new URLSearchParams()
    if (giorni) params.set('giorni', String(giorni))
    if (tipo) params.set('tipo', tipo)
    return request<{ scadenze: ScadenzaItem[]; totale: number }>(`/scadenzario?${params.toString()}`)
  },

  // Cash Flow
  getCashFlow: (mesi?: number) =>
    request<{ cash_flow: CashFlowItem[] }>(`/cash-flow${mesi ? `?mesi=${mesi}` : ''}`),

  // Report Mensile
  getReportMensile: (mese?: number, anno?: number) => {
    const params = new URLSearchParams()
    if (mese) params.set('mese', String(mese))
    if (anno) params.set('anno', String(anno))
    const qs = params.toString()
    return request<Record<string, unknown>>(`/finance/report-mensile${qs ? `?${qs}` : ''}`)
  },

  // Fatture Scadute
  getFattureScadute: () =>
    request<{ fatture_scadute: Array<{ id: number; numero: string; importo_totale: number; fornitore_o_cliente: string; data_scadenza: string; giorni_scaduta: number; alert_30gg: boolean }>; totale: number; valore_totale_scaduto: number }>('/fatture-scadute'),

  // Collaboratori (HR)
  getCollaboratori: (stato?: string, q?: string) => {
    const params = new URLSearchParams()
    if (stato) params.set('stato', stato)
    if (q) params.set('q', q)
    const qs = params.toString()
    return request<Collaboratore[]>(`/collaboratori${qs ? `?${qs}` : ''}`)
  },
  createCollaboratore: (data: Partial<Collaboratore> & { nome: string; cognome: string; tipo: string }) =>
    request<Collaboratore>('/collaboratori', { method: 'POST', body: JSON.stringify(data) }),
  updateCollaboratore: (id: number, data: Record<string, unknown>) =>
    request<Collaboratore>(`/collaboratori/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Progetti (Operations)
  getProgetti: (stato?: string) =>
    request<Progetto[]>(`/progetti${stato ? `?stato=${stato}` : ''}`),
  createProgetto: (data: Partial<Progetto> & { nome: string }) =>
    request<Progetto>('/progetti', { method: 'POST', body: JSON.stringify(data) }),
  updateProgetto: (id: number, data: Record<string, unknown>) =>
    request<Progetto>(`/progetti/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  getProgettiOverview: () =>
    request<{ progetti: ProgettoOverview[]; totale: number }>('/progetti-overview'),

  // Tasks
  getTasks: (progetto_id?: number, stato?: string) => {
    const params = new URLSearchParams()
    if (progetto_id) params.set('progetto_id', String(progetto_id))
    if (stato) params.set('stato', stato)
    const qs = params.toString()
    return request<TaskItem[]>(`/tasks${qs ? `?${qs}` : ''}`)
  },
  createTask: (data: { progetto_id: number; titolo: string; priorita?: string; collaboratore_id?: number; data_scadenza?: string }) =>
    request<TaskItem>('/tasks', { method: 'POST', body: JSON.stringify(data) }),
  updateTask: (id: number, data: Record<string, unknown>) =>
    request<TaskItem>(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Timesheet
  createTimesheet: (data: { collaboratore_id: number; progetto_id: number; data: string; ore: number; descrizione_attivita?: string }) =>
    request('/timesheet', { method: 'POST', body: JSON.stringify(data) }),

  // Contenuti (Marketing)
  getContenuti: (tipo?: string, stato?: string) => {
    const params = new URLSearchParams()
    if (tipo) params.set('tipo', tipo)
    if (stato) params.set('stato', stato)
    const qs = params.toString()
    return request<Contenuto[]>(`/contenuti${qs ? `?${qs}` : ''}`)
  },
  createContenuto: (data: { titolo: string; tipo: string; autore?: string; data_pubblicazione?: string; contenuto_testo?: string; note?: string }) =>
    request<Contenuto>('/contenuti', { method: 'POST', body: JSON.stringify(data) }),
  updateContenuto: (id: number, data: { stato?: string; titolo?: string; contenuto_testo?: string; note?: string }) =>
    request<Contenuto>(`/contenuti/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Contatti Evento
  getContattiEvento: (evento?: string) =>
    request<ContattoEvento[]>(`/contatti-evento${evento ? `?evento=${encodeURIComponent(evento)}` : ''}`),
  createContattoEvento: (data: { nome: string; evento: string; email?: string; azienda?: string; data_evento?: string; interesse?: string; note?: string }) =>
    request<ContattoEvento>('/contatti-evento', { method: 'POST', body: JSON.stringify(data) }),

  // Audit Log
  getAuditLog: (agent?: string, action?: string, limit?: number) => {
    const params = new URLSearchParams()
    if (agent) params.set('agent', agent)
    if (action) params.set('action', action)
    if (limit) params.set('limit', String(limit))
    const qs = params.toString()
    return request<AuditLogEntry[]>(`/audit-log${qs ? `?${qs}` : ''}`)
  },
}
