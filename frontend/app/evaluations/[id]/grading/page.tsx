'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

interface GradingResult {
  id: string
  submission_id: string
  criterion_scores: any
  suggested_total: number
  confidence: number
  teacher_final_score: number | null
  status: string
  override_reason: string | null
}

export default function GradingPage() {
  const params = useParams()
  const id = params.id as string
  const [results, setResults] = useState<GradingResult[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [grading, setGrading] = useState(false)
  const router = useRouter()

  const fetchGrading = async () => {
    try {
      const res = await fetch(`/api/evaluations/${id}/grading-results`)
      if (res.status === 401) {
        router.push('/login')
        return
      }
      if (res.ok) {
        const data = await res.json()
        setResults(data.grading_results || [])
        setStats(data.batch_statistics || null)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) fetchGrading()
  }, [id])

  const handleStartGrading = async () => {
    setGrading(true)
    try {
      await fetch(`/api/evaluations/${id}/grade`, { method: 'POST' })
      setTimeout(() => {
        fetchGrading()
        setGrading(false)
      }, 2000)
    } catch (err) {
      console.error(err)
      setGrading(false)
    }
  }

  const handleFinalize = async (submissionId: string) => {
    try {
      await fetch(`/api/evaluations/submissions/${submissionId}/finalize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm_finalization: true }),
      })
      fetchGrading()
    } catch (err) {
      console.error(err)
    }
  }

  const handleExportCSV = () => {
    window.open(`/api/evaluations/${id}/reports/csv`, '_blank')
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center space-x-4">
          <Link href={`/evaluations/${id}`} className="text-sm font-medium text-indigo-600 hover:underline">
            ← Back to Evaluation
          </Link>
          <span className="text-slate-300">|</span>
          <h1 className="text-lg font-bold text-slate-900">AI Grading & Teacher Review</h1>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleExportCSV}
            className="px-4 py-2 bg-white border border-slate-300 text-slate-700 font-medium rounded-lg text-sm shadow-sm hover:bg-slate-50"
          >
            📥 Export CSV Gradebook
          </button>
          <button
            onClick={handleStartGrading}
            disabled={grading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-sm shadow-sm disabled:opacity-50"
          >
            {grading ? 'Calculating Grades...' : '✨ Run AI Grading'}
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-8 py-8 space-y-8">
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold uppercase text-slate-400">Total Graded</span>
              <p className="text-3xl font-bold text-slate-900 mt-1">{stats.count}</p>
            </div>
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold uppercase text-slate-400">Mean Score</span>
              <p className="text-3xl font-bold text-indigo-600 mt-1">{stats.mean_score}</p>
            </div>
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold uppercase text-slate-400">Median Score</span>
              <p className="text-3xl font-bold text-slate-900 mt-1">{stats.median_score}</p>
            </div>
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold uppercase text-slate-400">Flagged Submissions</span>
              <p className="text-3xl font-bold text-amber-600 mt-1">{stats.flagged_count}</p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Grading Results & Teacher Review</h3>
          {loading ? (
            <p className="text-slate-500">Loading grading results...</p>
          ) : results.length === 0 ? (
            <p className="text-slate-500">No grading results computed yet. Click &quot;Run AI Grading&quot; above.</p>
          ) : (
            <div className="space-y-4">
              {results.map((r) => (
                <div key={r.id} className="p-5 rounded-xl border border-slate-200 bg-white shadow-sm flex justify-between items-center">
                  <div>
                    <div className="flex items-center space-x-3 mb-1">
                      <span className="font-bold text-slate-900 text-lg">
                        {r.teacher_final_score !== null ? r.teacher_final_score : r.suggested_total}
                      </span>
                      <span className="text-sm text-slate-500">Suggested: {r.suggested_total}</span>
                      <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${
                        r.status === 'finalized' ? 'bg-green-50 text-green-700' : 'bg-indigo-50 text-indigo-700'
                      }`}>
                        {r.status}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600">{r.criterion_scores?.feedback || 'Grading complete.'}</p>
                  </div>
                  <div>
                    {r.status !== 'finalized' && (
                      <button
                        onClick={() => handleFinalize(r.submission_id)}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm"
                      >
                        Finalize Grade
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
