"use client"

import React, { createContext, useContext, useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { api, User } from "@/lib/api"

interface AuthContextType {
  user: User | null
  loading: boolean
  currentBusinessId: string | null
  setCurrentBusinessId: (id: string) => void
  login: (tokens: { access_token: string; refresh_token: string }) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentBusinessId, setCurrentBusinessIdState] = useState<string | null>(null)
  const router = useRouter()
  const pathname = usePathname()

  const setCurrentBusinessId = (id: string) => {
    setCurrentBusinessIdState(id)
    if (typeof window !== "undefined") {
      localStorage.setItem("opspilot_biz_id", id)
    }
  }

  const refreshUser = async () => {
    try {
      const u = await api.getMe()
      setUser(u)
      if (u.memberships && u.memberships.length > 0) {
        const storedBiz = localStorage.getItem("opspilot_biz_id")
        const exists = u.memberships.some(m => m.business_id === storedBiz)
        if (!storedBiz || !exists) {
          setCurrentBusinessId(u.memberships[0].business_id)
        } else {
          setCurrentBusinessIdState(storedBiz)
        }
      }
    } catch {
      setUser(null)
      localStorage.removeItem("opspilot_token")
      localStorage.removeItem("opspilot_biz_id")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const token = localStorage.getItem("opspilot_token")
    if (token) {
      refreshUser()
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (tokens: { access_token: string; refresh_token: string }) => {
    localStorage.setItem("opspilot_token", tokens.access_token)
    await refreshUser()
    router.push("/dashboard")
  }

  const logout = () => {
    localStorage.removeItem("opspilot_token")
    localStorage.removeItem("opspilot_biz_id")
    setUser(null)
    router.push("/login")
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        currentBusinessId,
        setCurrentBusinessId,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
