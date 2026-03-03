'use client'

import { useState } from 'react'

interface Props {
  marketData: Record<string, any>
  apiUrl: string
}

const SYMBOLS = [
  { id: 'R_100', name: 'Vol 100' },
  { id: 'R_75', name: 'Vol 75' },
  { id: 'R_50', name: 'Vol 50' },
  { id: 'frxEURUSD', name: 'EUR/USD' },
  { id: 'frxGBPUSD', name: 'GBP/USD' },
]

export default function MarketData({ marketData, apiUrl }: Props) {
  const [loading, setLoading] = useState<string | null>(null)
  const [analysisResult, setAnalysisResult] = useState<any>(null)

  const handleAnalyze = async (symbol: string) => {
    setLoading(symbol)
    try {
      const res = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, question: '' }),
      })
      const data = await res.json()
      setAnalysisResult(data)
    } catch (e) {
      setAnalysisResult({ error: 'Analysis failed' })
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="agent-card">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
        📈 Market Data
      </h2>
      <div className="space-y-2">
        {SYMBOLS.map((sym) => {
          const data = marketData[sym.id]
          return (
            <div key={sym.id} className="flex items-center justify-between bg-black/30 rounded-lg px-3 py-2">
              <div>
                <span className="text-sm font-medium text-white">{sym.name}</span>
                <span className="text-xs text-gray-500 ml-2">{sym.id}</span>
              </div>
              <div className="flex items-center gap-3">
                {data?.current_price ? (
                  <div className="text-right">
                    <div className="text-sm font-mono text-white">
                      {data.current_price.toFixed(data.current_price > 100 ? 2 : 5)}
                    </div>
                    {data.indicators?.rsi && (
                      <div className={`text-xs ${
                        data.indicators.rsi > 70 ? 'text-red-400' :
                        data.indicators.rsi < 30 ? 'text-green-400' : 'text-gray-500'
                      }`}>
                        RSI {data.indicators.rsi}
                      </div>
                    )}
                  </div>
                ) : (
                  <span className="text-xs text-gray-600">—</span>
                )}
                <button
                  onClick={() => handleAnalyze(sym.id)}
                  disabled={loading === sym.id}
                  className="text-xs bg-deriv-red/20 hover:bg-deriv-red/40 text-deriv-red border border-deriv-red/30 px-2 py-1 rounded transition-colors disabled:opacity-50"
                >
                  {loading === sym.id ? '...' : 'Analyze'}
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Analysis result */}
      {analysisResult && (
        <div className="mt-3 bg-black/40 rounded-lg p-3 text-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 font-semibold">Latest Analysis</span>
            <button
              onClick={() => setAnalysisResult(null)}
              className="text-gray-600 hover:text-gray-400"
            >✕</button>
          </div>
          {analysisResult.error ? (
            <p className="text-red-400">{analysisResult.error}</p>
          ) : (
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-gray-500">Symbol:</span>
                <span className="text-white">{analysisResult.symbol}</span>
                <span className={`ml-auto font-bold px-2 py-0.5 rounded ${
                  analysisResult.decision === 'TRADE' ? 'bg-green-900/40 text-green-400' : 'bg-gray-800 text-gray-400'
                }`}>
                  {analysisResult.decision}
                </span>
              </div>
              {analysisResult.analysis?.indicators && (
                <div className="grid grid-cols-2 gap-1 mt-2">
                  {Object.entries(analysisResult.analysis.indicators)
                    .filter(([k]) => ['rsi', 'macd_histogram', 'trend', 'bb_position'].includes(k))
                    .map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-gray-600">{k}:</span>
                        <span className="text-gray-300">{typeof v === 'number' ? (v as number).toFixed(3) : String(v)}</span>
                      </div>
                    ))}
                </div>
              )}
              {analysisResult.analysis?.signal && (
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-gray-500">Signal:</span>
                  <span className={`font-bold ${
                    analysisResult.analysis.signal === 'CALL' ? 'text-green-400' :
                    analysisResult.analysis.signal === 'PUT' ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {analysisResult.analysis.signal}
                  </span>
                  <span className="text-gray-500">
                    ({(analysisResult.analysis.confidence * 100).toFixed(0)}% confidence)
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
