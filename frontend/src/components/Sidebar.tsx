"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  MessageSquare,
  Users,
  BookOpen,
  CalendarCheck,
  BarChart3,
  Settings,
  ShieldCheck,
  Bot,
  Sparkles,
} from "lucide-react"

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuth()

  const navItems = [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Conversations", href: "/conversations", icon: MessageSquare },
    { label: "Customers", href: "/customers", icon: Users },
    { label: "Knowledge Base", href: "/knowledge", icon: BookOpen },
    { label: "Follow-ups", href: "/followups", icon: CalendarCheck },
    { label: "Analytics", href: "/analytics", icon: BarChart3 },
    { label: "Settings", href: "/settings", icon: Settings },
  ]

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-30">
      {/* Brand */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
            OpsPilot
            <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              SaaS
            </span>
          </span>
          <p className="text-[11px] text-slate-400">Customer Operations</p>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          Workspace
        </div>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href))
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              )}
            >
              <Icon className={cn("w-4 h-4", isActive ? "text-indigo-400" : "text-slate-400")} />
              {item.label}
            </Link>
          )
        })}
      </div>

      {/* Tenant Indicator */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/40">
        <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Tenant Isolated Mode</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
          <p className="text-slate-400 text-[11px]">Active Business:</p>
          <p className="font-semibold text-slate-200 truncate">
            {user?.memberships?.[0]?.business_name || "Demo Learning Center"}
          </p>
          <span className="text-[10px] text-emerald-400 font-medium">
            Role: {user?.memberships?.[0]?.role || "OWNER"}
          </span>
        </div>
      </div>
    </aside>
  )
}
