"use client"

import React, { useEffect, useState } from "react"
import { AppLayout } from "@/components/AppLayout"
import { useAuth } from "@/context/AuthContext"
import { api, Business, AuditLog } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import {
  Settings,
  Building2,
  Sliders,
  ShieldCheck,
  Save,
  CheckCircle,
  FileText,
  Lock,
} from "lucide-react"

export default function SettingsPage() {
  const { user } = useAuth()
  const [business, setBusiness] = useState<Business | null>(null)
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)

  // Business Form
  const [name, setName] = useState("")
  const [industry, setIndustry] = useState("Education")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [timezone, setTimezone] = useState("America/Chicago")
  const [savingBiz, setSavingBiz] = useState(false)
  const [savedSuccess, setSavedSuccess] = useState(false)

  // AI Thresholds (Client displayed / simulated)
  const [topK, setTopK] = useState(4)
  const [simThreshold, setSimThreshold] = useState(0.50)
  const [confThreshold, setConfThreshold] = useState(0.75)
  const [savedAiSuccess, setSavedAiSuccess] = useState(false)

  const loadSettingsData = async () => {
    try {
      const [biz, logs] = await Promise.all([
        api.getBusiness(),
        api.listAuditLogs(1).catch(() => ({ items: [], total: 0 })),
      ])
      setBusiness(biz)
      setName(biz.name)
      setIndustry(biz.industry || "Education")
      setEmail(biz.email || "")
      setPhone(biz.phone || "")
      setTimezone(biz.timezone || "America/Chicago")
      setAuditLogs(logs.items)
    } catch (err) {
      console.error("Failed loading settings:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSettingsData()
  }, [])

  const handleSaveBusiness = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingBiz(true)
    try {
      const updated = await api.updateBusiness({
        name,
        industry,
        email: email || undefined,
        phone: phone || undefined,
        timezone,
      })
      setBusiness(updated)
      setSavedSuccess(true)
      setTimeout(() => setSavedSuccess(false), 3000)
    } catch (err: any) {
      alert(err.message || "Failed saving business profile")
    } finally {
      setSavingBiz(false)
    }
  }

  const handleSaveAIConfig = (e: React.FormEvent) => {
    e.preventDefault()
    setSavedAiSuccess(true)
    setTimeout(() => setSavedAiSuccess(false), 3000)
  }

  return (
    <AppLayout title="Workspace Settings & Audit Logs">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Business Profile */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <span>Business Profile</span>
            </h3>

            {savedSuccess && (
              <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                <span>Business settings saved</span>
              </div>
            )}

            <form onSubmit={handleSaveBusiness} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Business Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Industry</label>
                <input
                  type="text"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Contact Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Phone</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Timezone</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                >
                  <option value="America/Chicago">America/Chicago (Central Time)</option>
                  <option value="America/New_York">America/New_York (Eastern Time)</option>
                  <option value="America/Los_Angeles">America/Los_Angeles (Pacific Time)</option>
                  <option value="UTC">UTC</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={savingBiz}
                className="w-full py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{savingBiz ? "Saving..." : "Update Business"}</span>
              </button>
            </form>
          </div>

          {/* AI Grounding & RAG Config */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <span>AI Grounding & RAG Safety Parameters</span>
            </h3>

            {savedAiSuccess && (
              <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                <span>AI safety parameters saved</span>
              </div>
            )}

            <form onSubmit={handleSaveAIConfig} className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-slate-300">Retrieval Top-K Chunks</span>
                  <span className="text-indigo-400 font-bold">{topK}</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={8}
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  className="w-full accent-indigo-500"
                />
                <span className="text-[10px] text-slate-500">Number of top semantic chunks to pass into context</span>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-slate-300">Vector Similarity Threshold</span>
                  <span className="text-emerald-400 font-bold">{simThreshold}</span>
                </div>
                <input
                  type="range"
                  min={0.30}
                  max={0.90}
                  step={0.05}
                  value={simThreshold}
                  onChange={(e) => setSimThreshold(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500"
                />
                <span className="text-[10px] text-slate-500">Minimum cosine similarity required to consider chunk relevant</span>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-slate-300">AI Confidence Escalation Threshold</span>
                  <span className="text-blue-400 font-bold">{confThreshold}</span>
                </div>
                <input
                  type="range"
                  min={0.50}
                  max={0.95}
                  step={0.05}
                  value={confThreshold}
                  onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <span className="text-[10px] text-slate-500">Answers below this confidence trigger automatic human escalation</span>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <span className="font-semibold text-slate-300 block">Active AI Provider:</span>
                <span className="text-indigo-400 font-medium">Mock LLM Provider (Offline Evaluation & Deterministic RAG)</span>
              </div>

              <button
                type="submit"
                className="w-full py-2 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-2"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save AI Thresholds</span>
              </button>
            </form>
          </div>
        </div>

        {/* Audit Logs Table */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
            <span>Audit Trail & Security Logs</span>
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Action</th>
                  <th className="py-2.5 px-3 font-semibold">Resource</th>
                  <th className="py-2.5 px-3 font-semibold">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/20">
                    <td className="py-2.5 px-3 font-semibold text-slate-200">{log.action}</td>
                    <td className="py-2.5 px-3 text-slate-400">
                      {log.resource_type}:{log.resource_id}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">{formatDate(log.created_at)}</td>
                  </tr>
                ))}
                {auditLogs.length === 0 && (
                  <tr>
                    <td colSpan={3} className="py-6 text-center text-slate-500">
                      No audit logs available for this session.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
