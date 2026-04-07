export interface User {
  id: number
  username: string
  email: string
  full_name: string
  is_active: boolean
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface ChatMessage {
  id?: number
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_id?: string
  timestamp?: string
}

export interface ChatResponse {
  response: string
  conversation_id: number
  agent_id: string
  actions: Record<string, unknown>[]
  needs_human_review: boolean
}

export interface Conversation {
  id: number
  title: string
  main_agent: string | null
  created_at: string
  updated_at: string
}

export interface Notification {
  id: number
  agent: string
  type: string
  title: string
  message: string
  read: boolean
  created_at: string
}

export interface DashboardData {
  pipeline_value: number
  fatturato_mese: number
  progetti_attivi: number
  task_scaduti: number
  prossime_scadenze: unknown[]
}

export interface Contact {
  id: number
  nome: string
  cognome: string
  azienda: string
  email: string | null
  telefono: string | null
  ruolo: string | null
  fonte: string | null
  note: string | null
}

export interface Opportunity {
  id: number
  contact_id: number
  titolo: string
  valore_stimato: number
  stato: string
  probabilita_chiusura: number
  data_chiusura_prevista: string | null
  motivo_perdita: string | null
  note: string | null
  contact?: Contact
  created_at?: string
  updated_at?: string
}

export interface Contract {
  id: number
  opportunity_id: number
  contact_id: number
  titolo: string
  valore_totale: number
  data_inizio: string | null
  data_fine: string | null
  stato: string
  note: string | null
  created_at: string
}

export interface SAL {
  id: number
  contract_id: number
  numero_sal: number
  descrizione: string | null
  percentuale_avanzamento: number
  importo_maturato: number
  data_sal: string
  note: string | null
}

export interface PipelineStats {
  totale_opportunita: number
  valore_totale: number
  per_stato: Record<string, { count: number; value: number }>
  win_rate: number
  vinte: number
  perse: number
}

export interface Fattura {
  id: number
  contract_id: number | null
  tipo: 'attiva' | 'passiva'
  numero: string
  importo: number
  iva: number
  importo_totale: number
  data_emissione: string | null
  data_scadenza: string | null
  stato: 'emessa' | 'pagata' | 'scaduta'
  fornitore_o_cliente: string
  note: string | null
  data_pagamento: string | null
  created_at: string
  updated_at: string
}

export interface ScadenzaItem {
  id: number
  numero: string
  tipo: string
  importo_totale: number
  fornitore_o_cliente: string
  data_scadenza: string
  stato: string
  giorni_alla_scadenza: number
}

export interface CashFlowItem {
  mese: string
  label: string
  entrate: number
  uscite: number
  saldo: number
  is_past: boolean
}

export interface Collaboratore {
  id: number
  nome: string
  cognome: string
  tipo: 'dipendente' | 'consulente'
  email: string | null
  telefono: string | null
  tariffa_giornaliera: number | null
  competenze: string[] | null
  data_inizio_contratto: string | null
  data_fine_contratto: string | null
  stato: 'attivo' | 'inattivo'
  note: string | null
  created_at: string
}

export interface Progetto {
  id: number
  contract_id: number | null
  nome: string
  cliente: string | null
  data_inizio: string | null
  data_fine_prevista: string | null
  budget: number | null
  stato: 'pianificato' | 'attivo' | 'completato' | 'sospeso'
  percentuale_avanzamento: number
  note: string | null
  created_at: string
}

export interface TaskItem {
  id: number
  progetto_id: number
  collaboratore_id: number | null
  titolo: string
  descrizione: string | null
  priorita: 'alta' | 'media' | 'bassa'
  stato: 'da_fare' | 'in_corso' | 'completato' | 'bloccato'
  data_scadenza: string | null
  created_at: string
  completed_at: string | null
}

export interface ProgettoOverview {
  id: number
  nome: string
  cliente: string | null
  stato: string
  avanzamento: number
  semaforo: 'verde' | 'giallo' | 'rosso'
  budget: number | null
  ore_registrate: number
  task_totali: number
  task_completati: number
  data_fine_prevista: string | null
}

export interface Contenuto {
  id: number
  titolo: string
  tipo: 'post_linkedin' | 'articolo_blog' | 'case_study'
  stato: 'bozza' | 'in_revisione' | 'pubblicato'
  data_pubblicazione: string | null
  autore: string | null
  contenuto_testo: string | null
  metriche: Record<string, unknown> | null
  note: string | null
  created_at: string
  updated_at: string
}

export interface ContattoEvento {
  id: number
  nome: string
  email: string | null
  azienda: string | null
  evento: string
  data_evento: string | null
  interesse: string | null
  note: string | null
  convertito_a_contatto_id: number | null
  created_at: string
}

export interface AuditLogEntry {
  id: number
  user_id: number | null
  agent: string
  action: string
  entity_type: string | null
  entity_id: number | null
  details: Record<string, unknown> | null
  timestamp: string
}

export type PipelineState = 'lead' | 'qualificato' | 'proposta' | 'negoziazione' | 'vinto' | 'perso'

export const PIPELINE_LABELS: Record<PipelineState, string> = {
  lead: 'Lead',
  qualificato: 'Qualificato',
  proposta: 'Proposta Inviata',
  negoziazione: 'Negoziazione',
  vinto: 'Chiuso Vinto',
  perso: 'Chiuso Perso',
}

export const PIPELINE_COLORS: Record<PipelineState, string> = {
  lead: '#94A3B8',
  qualificato: '#6B3FA0',
  proposta: '#1B1F6B',
  negoziazione: '#E8712B',
  vinto: '#22C55E',
  perso: '#EF4444',
}
