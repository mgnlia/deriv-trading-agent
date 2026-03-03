'use client'

interface AgentStatus {
  status: string
  last_action: string | null
  confidence?: number
  risk_level?: string
  open_trades?: number
  decision?: string | null
}

interface Props {
  agents: Record<string, AgentStatus>
}

const AGENT_META: Record<string, { name: string; icon: string; description: string }> = {
  orchestrator: {
    name: 'Portfolio Orchestrator',
    icon: '🎯',
    description: 'Coordinates all agents, makes final decisions',
  },
  market_analysis: {
    name: 'Market Analysis',
    icon: '📊',
    description: 'RSI, MACD, Bollinger Bands, trend detection',
  },
  risk_management: {
    name: 'Risk Management',
    icon: '🛡️',
    description: 'Kelly criterion, VaR, position sizing',
  },
  trade_execution: {
    name: 'Trade Execution',
    icon: '⚡',
    description: 'Deriv API order placement & monitoring',
  },
}

const STATUS_COLORS: Record<string, string> = {
  idle: 'text-gray-400 bg-gray-800',
  analyzing: 'text-yellow-400 bg-yellow-900/30',
  executing: 'text-blue-400 bg-blue-900/30',
  approved: 'text-green-400 bg-green-900/30',
  rejected: 'text-red-400 bg-red-900/30',
  monitoring: 'text-purple-400 bg-purple-900/30',
  done: 'text-green-400 bg-green-900/30',
  error: 'text-red-500 bg-red-900/40',
  evaluating: 'text-orange-400 bg-orange-900/30',
}

export default function AgentPanel({ agents }: Props) {
  const order = ['orchestrator', 'market_analysis', 'risk_management', 'trade_execution']

  return (
    <div className="agent-card">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
        🤖 Agent Status
      </h2>
      <div className="space-y-3">
        {order.map((agentId) => {
          const meta = AGENT_META[agentId]
          const status = agents[agentId] || { status: 'idle', last_action: null }
          const colorClass = STATUS_COLORS[status.status] || 'text-gray-400 bg-gray-800'

          return (
            <div key={agentId} className="bg-black/30 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{meta?.icon}</span>
                  <span className="text-sm font-medium text-white">{meta?.name}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colorClass}`}>
                  {status.status}
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-1">{meta?.description}</p>
              {status.last_action && (
                <p className="text-xs text-gray-400 truncate">
                  → {status.last_action}
                </p>
              )}
              {/* Extra metrics */}
              <div className="flex gap-3 mt-1">
                {status.confidence !== undefined && status.confidence > 0 && (
                  <span className="text-xs text-yellow-400">
                    {(status.confidence * 100).toFixed(0)}% conf
                  </span>
                )}
                {status.risk_level && status.risk_level !== 'low' && (
                  <span className={`text-xs ${
                    status.risk_level === 'high' ? 'text-red-400' :
                    status.risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {status.risk_level} risk
                  </span>
                )}
                {status.open_trades !== undefined && status.open_trades > 0 && (
                  <span className="text-xs text-purple-400">
                    {status.open_trades} open
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
