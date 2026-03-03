'use client'

interface Trade {
  contract_id: string | number
  symbol: string
  signal: string
  stake: number
  pnl?: number
  outcome?: string
  status: string
  entry_time: number
  exit_time?: number
}

interface Props {
  trades: Trade[]
  openPositions: Trade[]
}

export default function TradeHistory({ trades, openPositions }: Props) {
  const allTrades = [
    ...openPositions.map(p => ({ ...p, status: 'open' })),
    ...[...trades].reverse().slice(0, 20),
  ]

  return (
    <div className="agent-card">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
        📋 Trade History
      </h2>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {allTrades.length === 0 ? (
          <p className="text-gray-600 text-sm text-center py-8">
            No trades yet. Start the trading loop or execute a manual trade.
          </p>
        ) : (
          allTrades.map((trade, i) => {
            const isOpen = trade.status === 'open'
            const isWin = trade.outcome === 'WIN'
            const pnlColor = isOpen ? 'text-blue-400' :
              isWin ? 'text-deriv-green' : 'text-deriv-red'

            return (
              <div
                key={`${trade.contract_id}-${i}`}
                className={`flex items-center justify-between p-2 rounded-lg text-xs ${
                  isOpen ? 'bg-blue-900/20 border border-blue-900/40' : 'bg-black/30'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${trade.signal === 'CALL' ? 'text-deriv-green' : 'text-deriv-red'}`}>
                      {trade.signal}
                    </span>
                    <span className="text-gray-400">{trade.symbol}</span>
                    {isOpen && (
                      <span className="text-blue-400 text-xs bg-blue-900/30 px-1.5 py-0.5 rounded">
                        LIVE
                      </span>
                    )}
                  </div>
                  <div className="text-gray-500 mt-0.5">
                    ${trade.stake.toFixed(2)} stake ·{' '}
                    {new Date(trade.entry_time * 1000).toLocaleTimeString()}
                  </div>
                </div>
                <div className="text-right">
                  {isOpen ? (
                    <div className="text-blue-400">Monitoring...</div>
                  ) : (
                    <>
                      <div className={`font-bold ${pnlColor}`}>
                        {trade.pnl !== undefined ? `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toFixed(2)}` : '—'}
                      </div>
                      <div className={`text-xs ${isWin ? 'text-deriv-green' : 'text-deriv-red'}`}>
                        {trade.outcome || trade.status}
                      </div>
                    </>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
