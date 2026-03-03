'use client'

interface Portfolio {
  balance: number
  equity: number
  open_positions: any[]
  total_pnl: number
  win_rate: number
  total_trades: number
  winning_trades: number
}

interface Props {
  portfolio: Portfolio
}

export default function PortfolioStats({ portfolio }: Props) {
  const pnlColor = portfolio.total_pnl >= 0 ? 'text-deriv-green' : 'text-deriv-red'
  const pnlSign = portfolio.total_pnl >= 0 ? '+' : ''

  const stats = [
    {
      label: 'Balance',
      value: `$${portfolio.balance.toFixed(2)}`,
      sub: 'Starting capital',
      color: 'text-white',
    },
    {
      label: 'Equity',
      value: `$${portfolio.equity.toFixed(2)}`,
      sub: 'Current value',
      color: 'text-white',
    },
    {
      label: 'Total P&L',
      value: `${pnlSign}$${portfolio.total_pnl.toFixed(2)}`,
      sub: `${pnlSign}${((portfolio.total_pnl / portfolio.balance) * 100).toFixed(1)}% return`,
      color: pnlColor,
    },
    {
      label: 'Win Rate',
      value: `${portfolio.win_rate.toFixed(1)}%`,
      sub: `${portfolio.winning_trades}/${portfolio.total_trades} trades`,
      color: portfolio.win_rate >= 50 ? 'text-deriv-green' : 'text-yellow-400',
    },
    {
      label: 'Open Positions',
      value: portfolio.open_positions.length.toString(),
      sub: 'Active contracts',
      color: portfolio.open_positions.length > 0 ? 'text-blue-400' : 'text-gray-400',
    },
    {
      label: 'Total Trades',
      value: portfolio.total_trades.toString(),
      sub: 'All time',
      color: 'text-gray-300',
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {stats.map((stat) => (
        <div key={stat.label} className="agent-card">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{stat.label}</p>
          <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
          <p className="text-xs text-gray-500 mt-0.5">{stat.sub}</p>
        </div>
      ))}
    </div>
  )
}
