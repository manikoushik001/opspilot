"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useAuth } from "@/context/AuthContext"
import { api } from "@/lib/api"
import { Bot, Lock, Mail, ArrowRight, ShieldCheck, Sparkles } from "lucide-react"

export default function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const tokens = await api.login({ email, password })
      await login(tokens)
    } catch (err: any) {
      setError(err.message || "Invalid email or password.")
    } finally {
      setLoading(false)
    }
  }

  const fillDemoCreds = (type: "owner" | "staff") => {
    if (type === "owner") {
      setEmail("owner@demolearning.com")
      setPassword("password123")
    } else {
      setEmail("staff@demolearning.com")
      setPassword("password123")
    }
  }

  return (
    <div className="min-h-screen bg-[#0b0f17] flex flex-col justify-center items-center px-4 relative overflow-hidden">
      {/* Subtle Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-indigo-500/10 blur-[100px] rounded-full pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-600 text-white shadow-xl shadow-indigo-500/25 mb-4">
            <Bot className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Sign in to OpsPilot</h1>
          <p className="text-sm text-slate-400 mt-1">AI-powered customer operations for small businesses</p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 backdrop-blur-xl shadow-2xl">
          {error && (
            <div className="mb-6 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Business Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@business.com"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-6 border-t border-slate-800">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 text-center">
              Quick Demo Logins (Demo Data)
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => fillDemoCreds("owner")}
                className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-indigo-500/40 text-[11px] text-slate-300 text-left transition-colors"
              >
                <span className="font-semibold block text-indigo-400">Owner Demo</span>
                <span className="text-[10px] text-slate-500">owner@demolearning.com</span>
              </button>
              <button
                type="button"
                onClick={() => fillDemoCreds("staff")}
                className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-indigo-500/40 text-[11px] text-slate-300 text-left transition-colors"
              >
                <span className="font-semibold block text-indigo-400">Staff Demo</span>
                <span className="text-[10px] text-slate-500">staff@demolearning.com</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-500 mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-medium">
            Register your business
          </Link>
        </p>
      </div>
    </div>
  )
}
