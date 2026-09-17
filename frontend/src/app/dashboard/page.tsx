"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { AppLayout } from "@/components/AppLayout"
import { StatusBadge, PriorityBadge } from "@/components/StatusBadges"
import { api, AnalyticsOverview, Conversation, Followup } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import {
  Users,
  MessageSquare,
  Sparkles,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Bot,
} from "lucide-react"

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [followups, setFollowups] = useState<Followup[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [anData, convData, folData] = await Promise.all([
          api.getAnalyticsOverview(),
          api.listConversations({ page: 1 }),
          api.listFollowups({ status: "PENDING" }),
        ])
        setAnalytics(anData)
        setConversations(convData.items)
        setFollowups(folData.items)
      } catch (err) {
        console.error("Failed loading dashboard data:", err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  return (
    <AppLayout title="Operational Dashboard">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Banner */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950/60 via-slate-900/80 to-slate-900 border border-indigo-500/20 p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <Sparkles className="w-4 h-4" />
              <span>AI Customer Operations Engine</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Demo Learning Center Operations Workspace
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Real-time grounded knowledge retrieval, multi-tenant isolation, automated intent classification, and controlled follow-up management.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/conversations"
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-indigo-600/25"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Open Inbox</span>
            </Link>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Total Customers</span>
              <Users className="w-4 h-4 text-blue-400" />
            </div>
            <p className="text-2xl font-bold text-white">{analytics?.total_customers ?? "--"}</p>
            <span className="text-[11px] text-slate-500 mt-1 block">Active Profiles</span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Open Threads</span>
              <MessageSquare className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-bold text-emerald-400">{analytics?.open_conversations ?? "--"}</p>
            <span className="text-[11px] text-slate-500 mt-1 block">Requiring attention</span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">AI Resolution Rate</span>
              <Sparkles className="w-4 h-4 text-indigo-400" />
            </div>
            <p className="text-2xl font-bold text-indigo-400">{analytics?.ai_resolution_rate ?? 0}%</p>
            <span className="text-[11px] text-slate-500 mt-1 block">Grounded RAG Answers</span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Human Escalations</span>
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            </div>
            <p className="text-2xl font-bold text-rose-400">{analytics?.human_escalations ?? "--"}</p>
            <span className="text-[11px] text-slate-500 mt-1 block">Flagged for staff review</span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Pending Follow-ups</span>
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-bold text-amber-400">{analytics?.pending_followups ?? "--"}</p>
              {analytics?.overdue_followups ? (
                <span className="text-xs font-bold text-rose-400">({analytics.overdue_followups} overdue)</span>
              ) : null}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Scheduled tasks</span>
          </div>
        </div>

        {/* 2 Column Layout: Recent Conversations + Pending Follow-ups */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Conversations */}
          <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-indigo-400" />
                <span>Recent Customer Conversations</span>
              </h3>
              <Link
                href="/conversations"
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
              >
                <span>View all</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-slate-800/60">
              {conversations.slice(0, 5).map((conv) => (
                <Link
                  key={conv.id}
                  href={`/conversations/${conv.id}`}
                  className="py-3.5 flex items-center justify-between hover:bg-slate-800/30 px-3 rounded-lg transition-colors group"
                >
                  <div className="space-y-1 min-w-0 pr-4">
                    <div className="flex items-center gap-2.5">
                      <p className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors truncate">
                        {conv.customer?.name || "Customer"}
                      </p>
                      <StatusBadge status={conv.status} />
                      <PriorityBadge priority={conv.priority} />
                    </div>
                    <p className="text-xs text-slate-400 truncate">
                      {conv.last_message?.content || "No messages yet"}
                    </p>
                  </div>
                  <div className="text-right text-[11px] text-slate-500 whitespace-nowrap">
                    {formatDate(conv.updated_at)}
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Pending Follow-ups */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-400" />
                <span>Active Follow-ups</span>
              </h3>
              <Link
                href="/followups"
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
              >
                <span>View all</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {followups.slice(0, 4).map((f) => (
                <div
                  key={f.id}
                  className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 space-y-1.5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-semibold text-slate-200 truncate">{f.title}</p>
                    {f.is_overdue && (
                      <span className="text-[10px] uppercase font-bold text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
                        Overdue
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 truncate">Customer: {f.customer?.name || "Client"}</p>
                  <p className="text-[10px] text-slate-500">Due: {formatDate(f.due_at)}</p>
                </div>
              ))}
              {followups.length === 0 && (
                <p className="text-xs text-slate-500 text-center py-6">No pending follow-ups</p>
              )}
            </div>
          </div>
        </div>

        {/* Intent Distribution & Operational Intelligence */}
        {analytics?.intent_distribution && analytics.intent_distribution.length > 0 && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              <span>Customer Intent Intelligence</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              {analytics.intent_distribution.map((item) => (
                <div key={item.intent} className="p-3.5 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-[11px] text-slate-400 uppercase font-semibold">
                    {item.intent.replace(/_/g, " ")}
                  </span>
                  <div className="flex items-baseline justify-between mt-1">
                    <p className="text-lg font-bold text-slate-100">{item.count}</p>
                    <span className="text-xs text-indigo-400 font-semibold">{item.percentage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
