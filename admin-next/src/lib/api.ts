// Client SDK for backend admin API

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function getAuthHeader(): string {
  if (typeof window !== "undefined") {
    const creds = sessionStorage.getItem("admin_creds");
    if (creds) return "Basic " + creds;
  }
  const u = process.env.ADMIN_USER || "dheiver";
  const p = process.env.ADMIN_PASS || "andradelemos2026";
  return "Basic " + Buffer.from(`${u}:${p}`).toString("base64");
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: getAuthHeader(),
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`API ${r.status}: ${text}`);
  }
  return r.json();
}

export interface DashboardStats {
  wa_status: string;
  api_status: string;
  total_leads: number;
  agendados: number;
  qualificando: number;
  handoff: number;
  novos_24h: number;
  upcoming_consultas: { titulo: string; inicio: string; criado_pelo_bot: boolean }[];
  leads_por_dia: { date: string; count: number }[];
  por_operadora: { name: string; value: number }[];
  funil: { etapa: string; count: number }[];
  por_modalidade: { name: string; value: number }[];
  por_cenario: { name: string; value: number }[];
  multimodal: { audios: number; imagens: number };
}

export interface ConversationSummary {
  phone: string;
  name: string;
  name_full: string;
  email: string;
  valor_atual: string;
  operadora: string;
  tipo_plano: string;
  stage: string;
  confirmed_slot_str: string;
  lead_status: string;
  last_message_at: string;
  ai_summary: string;
  cenario: string;
  last_followup_day: number;
}

export interface ConversationDetail {
  phone: string;
  profile: Record<string, any>;
  history: { role: string; content: string; ts?: string }[];
  stage: string;
  slot_str: string;
  cenario: string;
}

export interface AgendaEvent {
  id: string;
  titulo: string;
  descricao: string;
  inicio: string;
  fim: string;
  all_day: boolean;
  criado_pelo_bot: boolean;
  html_link: string;
}

export interface KnowledgeFile {
  name: string;
  size: number;
  modified: string;
}

export interface LogBlock {
  label: string;
  path: string;
  content: string;
}

export interface LlmInfo {
  primary?: string;
  fallback?: string;
  openai_model?: string;
  openai_model_fallback?: string;
  openrouter_model?: string;
  openai_configured?: boolean;
  openrouter_configured?: boolean;
  calendar_id?: string;
  lawyer_email?: string;
  meeting_duration_min?: number;
  scheduling_slots_count?: number;
  error?: string;
}

export const CENARIO_LABEL: Record<string, string> = {
  falso_coletivo: "Falso Coletivo",
  multifamiliar: "Multifamiliar",
  coletivo_adesao: "Coletivo Adesão",
  individual: "Individual/Familiar",
  inviavel: "Inviável",
  indefinido: "Indefinido",
};

export const CENARIO_COLOR: Record<string, string> = {
  falso_coletivo: "success",
  multifamiliar: "info",
  coletivo_adesao: "warning",
  individual: "secondary",
  inviavel: "danger",
  indefinido: "secondary",
};

export const api = {
  dashboardStats: () => call<DashboardStats>("/api/admin/dashboard"),
  conversations: () => call<ConversationSummary[]>("/api/admin/conversations"),
  conversation: (phone: string) => call<ConversationDetail>(`/api/admin/conversations/${encodeURIComponent(phone)}`),
  agenda: (days = 30) => call<AgendaEvent[]>(`/api/admin/agenda?days=${days}`),
  knowledgeList: () => call<KnowledgeFile[]>("/api/admin/knowledge"),
  knowledgeGet: (file: string) => call<{ content: string }>(`/api/admin/knowledge/${encodeURIComponent(file)}`),
  knowledgeSave: (file: string, content: string) =>
    call(`/api/admin/knowledge/${encodeURIComponent(file)}`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  logs: () => call<LogBlock[]>("/api/admin/logs"),
  llmInfo: () => call<LlmInfo>("/api/admin/llm-info"),
  health: () => call<{ status: string }>("/health"),
};
