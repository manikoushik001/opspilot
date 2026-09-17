"use client"

import React, { useEffect, useState, useRef } from "react"
import { AppLayout } from "@/components/AppLayout"
import { StatusBadge, PriorityBadge, IntentBadge } from "@/components/StatusBadges"
import { api, Conversation, Message, Customer } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import {
  MessageSquare,
  Search,
  Send,
  Sparkles,
  AlertTriangle,
  User,
  Phone,
  Mail,
  Calendar,
  CheckCircle,
  Clock,
  ShieldCheck,
  Bot,
  Plus,
  FileText,
} from "lucide-react"

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null)
  const [activeConv, setActiveConv] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [lastDecisionMeta, setLastDecisionMeta] = useState<any | null>(null)

  // Inputs
  const [staffReplyText, setStaffReplyText] = useState("")
  const [simulatedCustomerText, setSimulatedCustomerText] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [sendingStaff, setSendingStaff] = useState(false)
  const [simulatingAI, setSimulatingAI] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const loadConversations = async () => {
    try {
      const data = await api.listConversations({
        search: searchQuery || undefined,
        status: statusFilter || undefined,
      })
      setConversations(data.items)
      if (!selectedConvId && data.items.length > 0) {
        setSelectedConvId(data.items[0].id)
      }
    } catch (err) {
      console.error("Failed loading conversations:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadConversations()
  }, [searchQuery, statusFilter])

  const loadConversationDetail = async (convId: string) => {
    try {
      const conv = await api.getConversation(convId)
      setActiveConv(conv)
      setMessages(conv.messages || [])
    } catch (err) {
      console.error("Failed loading conversation detail:", err)
    }
  }

  useEffect(() => {
    if (selectedConvId) {
      loadConversationDetail(selectedConvId)
    }
  }, [selectedConvId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendStaffReply = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!staffReplyText.trim() || !selectedConvId) return
    setSendingStaff(true)
    try {
      const newMsg = await api.sendStaffMessage(selectedConvId, staffReplyText.trim())
      setMessages((prev) => [...prev, newMsg])
      setStaffReplyText("")
      loadConversations()
    } catch (err: any) {
      alert(err.message || "Failed to send message")
    } finally {
      setSendingStaff(false)
    }
  }

  const handleSimulateCustomer = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!simulatedCustomerText.trim() || !selectedConvId) return
    setSimulatingAI(true)
    try {
      const res = await api.simulateCustomerMessage(selectedConvId, simulatedCustomerText.trim())
      setMessages((prev) => [...prev, res.customer_message, res.ai_response])
      setLastDecisionMeta(res.decision_metadata)
      setSimulatedCustomerText("")
      loadConversationDetail(selectedConvId)
      loadConversations()
    } catch (err: any) {
      alert(err.message || "Failed running AI simulation")
    } finally {
      setSimulatingAI(false)
    }
  }

  const handleExecuteAction = async (actionType: string, payload: any) => {
    if (!selectedConvId || !activeConv) return
    try {
      const res = await api.executeAIAction({
        action_type: actionType,
        conversation_id: selectedConvId,
        customer_id: activeConv.customer_id,
        payload,
      })
      alert(`Action Executed: ${res.result}`)
      loadConversationDetail(selectedConvId)
      loadConversations()
    } catch (err: any) {
      alert(err.message || "Action execution failed")
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!selectedConvId) return
    try {
      await api.updateConversation(selectedConvId, { status: newStatus })
      loadConversationDetail(selectedConvId)
      loadConversations()
    } catch (err: any) {
      alert(err.message || "Status update failed")
    }
  }

  return (
    <AppLayout title="Conversations Inbox">
      <div className="h-[calc(100vh-8.5rem)] flex bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        {/* ================= COLUMN 1: Conversation List ================= */}
        <div className="w-80 border-r border-slate-800 flex flex-col bg-slate-950/50">
          {/* Search & Filters */}
          <div className="p-4 border-b border-slate-800 space-y-3">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
            <div className="flex gap-1.5 overflow-x-auto pb-1 text-[11px]">
              {["", "OPEN", "HUMAN_REVIEW", "RESOLVED"].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2 py-1 rounded-md font-medium whitespace-nowrap transition-colors ${
                    statusFilter === st
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-900 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {st === "" ? "All" : st.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
            {conversations.map((conv) => {
              const isSelected = conv.id === selectedConvId
              return (
                <div
                  key={conv.id}
                  onClick={() => setSelectedConvId(conv.id)}
                  className={`p-3.5 cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-indigo-950/40 border-l-2 border-indigo-500"
                      : "hover:bg-slate-900/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs font-semibold text-slate-200 truncate">
                      {conv.customer?.name || "Customer"}
                    </p>
                    <span className="text-[10px] text-slate-500 whitespace-nowrap">
                      {formatDate(conv.updated_at)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-1 mb-2">
                    {conv.last_message?.content || "No messages"}
                  </p>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={conv.status} />
                    <PriorityBadge priority={conv.priority} />
                  </div>
                </div>
              )
            })}
            {conversations.length === 0 && (
              <div className="p-8 text-center text-xs text-slate-500">No conversations found</div>
            )}
          </div>
        </div>

        {/* ================= COLUMN 2: Message Stream ================= */}
        <div className="flex-1 flex flex-col bg-slate-950/20 border-r border-slate-800 min-w-0">
          {/* Thread Header */}
          {activeConv ? (
            <div className="h-14 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-semibold text-xs">
                  {activeConv.customer?.name?.charAt(0) || "C"}
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-slate-200">{activeConv.customer?.name}</h3>
                  <p className="text-[10px] text-slate-400">{activeConv.customer?.email || "No email"}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={activeConv.status} />
                {activeConv.status === "HUMAN_REVIEW" && (
                  <span className="text-[10px] text-rose-400 font-medium px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    Human Review Flagged
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="h-14 border-b border-slate-800 flex items-center px-6 text-xs text-slate-500">
              Select a conversation to view messages
            </div>
          )}

          {/* Messages Stream */}
          <div className="flex-1 p-6 overflow-y-auto space-y-4">
            {messages.map((msg) => {
              const isCust = msg.sender_type === "CUSTOMER"
              const isAI = msg.sender_type === "AI"
              const isStaff = msg.sender_type === "STAFF"

              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isCust ? "items-start" : "items-end"}`}
                >
                  <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] text-slate-500">
                    {isCust && <span className="font-semibold text-slate-300">Customer</span>}
                    {isStaff && <span className="font-semibold text-indigo-400">Staff Agent</span>}
                    {isAI && (
                      <span className="font-semibold text-emerald-400 flex items-center gap-1">
                        <Sparkles className="w-3 h-3" />
                        OpsPilot AI (Grounded)
                      </span>
                    )}
                    <span>•</span>
                    <span>{formatDate(msg.created_at)}</span>
                  </div>

                  <div
                    className={`max-w-xl p-3.5 rounded-2xl text-xs leading-relaxed ${
                      isCust
                        ? "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-sm"
                        : isAI
                        ? "bg-indigo-950/40 border border-indigo-500/30 text-indigo-100 rounded-tr-sm shadow-lg shadow-indigo-950/50"
                        : "bg-indigo-600 text-white rounded-tr-sm shadow-md"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>

                    {/* Safe Decision Metadata Badge */}
                    {isAI && msg.intent && (
                      <div className="mt-2.5 pt-2 border-t border-indigo-500/20 flex flex-wrap items-center gap-2 text-[10px] text-indigo-300/80">
                        <span className="font-medium text-indigo-400">Intent: {msg.intent}</span>
                        {msg.ai_confidence && (
                          <span>• Conf: {Math.round(msg.ai_confidence * 100)}%</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Action Boxes */}
          {activeConv && (
            <div className="p-4 border-t border-slate-800 bg-slate-900/60 space-y-3">
              {/* Staff Response Box */}
              <form onSubmit={handleSendStaffReply} className="flex gap-2">
                <input
                  type="text"
                  value={staffReplyText}
                  onChange={(e) => setStaffReplyText(e.target.value)}
                  placeholder="Type staff response..."
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
                <button
                  type="submit"
                  disabled={sendingStaff || !staffReplyText.trim()}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Reply</span>
                </button>
              </form>

              {/* Simulated Customer Message Box */}
              <form
                onSubmit={handleSimulateCustomer}
                className="flex items-center gap-2 p-2 rounded-lg bg-indigo-950/20 border border-indigo-500/20"
              >
                <div className="flex items-center gap-1.5 text-indigo-400 text-[11px] font-semibold whitespace-nowrap pl-1">
                  <Bot className="w-3.5 h-3.5" />
                  <span>Simulate Customer:</span>
                </div>
                <input
                  type="text"
                  value={simulatedCustomerText}
                  onChange={(e) => setSimulatedCustomerText(e.target.value)}
                  placeholder="e.g. 'What is the fee for the weekend Java course?'"
                  className="flex-1 bg-slate-950 border border-slate-800/80 rounded-md px-2.5 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
                <button
                  type="submit"
                  disabled={simulatingAI || !simulatedCustomerText.trim()}
                  className="px-3 py-1.5 rounded-md bg-indigo-600/80 hover:bg-indigo-600 text-white text-[11px] font-semibold transition-colors flex items-center gap-1 disabled:opacity-50"
                >
                  {simulatingAI ? "Processing RAG..." : "Send & Run AI"}
                </button>
              </form>
            </div>
          )}
        </div>

        {/* ================= COLUMN 3: Customer & AI Inspector ================= */}
        <div className="w-80 flex flex-col bg-slate-950/60 overflow-y-auto p-5 space-y-6">
          {activeConv ? (
            <>
              {/* Customer Profile */}
              <div>
                <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3">
                  Customer Profile
                </h4>
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2.5">
                  <p className="text-sm font-bold text-white">{activeConv.customer?.name}</p>
                  <div className="space-y-1.5 text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-slate-500" />
                      <span className="truncate">{activeConv.customer?.email || "No email"}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Phone className="w-3.5 h-3.5 text-slate-500" />
                      <span>{activeConv.customer?.phone || "No phone"}</span>
                    </div>
                  </div>
                  {activeConv.customer?.notes && (
                    <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400">
                      <span className="font-semibold text-slate-300 block mb-0.5">Notes:</span>
                      {activeConv.customer.notes}
                    </div>
                  )}
                </div>
              </div>

              {/* Status Controls */}
              <div>
                <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Conversation Controls
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleStatusChange("RESOLVED")}
                    className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold hover:bg-emerald-500/20 transition-colors flex items-center justify-center gap-1.5"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Resolve</span>
                  </button>
                  <button
                    onClick={() => handleStatusChange("HUMAN_REVIEW")}
                    className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold hover:bg-rose-500/20 transition-colors flex items-center justify-center gap-1.5"
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Escalate</span>
                  </button>
                </div>
              </div>

              {/* AI Decision Inspector */}
              <div>
                <h4 className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Decision Inspector</span>
                </h4>
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                  {lastDecisionMeta ? (
                    <>
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase block font-medium">Classified Intent:</span>
                        <span className="text-xs font-semibold text-indigo-400">
                          {lastDecisionMeta.intent}
                        </span>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-400 uppercase block font-medium">
                          Confidence Score: {Math.round(lastDecisionMeta.confidence * 100)}%
                        </span>
                        <div className="w-full bg-slate-950 rounded-full h-1.5 mt-1 overflow-hidden">
                          <div
                            className="bg-indigo-500 h-full rounded-full transition-all"
                            style={{ width: `${Math.round(lastDecisionMeta.confidence * 100)}%` }}
                          />
                        </div>
                      </div>

                      {lastDecisionMeta.is_escalated && (
                        <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[11px]">
                          <span className="font-semibold block">Escalation Triggered:</span>
                          {lastDecisionMeta.escalation_reason || "Low confidence / policy requirement"}
                        </div>
                      )}

                      {/* Grounded Sources */}
                      {lastDecisionMeta.sources && lastDecisionMeta.sources.length > 0 && (
                        <div>
                          <span className="text-[10px] text-slate-400 uppercase block font-medium mb-1">
                            Retrieved Sources ({lastDecisionMeta.sources.length}):
                          </span>
                          <div className="space-y-1.5">
                            {lastDecisionMeta.sources.map((src: any, idx: number) => (
                              <div
                                key={idx}
                                className="p-2 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300"
                              >
                                <span className="font-semibold text-indigo-400 block truncate">
                                  📄 {src.filename} (Score: {Math.round(src.similarity_score * 100)}%)
                                </span>
                                <p className="text-slate-400 text-[10px] line-clamp-2 mt-0.5">
                                  {src.content}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* AI Proposed Action */}
                      {lastDecisionMeta.suggested_action && lastDecisionMeta.suggested_action !== "NONE" && (
                        <div className="pt-2 border-t border-slate-800">
                          <span className="text-[10px] text-amber-400 font-semibold uppercase block mb-1.5">
                            AI Proposed Action:
                          </span>
                          <p className="text-xs text-slate-200 mb-2">
                            {lastDecisionMeta.suggested_action}
                          </p>
                          <button
                            onClick={() =>
                              handleExecuteAction(
                                lastDecisionMeta.suggested_action,
                                lastDecisionMeta.action_payload
                              )
                            }
                            className="w-full py-1.5 px-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 hover:bg-amber-500/20 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Validate & Execute Action</span>
                          </button>
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-slate-500">
                      Send a message or test simulation to inspect AI retrieval and grounding decision steps.
                    </p>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="text-xs text-slate-500 text-center py-12">
              No conversation selected
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
