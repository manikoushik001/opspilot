"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { AppLayout } from "@/components/AppLayout"
import { StatusBadge } from "@/components/StatusBadges"
import { api, Followup, Customer } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import {
  CalendarCheck,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Plus,
  User,
  XCircle,
} from "lucide-react"

export default function FollowupsPage() {
  const [followups, setFollowups] = useState<Followup[]>([])
  const [activeTab, setActiveTab] = useState<"ALL" | "PENDING" | "OVERDUE" | "COMPLETED">("PENDING")
  const [counts, setCounts] = useState({ pending: 0, overdue: 0, completed: 0, total: 0 })
  const [loading, setLoading] = useState(true)

  // Create Modal
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [customers, setCustomers] = useState<Customer[]>([])
  const [selectedCustId, setSelectedCustId] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [dueDays, setDueDays] = useState(1)
  const [creating, setCreating] = useState(false)

  const loadFollowups = async () => {
    setLoading(true)
    try {
      let statusParam: string | undefined = undefined
      let overdueParam: boolean = false

      if (activeTab === "PENDING") statusParam = "PENDING"
      if (activeTab === "COMPLETED") statusParam = "COMPLETED"
      if (activeTab === "OVERDUE") {
        statusParam = "PENDING"
        overdueParam = true
      }

      const res = await api.listFollowups({
        status: statusParam,
        overdue: overdueParam,
      })

      setFollowups(res.items)
      setCounts({
        pending: res.pending_count,
        overdue: res.overdue_count,
        completed: res.completed_count,
        total: res.total,
      })
    } catch (err) {
      console.error("Failed loading followups:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFollowups()
  }, [activeTab])

  const openCreateModal = async () => {
    setIsModalOpen(true)
    try {
      const custData = await api.listCustomers({ limit: 50 })
      setCustomers(custData.items)
      if (custData.items.length > 0) {
        setSelectedCustId(custData.items[0].id)
      }
    } catch (err) {
      console.error("Failed fetching customers:", err)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCustId || !title.trim()) return
    setCreating(true)
    try {
      const dueAt = new Date(Date.now() + dueDays * 24 * 60 * 60 * 1000).toISOString()
      await api.createFollowup({
        customer_id: selectedCustId,
        title: title.trim(),
        description: description.trim() || undefined,
        due_at: dueAt,
      })
      setIsModalOpen(false)
      setTitle("")
      setDescription("")
      loadFollowups()
    } catch (err: any) {
      alert(err.message || "Failed creating follow-up")
    } finally {
      setCreating(false)
    }
  }

  const handleMarkComplete = async (id: string) => {
    try {
      await api.updateFollowup(id, { status: "COMPLETED" })
      loadFollowups()
    } catch (err: any) {
      alert(err.message || "Failed updating status")
    }
  }

  const handleCancel = async (id: string) => {
    try {
      await api.updateFollowup(id, { status: "CANCELLED" })
      loadFollowups()
    } catch (err: any) {
      alert(err.message || "Failed cancelling task")
    }
  }

  return (
    <AppLayout title="Follow-up Management">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header and Tabs */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("PENDING")}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === "PENDING"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>Pending ({counts.pending})</span>
            </button>
            <button
              onClick={() => setActiveTab("OVERDUE")}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === "OVERDUE"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              <span>Overdue ({counts.overdue})</span>
            </button>
            <button
              onClick={() => setActiveTab("COMPLETED")}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === "COMPLETED"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Completed ({counts.completed})</span>
            </button>
          </div>

          <button
            onClick={openCreateModal}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-indigo-600/20"
          >
            <Plus className="w-4 h-4" />
            <span>Create Follow-up</span>
          </button>
        </div>

        {/* Task List */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl divide-y divide-slate-800/60 shadow-xl overflow-hidden">
          {followups.map((f) => (
            <div key={f.id} className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-800/20 transition-colors">
              <div className="space-y-1.5 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-xs font-bold text-slate-100">{f.title}</h4>
                  <StatusBadge status={f.status} />
                  {f.is_overdue && (
                    <span className="text-[10px] uppercase font-bold text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
                      Overdue
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3 text-[11px] text-slate-400">
                  <span className="text-indigo-400 font-semibold">
                    Customer: {f.customer?.name || "Client"}
                  </span>
                  <span>•</span>
                  <span>Due: {formatDate(f.due_at)}</span>
                  {f.completed_at && (
                    <>
                      <span>•</span>
                      <span className="text-emerald-400">Completed: {formatDate(f.completed_at)}</span>
                    </>
                  )}
                </div>

                {f.description && (
                  <p className="text-xs text-slate-400 pt-0.5 leading-relaxed">{f.description}</p>
                )}
              </div>

              {/* Action Buttons */}
              {f.status === "PENDING" && (
                <div className="flex items-center gap-2 self-end sm:self-center">
                  <button
                    onClick={() => handleMarkComplete(f.id)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Complete</span>
                  </button>
                  <button
                    onClick={() => handleCancel(f.id)}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/40 hover:text-rose-400 text-slate-400 transition-colors"
                    title="Cancel Task"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          ))}
          {followups.length === 0 && !loading && (
            <div className="p-12 text-center text-xs text-slate-500">
              No follow-ups in this category.
            </div>
          )}
        </div>

        {/* Create Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
              <h3 className="text-base font-bold text-white">Create Follow-up Task</h3>
              <form onSubmit={handleCreate} className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Select Customer *</label>
                  <select
                    value={selectedCustId}
                    onChange={(e) => setSelectedCustId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.email || c.phone || "No contact"})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Task Title *</label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Call regarding weekend cohort registration"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Due In (Days)</label>
                  <input
                    type="number"
                    min={0}
                    max={30}
                    value={dueDays}
                    onChange={(e) => setDueDays(parseInt(e.target.value) || 1)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Description</label>
                  <textarea
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Action notes or special instructions..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creating}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50"
                  >
                    {creating ? "Creating..." : "Create Task"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
