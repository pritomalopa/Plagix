'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

interface Submission {
  id: string
  student_label: string
  original_filename: string
  extraction_status: string
  created_at: string
}

export default function UploadSubmissionsPage() {
  const params = useParams()
  const id = params.id as string
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [files, setFiles] = useState<FileList | null>(null)
  const [message, setMessage] = useState('')
  const router = useRouter()

  const fetchSubmissions = async () => {
    try {
      const res = await fetch(`/api/evaluations/${id}/submissions`)
      if (res.status === 401) {
        router.push('/login')
        return
      }
      if (res.ok) {
        const data = await res.json()
        setSubmissions(data.submissions || [])
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) fetchSubmissions()
  }, [id])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!files || files.length === 0) return

    setUploading(true)
    setMessage('')
    const formData = new FormData()
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i])
    }

    try {
      const res = await fetch(`/api/evaluations/${id}/upload`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Upload failed')
      }
      setMessage(`Successfully uploaded ${data.uploaded_count || files.length} file(s).`)
      setFiles(null)
      fetchSubmissions()
    } catch (err: any) {
      setMessage(`Error: ${err.message}`)
    } finally {
      setUploading(false)
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
          <h1 className="text-lg font-bold text-slate-900">Submission Ingestion</h1>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm h-fit">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Upload Student Files</h3>
            <p className="text-sm text-slate-500 mb-4">
              Upload individual files (PDF, DOCX, TXT) or a ZIP archive containing multiple submissions.
            </p>

            {message && (
              <div className="mb-4 p-3 bg-indigo-50 border border-indigo-200 text-indigo-700 text-sm rounded-lg">
                {message}
              </div>
            )}

            <form onSubmit={handleUpload} className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-indigo-500 transition-colors">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt,.zip"
                  onChange={(e) => setFiles(e.target.files)}
                  className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                />
              </div>
              <button
                type="submit"
                disabled={uploading || !files}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-sm disabled:opacity-50"
              >
                {uploading ? 'Uploading & Extracting...' : 'Upload & Process Files'}
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Ingested Submissions ({submissions.length})</h3>
            {loading ? (
              <p className="text-slate-500">Loading submissions...</p>
            ) : submissions.length === 0 ? (
              <p className="text-slate-500">No submissions uploaded yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                      <th className="py-3 px-4">Student Label</th>
                      <th className="py-3 px-4">Original Filename</th>
                      <th className="py-3 px-4">Extraction Status</th>
                      <th className="py-3 px-4">Uploaded At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {submissions.map((sub) => (
                      <tr key={sub.id} className="hover:bg-slate-50">
                        <td className="py-3 px-4 font-medium text-slate-900">{sub.student_label}</td>
                        <td className="py-3 px-4 text-slate-600">{sub.original_filename}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded-md text-xs font-semibold ${
                            sub.extraction_status === 'completed' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'
                          }`}>
                            {sub.extraction_status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-500">{new Date(sub.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
