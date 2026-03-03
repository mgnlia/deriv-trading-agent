'use client'

import { useState } from 'react'

interface Props {
  tradingActive: boolean
  onStart: () => void
  onStop: () => void
  onAnalyze: (symbol: string) => Promise<any>
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ControlPanel({ tradingActive, onStart, onStop, onAnalyze }: Props) {
  const [symbol, setSymbol] = useState('R_100')
  const [contractType, setContractType] = useState('CALL')
  const [stake, setStake] = useState('10')
  const [trading, setTrading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleManualTrade = async () => {
    setTrading(true)
    setResult(null)
    try {
      const res = await fetch(`${API_URL}/api/trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          contract_type: contractType,
          duration: 5,
          duration_unit: 'm',
          stake: parseFloat(stake),
          basis: 'stake',
        }),
      })
      const data = await res.json()
      if (data.success) {
        setResult(`✅ Trade placed! Contract #${data.trade?.contract_id}`)
      } else {
        setResult(`❌ ${data.error || data.reason || 'Trade failed'}`)
      }
    } catch (e) {
      setResult('❌ Connection error')
    } finally {
      setTrading(false)
    }
  }

  return (
    <div className="agent-card space-y-4">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
        🎮 Control Panel
      </h2>

      {/* Auto Trading */}
      <div>
        <p className="text-xs text-gray-500 mb-2">Autonomous Trading Loop</p>
        {tradingActive ? (
          <button
            onClick={onStop}
            className="w-full bg-red-900/40 hover:bg-red-900/60 border border-red-700/50 text-red-300 font-semibold py-2 rounded-lg transition-colors text-sm"
          >
            ⏹ Stop Trading
          </button>
        ) : (
          <button
            onClick={onStart}
            className="w-full bg-deriv-green/20 hover:bg-deriv-green/30 border border-deriv-green/40 text-deriv-green font-semibold py-2 rounded-lg transition-colors text-sm"
          >
            ▶ Start Auto Trading
          </button>
        )}
      </div>

      <div className="border-t border-deriv-border pt-4">
        <p className="text-xs text-gray-500 mb-2">Manual Trade</p>
        <div className="grid grid-cols-2 gap-2 mb-2">
          <select
            value={symbol}
            onChange={e => setSymbol(e.target.value)}
            className="bg-black/40 border border-deriv-border text-white text-xs rounded px-2 py-1.5"
          >
            <option value="R_100">Vol 100</option>
            <option value="R_75">Vol 75</option>
            <option value="R_50">Vol 50</option>
            <option value="frxEURUSD">EUR/USD</option>
            <option value="frxGBPUSD">GBP/USD</option>
          </select>
          <select
            value={contractType}
            onChange={e => setContractType(e.target.value)}
            className="bg-black/40 border border-deriv-border text-white text-xs rounded px-2 py-1.5"
          >
            <option value="CALL">CALL (↑)</option>
            <option value="PUT">PUT (↓)</option>
          </select>
        </div>
        <div className="flex gap-2">
          <input
            type="number"
            value={stake}
            onChange={e => setStake(e.target.value)}
            min="1"
            max="100"
            className="flex-1 bg-black/40 border border-deriv-border text-white text-xs rounded px-2 py-1.5"
            placeholder="Stake ($)"
          />
          <button
            onClick={handleManualTrade}
            disabled={trading}
            className="bg-deriv-red/80 hover:bg-deriv-red text-white font-semibold px-4 py-1.5 rounded text-xs transition-colors disabled:opacity-50"
          >
            {trading ? '...' : 'Trade'}
          </button>
        </div>
        {result && (
          <p className={`text-xs mt-2 ${result.startsWith('✅') ? 'text-green-400' : 'text-red-400'}`}>
            {result}
          </p>
        )}
      </div>
    </div>
  )
}
