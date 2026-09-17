const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  created_at: string
  memberships: {
    business_id: string
    business_name?: string
    role: "OWNER" | "STAFF"
  }[]
}

export interface Business {
  id: string
  name: string
  description?: string
  industry?: string
  email?: string
  phone?: string
  timezone: string
}

export interface Customer {
  id: string
  business_id: string
  name: string
  email?: string
  phone?: string
  status: "NEW" | "ACTIVE" | "FOLLOW_UP" | "RESOLVED" | "INACTIVE"
  notes?: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  conversation_id: string
  sender_type: "CUSTOMER" | "STAFF" | "AI"
  sender_id?: string
  content: string
  intent?: string
  ai_confidence?: number
  created_at: string
}

export interface Conversation {
  id: string
  business_id: string
  customer_id: string
  status: "OPEN" | "WAITING" | "HUMAN_REVIEW" | "RESOLVED" | "CLOSED"
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT"
  assigned_to?: string
  resolved_at?: string
  created_at: string
  updated_at: string
  customer?: Customer
  last_message?: Message
  messages?: Message[]
}

export interface KnowledgeDocument {
  id: string
  business_id: string
  filename: string
  mime_type: string
  status: "UPLOADED" | "PROCESSING" | "READY" | "FAILED"
  chunk_count: number
  error_message?: string
  created_at: string
}

export interface KnowledgeChunk {
  id: string
  document_id: string
  chunk_index: number
  content: string
  metadata_dict: Record<string, any>
  created_at: string
}

export interface Followup {
  id: string
  business_id: string
  customer_id: string
  conversation_id?: string
  assigned_to?: string
  title: string
  description?: string
  due_at: string
  status: "PENDING" | "COMPLETED" | "CANCELLED"
  completed_at?: string
  is_overdue: boolean
  customer?: Customer
}

export interface AnalyticsOverview {
  total_customers: number
  total_conversations: number
  open_conversations: number
  resolved_conversations: number
  human_escalations: number
  pending_followups: number
  overdue_followups: number
  ai_resolution_rate: number
  avg_response_time_seconds: number
  avg_ai_confidence: number
  intent_distribution: { intent: string; count: number; percentage: number }[]
  daily_volume: { date: string; total_conversations: number; ai_handled: number; human_escalated: number }[]
  resolution_breakdown: {
    ai_resolved: number
    human_resolved: number
    open_or_in_progress: number
    escalated_to_human: number
  }
}

export interface AuditLog {
  id: string
  business_id: string
  user_id?: string
  action: string
  resource_type: string
  resource_id?: string
  metadata_dict: Record<string, any>
  created_at: string
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("opspilot_token") : null
  const businessId = typeof window !== "undefined" ? localStorage.getItem("opspilot_biz_id") : null

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  if (businessId) {
    headers["X-Business-ID"] = businessId
  }

  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    let errMsg = "An error occurred"
    try {
      const errData = await res.json()
      errMsg = errData.detail || errData.message || errMsg
    } catch {
      errMsg = res.statusText
    }
    throw new Error(errMsg)
  }

  if (res.status === 204) {
    return {} as T
  }

  return res.json()
}

export const api = {
  // Auth
  register: (data: any) => request<User>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data: any) => request<{ access_token: string; refresh_token: string }>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(data) }),
  getMe: () => request<User>("/api/v1/auth/me"),

  // Business
  getBusiness: () => request<Business>("/api/v1/business"),
  updateBusiness: (data: any) => request<Business>("/api/v1/business", { method: "PATCH", body: JSON.stringify(data) }),

  // Customers
  listCustomers: (params: { search?: string; status?: string; page?: number; limit?: number } = {}) => {
    const query = new URLSearchParams()
    if (params.search) query.append("search", params.search)
    if (params.status) query.append("status", params.status)
    if (params.page) query.append("page", params.page.toString())
    if (params.limit) query.append("limit", params.limit.toString())
    return request<{ items: Customer[]; total: number; page: number; pages: number }>(`/api/v1/customers?${query}`)
  },
  getCustomer: (id: string) => request<Customer>(`/api/v1/customers/${id}`),
  createCustomer: (data: any) => request<Customer>("/api/v1/customers", { method: "POST", body: JSON.stringify(data) }),
  updateCustomer: (id: string, data: any) => request<Customer>(`/api/v1/customers/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteCustomer: (id: string) => request<void>(`/api/v1/customers/${id}`, { method: "DELETE" }),

  // Conversations
  listConversations: (params: { status?: string; priority?: string; search?: string; page?: number } = {}) => {
    const query = new URLSearchParams()
    if (params.status) query.append("status", params.status)
    if (params.priority) query.append("priority", params.priority)
    if (params.search) query.append("search", params.search)
    if (params.page) query.append("page", params.page.toString())
    return request<{ items: Conversation[]; total: number; page: number; pages: number }>(`/api/v1/conversations?${query}`)
  },
  getConversation: (id: string) => request<Conversation>(`/api/v1/conversations/${id}`),
  createConversation: (data: any) => request<Conversation>("/api/v1/conversations", { method: "POST", body: JSON.stringify(data) }),
  updateConversation: (id: string, data: any) => request<Conversation>(`/api/v1/conversations/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  sendStaffMessage: (convId: string, content: string) =>
    request<Message>(`/api/v1/conversations/${convId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, sender_type: "STAFF" }),
    }),
  simulateCustomerMessage: (convId: string, content: string) =>
    request<{ customer_message: Message; ai_response: Message; decision_metadata: any }>(
      `/api/v1/conversations/${convId}/simulate-customer`,
      {
        method: "POST",
        body: JSON.stringify({ content }),
      }
    ),

  // Knowledge Base
  listDocuments: () => request<KnowledgeDocument[]>("/api/v1/knowledge/documents"),
  getDocumentChunks: (docId: string) => request<KnowledgeChunk[]>(`/api/v1/knowledge/documents/${docId}/chunks`),
  uploadDocument: async (file: File) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("opspilot_token") : null
    const businessId = typeof window !== "undefined" ? localStorage.getItem("opspilot_biz_id") : null
    const formData = new FormData()
    formData.append("file", file)

    const headers: Record<string, string> = {}
    if (token) headers["Authorization"] = `Bearer ${token}`
    if (businessId) headers["X-Business-ID"] = businessId

    const res = await fetch(`${API_BASE_URL}/api/v1/knowledge/documents`, {
      method: "POST",
      headers,
      body: formData,
    })
    if (!res.ok) throw new Error("Document upload failed")
    return res.json()
  },
  deleteDocument: (docId: string) => request<void>(`/api/v1/knowledge/documents/${docId}`, { method: "DELETE" }),
  searchKnowledge: (query: string) =>
    request<any[]>("/api/v1/knowledge/search", { method: "POST", body: JSON.stringify({ query }) }),

  // Follow-ups
  listFollowups: (params: { status?: string; overdue?: boolean } = {}) => {
    const query = new URLSearchParams()
    if (params.status) query.append("status", params.status)
    if (params.overdue) query.append("overdue", "true")
    return request<{ items: Followup[]; total: number; pending_count: number; overdue_count: number; completed_count: number }>(`/api/v1/followups?${query}`)
  },
  createFollowup: (data: any) => request<Followup>("/api/v1/followups", { method: "POST", body: JSON.stringify(data) }),
  updateFollowup: (id: string, data: any) => request<Followup>(`/api/v1/followups/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // AI Actions
  executeAIAction: (data: any) => request<any>("/api/v1/ai/execute-action", { method: "POST", body: JSON.stringify(data) }),

  // Analytics
  getAnalyticsOverview: () => request<AnalyticsOverview>("/api/v1/analytics/overview"),

  // Audit Logs
  listAuditLogs: (page: number = 1) => request<{ items: AuditLog[]; total: number }>(`/api/v1/audit-logs?page=${page}`),
}
