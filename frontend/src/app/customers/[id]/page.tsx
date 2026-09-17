"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { AppLayout } from "@/components/AppLayout"
import { StatusBadge, PriorityBadge } from "@/components/StatusBadges"
import { api, Customer, Conversation, Followup } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import {
  User,
  Mail,
  Phone,
  MessageSquare,
  Clock,
  ArrowLeft,
  Save,
  CheckCircle,
  Plus,
} from "lucide-react"

export default function CustomerDetailPage() {
  const params = useParams()
  const customerId = params.id as string
  const router = useRouter()

  const [customer, setCustomer] = useState<Customer | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [followups, setFollowups] = useState<Followup[]>([])
  const [loading, setLoading] = useState(true)

  // Edit fields
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [status, setStatus] = useState("NEW")
  const [notes, setNotes] = useState("")
  const [saving, setSaving] = useState(false)
  const [savedSuccess, setSavedSuccess] = useState(false)

  const loadCustomerData = async () => {
    try {
      const [cust, convs, fols] = await Promise.all([
        api.getCustomer(customerId),
        api.listConversations({ search: customerId }),
        api.listFollowups(),
      ])
      setCustomer(cust)
      setName(cust.name)
      setEmail(cust.email || "")
      setPhone(cust.phone || "")
      setStatus(cust.status)
      setNotes(cust.notes || "")
      setConversations(convs.items.filter((c) => c.customer_id === customerId))
      setFollowups(fols.items.filter((f) => f.customer_id === customerId))
    } catch (err) {
      console.error("Failed loading customer details:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (customerId) {
      loadCustomerData()
    }
  }, [customerId])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      const updated = await api.updateCustomer(customerId, {
        name,
        email: email || undefined,
        phone: phone || undefined,
        status,
        notes: notes || undefined,
      })
      setCustomer(updated)
      setSavedSuccess(true)
      setTimeout(() => setSavedSuccess(false), 3000)
    } catch (err: any) {
      alert(err.message || "Failed saving customer profile")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <AppLayout title="Customer Profile">
        <div className="flex items-center justify-center py-20 text-slate-500">
          Loading customer record...
        </div>
      </AppLayout>
    )
  }

  if (!customer) {
    return (
      <AppLayout title="Customer Profile">
        <div className="text-center py-20">
          <p className="text-slate-400 mb-4">Customer not found</p>
          <Link href="/customers" className="text-indigo-400 hover:underline text-xs font-semibold">
            Back to Customer Directory
          </Link>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout title={`Customer Profile: ${customer.name}`}>
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <Link
            href="/customers"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Directory</span>
          </Link>
          <StatusBadge status={customer.status} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Edit Form */}
          <div className="lg:col-span-1 bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <User className="w-4 h-4 text-indigo-400" />
              <span>Contact Information</span>
            </h3>

            {savedSuccess && (
              <div className="mb-4 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                <span>Profile updated successfully</span>
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Email</label>
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
                <label className="block text-xs font-semibold text-slate-300 mb-1">Lifecycle Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                >
                  <option value="NEW">New</option>
                  <option value="ACTIVE">Active</option>
                  <option value="FOLLOW_UP">Follow Up</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="INACTIVE">Inactive</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Operational Notes</label>
                <textarea
                  rows={4}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? "Saving..." : "Save Changes"}</span>
              </button>
            </form>
          </div>

          {/* Activity & Conversations & Followups */}
          <div className="lg:col-span-2 space-y-6">
            {/* Conversation History */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-indigo-400" />
                <span>Conversations History ({conversations.length})</span>
              </h3>

              <div className="space-y-3">
                {conversations.map((conv) => (
                  <Link
                    key={conv.id}
                    href={`/conversations/${conv.id}`}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-indigo-500/30 flex items-center justify-between transition-colors block"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <StatusBadge status={conv.status} />
                        <PriorityBadge priority={conv.priority} />
                        <span className="text-[11px] text-slate-500">{formatDate(conv.updated_at)}</span>
                      </div>
                      <p className="text-xs text-slate-300 line-clamp-1">{conv.last_message?.content || "Conversation thread"}</p>
                    </div>
                  </Link>
                ))}
                {conversations.length === 0 && (
                  <p className="text-xs text-slate-500 text-center py-6">No conversations recorded for this customer.</p>
                )}
              </div>
            </div>

            {/* Followups */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-400" />
                <span>Follow-up Tasks ({followups.length})</span>
              </h3>

              <div className="space-y-3">
                {followups.map((f) => (
                  <div key={f.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-xs font-semibold text-slate-200">{f.title}</p>
                      <p className="text-[11px] text-slate-400">Due: {formatDate(f.due_at)}</p>
                    </div>
                    <StatusBadge status={f.status} />
                  </div>
                ))}
                {followups.length === 0 && (
                  <p className="text-xs text-slate-500 text-center py-6">No active follow-ups for this customer.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
