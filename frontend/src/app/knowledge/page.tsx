"use client"

import React, { useEffect, useState, useRef } from "react"
import { AppLayout } from "@/components/AppLayout"
import { StatusBadge } from "@/components/StatusBadges"
import { api, KnowledgeDocument, KnowledgeChunk } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import {
  BookOpen,
  UploadCloud,
  FileText,
  Trash2,
  Search,
  Eye,
  Sparkles,
  Layers,
  AlertCircle,
} from "lucide-react"

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // Chunk Modal
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDocument | null>(null)
  const [chunks, setChunks] = useState<KnowledgeChunk[]>([])
  const [loadingChunks, setLoadingChunks] = useState(false)

  // Vector Search Test
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const loadDocuments = async () => {
    try {
      const data = await api.listDocuments()
      setDocuments(data)
    } catch (err) {
      console.error("Failed loading knowledge documents:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setUploadError(null)
    try {
      await api.uploadDocument(file)
      await loadDocuments()
      if (fileInputRef.current) fileInputRef.current.value = ""
    } catch (err: any) {
      setUploadError(err.message || "Failed uploading and processing document")
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Delete knowledge document "${filename}" and its vector chunks?`)) return
    try {
      await api.deleteDocument(docId)
      loadDocuments()
      if (selectedDoc?.id === docId) setSelectedDoc(null)
    } catch (err: any) {
      alert(err.message || "Failed deleting document")
    }
  }

  const handleViewChunks = async (doc: KnowledgeDocument) => {
    setSelectedDoc(doc)
    setLoadingChunks(true)
    try {
      const chunkList = await api.getDocumentChunks(doc.id)
      setChunks(chunkList)
    } catch (err) {
      console.error("Failed loading chunks:", err)
    } finally {
      setLoadingChunks(false)
    }
  }

  const handleTestSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const results = await api.searchKnowledge(searchQuery.trim())
      setSearchResults(results)
    } catch (err: any) {
      alert(err.message || "Search failed")
    } finally {
      setSearching(false)
    }
  }

  return (
    <AppLayout title="Knowledge Base & RAG Index">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Upload Drop Area */}
        <div className="bg-slate-900/60 border-2 border-dashed border-slate-800 hover:border-indigo-500/40 rounded-2xl p-8 text-center transition-colors">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".md,.txt,.pdf,.json,.csv"
            className="hidden"
            id="kb-upload"
          />
          <div className="max-w-md mx-auto space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Upload Grounded Business Knowledge</h3>
              <p className="text-xs text-slate-400 mt-1">
                Supports PDF, Markdown (.md), and plain text documents. Text is automatically cleaned, chunked, and vectorized into pgvector.
              </p>
            </div>
            <label
              htmlFor="kb-upload"
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold cursor-pointer transition-colors shadow-lg shadow-indigo-600/20 ${
                uploading ? "opacity-50 pointer-events-none" : ""
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>{uploading ? "Ingesting & Vectorizing..." : "Select Document"}</span>
            </label>
            {uploadError && (
              <p className="text-xs text-rose-400 mt-2 font-medium flex items-center justify-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>{uploadError}</span>
              </p>
            )}
          </div>
        </div>

        {/* 2 Column: Document List & Semantic Vector Search Sandbox */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Document List */}
          <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-indigo-400" />
                <span>Indexed Documents ({documents.length})</span>
              </h3>
            </div>

            <div className="divide-y divide-slate-800/60">
              {documents.map((doc) => (
                <div key={doc.id} className="py-4 flex items-center justify-between gap-4">
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-bold text-slate-200 truncate">{doc.filename}</p>
                      <StatusBadge status={doc.status} />
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-slate-400">
                      <span>{doc.chunk_count} vector chunks</span>
                      <span>•</span>
                      <span>Uploaded {formatDate(doc.created_at)}</span>
                    </div>
                    {doc.error_message && (
                      <p className="text-[10px] text-rose-400">{doc.error_message}</p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleViewChunks(doc)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors flex items-center gap-1.5"
                    >
                      <Layers className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Inspect Chunks</span>
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id, doc.filename)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/60 hover:text-rose-400 text-slate-400 transition-colors"
                      title="Delete Document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
              {documents.length === 0 && !loading && (
                <div className="text-center py-12 text-xs text-slate-500">
                  No knowledge documents uploaded yet.
                </div>
              )}
            </div>
          </div>

          {/* Semantic Vector Search Sandbox */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <span>RAG Retrieval Sandbox</span>
              </h3>
              <p className="text-[11px] text-slate-400 mt-1">
                Test cosine similarity search across your tenant&apos;s vectorized knowledge chunks.
              </p>
            </div>

            <form onSubmit={handleTestSearch} className="space-y-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g. 'What is the refund policy?'"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={searching || !searchQuery.trim()}
                className="w-full py-2 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
              >
                <Search className="w-3.5 h-3.5" />
                <span>{searching ? "Searching..." : "Test Vector Search"}</span>
              </button>
            </form>

            <div className="space-y-2.5 max-h-96 overflow-y-auto pt-2">
              {searchResults.map((res, i) => (
                <div key={i} className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-semibold text-indigo-400 truncate">{res.filename}</span>
                    <span className="font-bold text-emerald-400">
                      {Math.round(res.similarity_score * 100)}% Sim
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 line-clamp-3 leading-relaxed">{res.content}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Chunks Inspector Modal */}
        {selectedDoc && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-base font-bold text-white">Chunks Inspector: {selectedDoc.filename}</h3>
                  <p className="text-xs text-slate-400">{chunks.length} total vectorized chunks</p>
                </div>
                <button
                  onClick={() => setSelectedDoc(null)}
                  className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Close
                </button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {chunks.map((c) => (
                  <div key={c.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase font-semibold">
                      <span>Chunk #{c.chunk_index}</span>
                      <span>Index: {c.chunk_index}</span>
                    </div>
                    <p className="text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">{c.content}</p>
                  </div>
                ))}
                {loadingChunks && (
                  <div className="text-center py-12 text-xs text-slate-500">Loading vector chunks...</div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
