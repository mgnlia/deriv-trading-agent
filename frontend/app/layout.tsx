import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Deriv Trading Agent — Multi-Agent AI Trading System',
  description: 'A2A protocol multi-agent forex/CFD trading system powered by AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-deriv-dark text-white min-h-screen">{children}</body>
    </html>
  )
}
