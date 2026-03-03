'use client'

interface ReasoningEntry {
  agent: string
  step: string
  content: string
  timestamp: number
}

interface Props {
  entries: ReasoningEntry[]
}

const AGENT_COLORS: Record<string, string> = {
  orchestrator: 'text-deriv-red',
  market_analysis: 'text-yellow-400',
  risk_management: 'text-blue-400',
  trade_execution: 'text-purple-400',
}

const AGENT_LABELS: Record<string, string> = {
  orchestrator: 'Orchestrator',
  market_analysis: 'Market',
  risk_management: 'Risk',
  trade_execution: 'Execution',
}

export default function ReasoningLog({ entries }: Props) {
  const sorted = [...entries].reverse().slice(0, 20)

  return (
    <div className="agent-card">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
        🧠 Agent Reasoning
      </h2>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {sorted.length === 0 ? (
          <p className="text-gray-600 text-sm text-center py-4">
            No reasoning yet. Start trading or run an analysis.
          </p>
        ) : (
          sorted.map((entry, i) => (
            <div key={i} className="text-xs border-l-2 border-deriv-border pl-2 py-0.5">
              <div className="flex items-center gap-2 mb-0.5">
                <span className={`font-semibold ${AGENT_COLORS[entry.agent] || 'text-gray-400'}`}>
                  {AGENT_LABELS[entry.agent] || entry.agent}
                </span>
                <span className="text-gray-600">·</span>
                <span className="text-gray-500">{entry.step}</span>
                <span className="text-gray-700 ml-auto">
                  {new Date(entry.timestamp * 1000).toLocaleTimeString()}
                </span>
              </div>
              <p className="text-gray-300 leading-relaxed">{entry.content}</p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
