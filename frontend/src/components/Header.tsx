"use client"

import React from "react"
import { useAuth } from "@/context/AuthContext"
import { LogOut, User as UserIcon, Bell, Sparkles } from "lucide-react"

export function Header({ title }: { title: string }) {
  const { user, logout } = useAuth()

  return (
    <header className="h-16 bg-slate-950/80 backdrop-blur border-b border-slate-800 flex items-center justify-between px-8 sticky top-0 z-20">
      <div>
        <h1 className="text-lg font-semibold text-white tracking-tight">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-400">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span>RAG Active (pgvector)</span>
        </div>

        {/* User Badge */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <UserIcon className="w-4 h-4" />
          </div>
          <div className="text-left hidden sm:block">
            <p className="text-xs font-semibold text-slate-200">{user?.full_name || "Admin"}</p>
            <p className="text-[10px] text-slate-400">{user?.email || "owner@demolearning.com"}</p>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-900 transition-colors ml-2"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  )
}
