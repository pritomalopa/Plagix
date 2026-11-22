import './globals.css'
import type { Metadata } from 'metadata' // wait, Metadata type is from 'next'

export const metadata = {
  title: 'PLAGIX - Academic Evaluation & Integrity Platform',
  description: 'AI-assisted grading, answer relevance, and plagiarism detection for educators.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">{children}</body>
    </html>
  )
}
