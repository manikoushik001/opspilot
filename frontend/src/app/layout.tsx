import type { Metadata } from "next"
import "./globals.css"
import { AuthProvider } from "@/context/AuthContext"

export const metadata: Metadata = {
  title: "OpsPilot - AI-Powered Customer Operations SaaS",
  description: "Multi-tenant AI-powered customer operations platform for small businesses with grounded RAG, follow-up workflows, and strict tenant isolation.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b0f17] text-slate-100 antialiased min-h-screen">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
