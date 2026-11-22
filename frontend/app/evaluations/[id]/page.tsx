'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

interface RubricCriterion {
  id: string
  criterion: string
  description: string
  max_points: number
  weight: number
  expected_evidence: string
  order: number
}

interface Question {
  id: string
  order: number
  prompt: string
  reference_answer: string
  rubric_criteria: RubricCriterion[]
}

interface EvaluationDetail {
  id: string
  title: string
  max_marks: number
  status: string
  questions: Question[]
}

export default function EvaluationDetailPage() {
  const params = useParams()
  const id = params.id as string
  const [evaluation, setEvaluation] = useState<EvaluationDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [showQuestionModal, setShowQuestionModal] = useState(false)
  const [prompt, setPrompt] = useState('')
  const [refAnswer, setRefAnswer] = useState('')
  const router = useRouter()

  const fetchDetail = async () => {
    try {
      const res = await fetch(`/api/evaluations/${id}`)
      if (res.status === 401) {
        router.push('/login')
        return
      }
      if (res.ok) {
        const data = await res.json()
        setEvaluation(data)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) fetchDetail()
  }, [id])

  const handleAddQuestion = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!evaluation) return
    try {
      const nextOrder = (evaluation.questions?.length || 0) + 1
      const res = await fetch(`/api/evaluations/${id}/questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order: nextOrder,
          prompt,
          reference_answer: refAnswer,
          expected_concepts: {},
        }),
      })
      if (res.ok) {
        setPrompt('')
        setRefAnswer('')
        setShowQuestionModal(false)
        fetchDetail()
      }
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-slate-500">Loading evaluation...</div>
  }

  if (!evaluation) {
    return <div className="min-h-screen flex items-center justify-center text-slate-500">Evaluation not found.</div>
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center space-x-4">
          <Link href="/dashboard" className="text-sm font-medium text-indigo-600 hover:underline">
            ← Back to Dashboard
          </Link>
          <span className="text-slate-300">|</span>
          <h1 className="text-lg font-bold text-slate-900">{evaluation.title}</h1>
        </div>
        <div className="flex space-x-3">
          <Link
            href={`/evaluations/${id}/upload`}
            className="px-4 py-2 bg-white border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-slate-50 text-sm shadow-sm"
          >
            📂 Upload Submissions
          </Link>
          <Link
            href={`/evaluations/${id}/analysis`}
            className="px-4 py-2 bg-indigo-50 text-indigo-700 font-medium rounded-lg hover:bg-indigo-100 text-sm"
          >
            📊 Analysis & Similarity
          </Link>
          <Link
            href={`/evaluations/${id}/grading`}
            className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 text-sm shadow-sm"
          >
            ✨ AI Grading & Review
          </Link>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Questions & Rubric Criteria</h2>
            <p className="text-sm text-slate-500 mt-1">Configure evaluation questions, reference answers, and grading rubrics.</p>
          </div>
          <button
            onClick={() => setShowQuestionModal(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-sm"
          >
            + Add Question
          </button>
        </div>

        {evaluation.questions.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
            <p className="text-slate-600 mb-4">No questions added to this evaluation yet.</p>
            <button
              onClick={() => setShowQuestionModal(true)}
              className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg"
            >
              Add First Question
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {evaluation.questions.map((q) => (
              <div key={q.id} className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-bold text-slate-900">Question {q.order}</h3>
                </div>
                <p className="text-slate-800 font-medium mb-3">{q.prompt}</p>
                {q.reference_answer && (
                  <div className="mb-4 p-3 bg-slate-50 rounded-lg border border-slate-200 text-sm">
                    <span className="font-semibold text-slate-700 block mb-1">Reference Answer:</span>
                    <p className="text-slate-600">{q.reference_answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>

      {showQuestionModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Add Question</h3>
            <form onSubmit={handleAddQuestion} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Question Prompt</label>
                <textarea
                  required
                  rows={3}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900"
                  placeholder="Explain photosynthesis and its two main stages..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Reference Answer (Optional)</label>
                <textarea
                  rows={3}
                  value={refAnswer}
                  onChange={(e) => setRefAnswer(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900"
                  placeholder="Key concepts include light-dependent reactions and Calvin cycle..."
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowQuestionModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700"
                >
                  Save Question
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
