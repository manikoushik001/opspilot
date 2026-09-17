"use client"

import React, { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { Sidebar } from "@/components/Sidebar"
import { Header } from "@/components/Header"

export function AppLayout({ children, title }: { children: React.ReactNode; title: string }) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!loading && !user && pathname !== "/login" && pathname !== "/register") {
      router.push("/login")
    }
  }, [user, loading, pathname, router])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-medium text-slate-400">Loading OpsPilot workspace...</p>
        </div>
      </div>
    )
  }

  if (!user && pathname !== "/login" && pathname !== "/register") {
    return null
  }

  return (
    <div className="min-h-screen bg-[#0b0f17] text-slate-100 flex">
      <Sidebar />
      <div className="flex-1 flex flex-col pl-64 min-w-0">
        <Header title={title} />
        <main className="flex-1 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  )
}
