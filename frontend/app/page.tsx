'use client'

import { useEffect, useState, useCallback } from 'react'
import AgentPanel from '@/components/AgentPanel'
import PortfolioStats from '@/components/PortfolioStats'
import ReasoningLog from '@/components/ReasoningLog'
import TradeHistory from '@/components/TradeHistory'
import MarketData from '@/components/MarketData'
import ControlPanel from '@/components/ControlPanel'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface AgentStatus {
  status: string
  last_action: string | null
  confidence?: number
  risk_level?: string
  open_trades?: number
  decision?: string | null
}

interface Portfolio {
  balance: number
  equity: number
  open_positions: any[]
  total_pnl: number
  win_rate: number
  total_trades: number
  winning_trades: number
}

interface ReasoningEntry {
  agent: string
  step: string
  content: string
  timestamp: number
}

interface AppState {
  agents: Record<string, AgentStatus>
  portfolio: Portfolio
  market_data: Record<string, any>
  recent_trades: any[]
  recent_reasoning: ReasoningEntry[]
  trading_active: boolean
}

const DEFAULT_STATE: AppState = {
  agents: {
    market_analysis: { status: 'idle', last_action: null, confidence: 0 },
    risk_management: { status: 'idle', last_action: null, risk_level: 'low' },
    trade_execution: { status: 'idle', last_action: null, open_trades: 0 },
    orchestrator: { status: 'idle', last_action: null, decision: null },
  },
  portfolio: {
    balance: 10000,
    equity: 10000,
    open_positions: [],
    total_pnl: 0,
    win_rate: 0,
    total_trades: 0,
    winning_trades: 0,
  },
  market_data: {},
  recent_trades: [],
  recent_reasoning: [],
  trading_active: false,
}

export default function Dashboard() {
  const [state, setState] = useState<AppState>(DEFAULT_STATE)
  const [connected, setConnected] = useState(false)
  const [events, setEvents] = useState<any[]>([])

  // Fetch initial state
  const fetchState = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/state`)
      if (res.ok) {
        const data = await res.json()
        setState(data)
        setConnected(true)
      }
    } catch {
      setConnected(false)
    }
  }, [])

  // SSE connection for real-time updates
  useEffect(() => {
    fetchState()

    const es = new EventSource(`${API_URL}/api/stream`)

    es.onopen = () => setConnected(true)
    es.onerror = () => {
      setConnected(false)
      // Fallback: poll every 3s
      const poll = setInterval(fetchState, 3000)
      return () => clearInterval(poll)
    }

    es.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data)
        if (event.type === 'snapshot') {
          setState(event.data)
        } else {
          setEvents(prev => [event, ...prev].slice(0, 50))
          // Also refresh state on any event
          fetchState()
        }
      } catch {}
    }

    return () => es.close()
  }, [fetchState])

  const handleStartTrading = async () => {
    await fetch(`${API_URL}/api/start-trading`, { method: 'POST' })
    fetchState()
  }

  const handleStopTrading = async () => {
    await fetch(`${API_URL}/api/stop-trading`, { method: 'POST' })
    fetchState()
  }

  const handleAnalyze = async (symbol: string) => {
    const res = await fetch(`${API_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, question: '' }),
    })
    const data = await res.json()
    fetchState()
    return data
  }

  return (
    <div className="min-h-screen bg-deriv-dark p-4 md:p-6">
      {/* Header */}
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">
            <span className="text-deriv-red">Deriv</span> Trading Agent
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Multi-Agent AI Trading System · A2A Protocol
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 text-sm ${connected ? 'text-deriv-green' : 'text-red-400'}`}>
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-deriv-green pulse-green' : 'bg-red-400'}`} />
            {connected ? 'Connected' : 'Disconnected'}
          </div>
          {state.trading_active && (
            <div className="flex items-center gap-2 text-sm text-yellow-400">
              <div className="w-2 h-2 rounded-full bg-yellow-400 pulse-green" />
              Trading Active
            </div>
          )}
        </div>
      </header>

      {/* Portfolio Stats */}
      <div className="mb-6">
        <PortfolioStats portfolio={state.portfolio} />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Agents + Control */}
        <div className="lg:col-span-1 space-y-4">
          <ControlPanel
            tradingActive={state.trading_active}
            onStart={handleStartTrading}
            onStop={handleStopTrading}
            onAnalyze={handleAnalyze}
          />
          <AgentPanel agents={state.agents} />
        </div>

        {/* Center: Market Data + Reasoning */}
        <div className="lg:col-span-1 space-y-4">
          <MarketData marketData={state.market_data} apiUrl={API_URL} />
          <ReasoningLog entries={state.recent_reasoning} />
        </div>

        {/* Right: Trade History */}
        <div className="lg:col-span-1">
          <TradeHistory
            trades={state.recent_trades}
            openPositions={state.portfolio.open_positions}
          />
        </div>
      </div>

      {/* Architecture note */}
      <footer className="mt-8 text-center text-gray-600 text-xs">
        A2A Protocol · 4 Specialized Agents · Deriv WebSocket API · Real-time Dashboard
      </footer>
    </div>
  )
}
