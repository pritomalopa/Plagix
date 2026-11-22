'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

interface RelevanceResult {
  id: string
  submission_id: string
  category: string
  score: number
  confidence: number
  rationale: string
  evidence: any
}

interface Comparison {
  id: string
  submission_a_id: string
  submission_b_id: string
  exact_score: number
  lexical_score: number
  semantic_score: number
  status: string
}

export default function AnalysisPage() {
  const params = useParams()
  const id = params.id as string
  const [relevanceResults, setRelevanceResults] = useState<RelevanceResult[]>([])
  const [comparisons, setComparisons] = useState<Comparison[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const router = useRouter()

  const fetchAnalysis = async () => {
    try {
      const relRes = await fetch(`/api/evaluations/${id}/relevance`)
      if (relRes.ok) {
        const data = await relRes.json()
        setRelevanceResults(data.relevance_results || [])
      }

      const compRes = await fetch(`/api/evaluations/${id}/comparisons`)
      if (compRes.ok) {
        const data = await compRes.json()
        setComparisons(data.comparisons || [])
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) fetchAnalysis()
  }, [id])

  const handleStartAnalysis = async () => {
    setAnalyzing(true)
    try {
      await fetch(`/api/evaluations/${id}/relevance`, { method: 'POST' })
      await fetch(`/api/evaluations/${id}/compare`, { method: 'POST' })
      setTimeout(() => {
        fetchAnalysis()
        setAnalyzing(false)
      }, 2000)
    } catch (err) {
      console.error(err)
      setAnalyzing(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center space-x-4">
          <Link href={`/evaluations/${id}`} className="text-sm font-medium text-indigo-600 hover:underline">
            ← Back to Evaluation
          </Link>
          <span className="text-slate-300">|</span>
          <h1 className="text-lg font-bold text-slate-900">Relevance & Similarity Analysis</h1>
        </div>
        <button
          onClick={handleStartAnalysis}
          disabled={analyzing}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-sm shadow-sm disabled:opacity-50"
        >
          {analyzing ? 'Running Analysis...' : '🚀 Run Analysis Engine'}
        </button>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-8 py-8 space-y-8">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Answer Relevance Results</h3>
          {loading ? (
            <p className="text-slate-500">Loading relevance results...</p>
          ) : relevanceResults.length === 0 ? (
            <p className="text-slate-500">No relevance analysis run yet. Click &quot;Run Analysis Engine&quot; above.</p>
          ) : (
            <div className="space-y-4">
              {relevanceResults.map((rel) => (
                <div key={rel.id} className="p-4 rounded-lg border border-slate-200 bg-slate-50 flex justify-between items-center">
                  <div>
                    <span className="text-xs font-semibold uppercase px-2 py-1 bg-indigo-100 text-indigo-700 rounded-md">
                      {rel.category}
                    </span>
                    <p className="text-sm text-slate-700 mt-2">{rel.rationale}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-bold text-slate-900">{(rel.score * 100).toFixed(1)}%</span>
                    <span className="block text-xs text-slate-400">Alignment Score</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Pairwise Similarity Comparisons</h3>
          {loading ? (
            <p className="text-slate-500">Loading comparisons...</p>
          ) : comparisons.length === 0 ? (
            <p className="text-slate-500">No comparisons computed yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                    <th className="py-3 px-4">Exact Score</th>
                    <th className="py-3 px-4">Lexical Score</th>
                    <th className="py-3 px-4">Semantic Score</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {comparisons.map((comp) => (
                    <tr key={comp.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-medium text-slate-900">
                        {comp.exact_score !== null ? `${(comp.exact_score * 100).toFixed(1)}%` : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {comp.lexical_score !== null ? `${(comp.lexical_score * 100).toFixed(1)}%` : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {comp.semantic_score !== null ? `${(comp.semantic_score * 100).toFixed(1)}%` : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 bg-green-50 text-green-700 rounded-md text-xs font-semibold">
                          {comp.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
