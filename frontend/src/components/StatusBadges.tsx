import React from "react"
import { cn } from "@/lib/utils"

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text?: string; label?: string }> = {
    // Customer
    NEW: { bg: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
    ACTIVE: { bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    FOLLOW_UP: { bg: "bg-amber-500/10 text-amber-400 border-amber-500/20", label: "Follow Up" },
    RESOLVED: { bg: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
    INACTIVE: { bg: "bg-rose-500/10 text-rose-400 border-rose-500/20" },

    // Conversation
    OPEN: { bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    WAITING: { bg: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
    HUMAN_REVIEW: { bg: "bg-rose-500/15 text-rose-400 border-rose-500/30", label: "Human Review" },
    CLOSED: { bg: "bg-slate-500/10 text-slate-400 border-slate-500/20" },

    // Followup
    PENDING: { bg: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
    COMPLETED: { bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    CANCELLED: { bg: "bg-slate-500/10 text-slate-400 border-slate-500/20" },

    // Knowledge Doc
    UPLOADED: { bg: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
    PROCESSING: { bg: "bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse" },
    READY: { bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    FAILED: { bg: "bg-rose-500/10 text-rose-400 border-rose-500/20" },
  }

  const conf = map[status] || { bg: "bg-slate-800 text-slate-300 border-slate-700" }
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border", conf.bg)}>
      {conf.label || status}
    </span>
  )
}

export function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, string> = {
    LOW: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    MEDIUM: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    HIGH: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    URGENT: "bg-rose-500/15 text-rose-400 border-rose-500/30 font-semibold",
  }
  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border", map[priority] || "bg-slate-800 text-slate-400")}>
      {priority}
    </span>
  )
}

export function IntentBadge({ intent }: { intent?: string }) {
  if (!intent) return null
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
      {intent.replace(/_/g, " ")}
    </span>
  )
}
