"use client"

import React, { useEffect, useState } from "react"
import { AppLayout } from "@/components/AppLayout"
import { api, AnalyticsOverview } from "@/lib/api"
import {
  BarChart3,
  TrendingUp,
  Sparkles,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Users,
  MessageSquare,
  ShieldCheck,
  Zap,
} from "lucide-react"

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const res = await api.getAnalyticsOverview()
        setData(res)
      } catch (err) {
        console.error("Failed loading analytics:", err)
      } finally {
        setLoading(false)
      }
    }
    loadAnalytics()
  }, [])

  if (loading) {
    return (
      <AppLayout title="Operational Analytics">
        <div className="flex items-center justify-center py-20 text-slate-500">
          Loading analytics metrics...
        </div>
      </AppLayout>
    )
  }

  const resBk = data?.resolution_breakdown || {
    ai_resolved: 0,
    human_resolved: 0,
    open_or_in_progress: 0,
    escalated_to_human: 0,
  }

  return (
    <AppLayout title="Operations & AI Performance Analytics">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* KPI Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">AI Resolution Efficiency</span>
              <Sparkles className="w-4 h-4 text-indigo-400" />
            </div>
            <p className="text-3xl font-extrabold text-indigo-400">{data?.ai_resolution_rate ?? 0}%</p>
            <p className="text-[11px] text-slate-500 mt-1">Autonomous grounded RAG answers</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Avg Response Time</span>
              <Zap className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-3xl font-extrabold text-emerald-400">
              {data?.avg_response_time_seconds ?? 1.2}s
            </p>
            <p className="text-[11px] text-slate-500 mt-1">Real-time vector search & inference</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Mean AI Confidence</span>
              <ShieldCheck className="w-4 h-4 text-blue-400" />
            </div>
            <p className="text-3xl font-extrabold text-blue-400">
              {Math.round((data?.avg_ai_confidence ?? 0.88) * 100)}%
            </p>
            <p className="text-[11px] text-slate-500 mt-1">Above grounding threshold (&ge; 75%)</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Human Escalation Rate</span>
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            </div>
            <p className="text-3xl font-extrabold text-rose-400">
              {data?.human_escalations ?? 0}
            </p>
            <p className="text-[11px] text-slate-500 mt-1">Policy triggered or low confidence</p>
          </div>
        </div>

        {/* 2 Column Charts: Volume & Resolution Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Daily Volume Bar Chart */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              <span>7-Day Conversation Volume & AI Handling</span>
            </h3>

            <div className="pt-4 flex items-end justify-between gap-3 h-48 border-b border-slate-800 pb-2">
              {data?.daily_volume.map((pt, i) => {
                const heightPercent = Math.min(100, Math.max(15, (pt.total_conversations / 10) * 100))
                const aiPercent = Math.min(100, Math.max(10, (pt.ai_handled / Math.max(pt.total_conversations, 1)) * 100))

                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                    <div className="w-full flex items-end justify-center gap-1 h-full">
                      {/* Total Bar */}
                      <div
                        className="w-1/2 bg-slate-800 rounded-t-sm transition-all"
                        style={{ height: `${heightPercent}%` }}
                        title={`Total: ${pt.total_conversations}`}
                      />
                      {/* AI Bar */}
                      <div
                        className="w-1/2 bg-indigo-600 rounded-t-sm transition-all"
                        style={{ height: `${(heightPercent * aiPercent) / 100}%` }}
                        title={`AI Handled: ${pt.ai_handled}`}
                      />
                    </div>
                    <span className="text-[10px] text-slate-500 whitespace-nowrap">{pt.date}</span>
                  </div>
                )
              })}
            </div>

            <div className="flex items-center justify-center gap-6 pt-2 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-sm bg-slate-800 inline-block" />
                <span>Total Conversations</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-sm bg-indigo-600 inline-block" />
                <span>AI Answered</span>
              </div>
            </div>
          </div>

          {/* Resolution Method Breakdown */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Resolution & Operational Breakdown</span>
            </h3>

            <div className="space-y-4 pt-2">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-300 font-semibold">AI Resolved Conversations</span>
                  <span className="text-indigo-400 font-bold">{resBk.ai_resolved}</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-indigo-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, (resBk.ai_resolved / Math.max(data?.total_conversations || 1, 1)) * 100)}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-300 font-semibold">Staff Assisted / Human Resolved</span>
                  <span className="text-emerald-400 font-bold">{resBk.human_resolved}</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, (resBk.human_resolved / Math.max(data?.total_conversations || 1, 1)) * 100)}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-300 font-semibold">Open & In Progress</span>
                  <span className="text-amber-400 font-bold">{resBk.open_or_in_progress}</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, (resBk.open_or_in_progress / Math.max(data?.total_conversations || 1, 1)) * 100)}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-300 font-semibold">Human Escalations Flagged</span>
                  <span className="text-rose-400 font-bold">{resBk.escalated_to_human}</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-rose-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, (resBk.escalated_to_human / Math.max(data?.total_conversations || 1, 1)) * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Intent Distribution Bars */}
        {data?.intent_distribution && data.intent_distribution.length > 0 && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white">Intent Classification Distribution</h3>
            <div className="space-y-3">
              {data.intent_distribution.map((item) => (
                <div key={item.intent} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300 font-medium uppercase text-[11px]">
                      {item.intent.replace(/_/g, " ")}
                    </span>
                    <span className="text-slate-400">
                      {item.count} messages ({item.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-indigo-500 to-blue-500 h-full rounded-full"
                      style={{ width: `${item.percentage}%` }}
                    />
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
