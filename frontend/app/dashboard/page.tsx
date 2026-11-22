'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface Evaluation {
  id: string
  title: string
  max_marks: number
  status: string
  created_at: string
}

export default function DashboardPage() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [title, setTitle] = useState('')
  const [maxMarks, setMaxMarks] = useState(100)
  const [creating, setCreating] = useState(false)
  const router = useRouter()

  const fetchEvaluations = async () => {
    try {
      const res = await fetch('/api/evaluations')
      if (res.status === 401) {
        router.push('/login')
        return
      }
      if (res.ok) {
        const data = await res.json()
        setEvaluations(data.evaluations || [])
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvaluations()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    try {
      const res = await fetch('/api/evaluations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, max_marks: Number(maxMarks) }),
      })
      if (res.ok) {
        setTitle('')
        setMaxMarks(100)
        setShowCreateModal(false)
        fetchEvaluations()
      }
    } catch (err) {
      console.error(err)
    } finally {
      setCreating(false)
    }
  }

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center space-x-3">
          <h1 className="text-xl font-bold text-indigo-600 tracking-tight">PLAGIX</h1>
          <span className="text-slate-300">|</span>
          <span className="text-sm font-medium text-slate-700">Teacher Dashboard</span>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm font-medium text-slate-600 hover:text-red-600 transition-colors"
        >
          Sign Out
        </button>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Evaluations</h2>
            <p className="text-sm text-slate-500 mt-1">Manage exam batches, rubrics, and submission analysis.</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-sm transition-colors"
          >
            + New Evaluation
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500">Loading evaluations...</div>
        ) : evaluations.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
            <p className="text-slate-600 mb-4">No evaluations created yet.</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg"
            >
              Create your first evaluation
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {evaluations.map((ev) => (
              <Link
                key={ev.id}
                href={`/evaluations/${ev.id}`}
                className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:border-indigo-500 hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider px-2 py-1 bg-indigo-50 text-indigo-700 rounded-md">
                      {ev.status}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(ev.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 mb-1">{ev.title}</h3>
                </div>
                <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center text-sm text-slate-600">
                  <span>Max Marks: {ev.max_marks}</span>
                  <span className="text-indigo-600 font-medium hover:underline">View Details →</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Create New Evaluation</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Evaluation Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900"
                  placeholder="Midterm Exam - Fall 2026"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Maximum Marks</label>
                <input
                  type="number"
                  required
                  min={1}
                  value={maxMarks}
                  onChange={(e) => setMaxMarks(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Evaluation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
