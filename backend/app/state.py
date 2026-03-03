"""
Shared agent state — thread-safe state store for all agents.
"""
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """Central state shared across all agents."""

    # Agent statuses
    agent_statuses: dict[str, dict] = field(default_factory=lambda: {
        "market_analysis": {"status": "idle", "last_action": None, "confidence": 0.0},
        "risk_management": {"status": "idle", "last_action": None, "risk_level": "low"},
        "trade_execution": {"status": "idle", "last_action": None, "open_trades": 0},
        "orchestrator": {"status": "idle", "last_action": None, "decision": None},
    })

    # Market data cache
    market_data: dict[str, dict] = field(default_factory=dict)

    # Portfolio
    portfolio: dict[str, Any] = field(default_factory=lambda: {
        "balance": 10000.0,
        "equity": 10000.0,
        "open_positions": [],
        "total_pnl": 0.0,
        "win_rate": 0.0,
        "total_trades": 0,
        "winning_trades": 0,
    })

    # Trade history
    trade_history: list[dict] = field(default_factory=list)

    # SSE events queue
    events: list[dict] = field(default_factory=list)

    # Trading loop control
    trading_active: bool = False

    # Agent reasoning logs
    reasoning_log: list[dict] = field(default_factory=list)

    def emit_event(self, event_type: str, agent: str, data: Any):
        """Append an SSE event."""
        event = {
            "type": event_type,
            "agent": agent,
            "data": data,
            "timestamp": time.time(),
        }
        self.events.append(event)
        # Keep last 500 events
        if len(self.events) > 500:
            self.events = self.events[-500:]

    def update_agent_status(self, agent: str, **kwargs):
        """Update an agent's status fields."""
        if agent in self.agent_statuses:
            self.agent_statuses[agent].update(kwargs)
            self.emit_event("agent_status", agent, self.agent_statuses[agent])

    def log_reasoning(self, agent: str, step: str, content: str):
        """Log a reasoning step from an agent."""
        entry = {
            "agent": agent,
            "step": step,
            "content": content,
            "timestamp": time.time(),
        }
        self.reasoning_log.append(entry)
        if len(self.reasoning_log) > 200:
            self.reasoning_log = self.reasoning_log[-200:]
        self.emit_event("reasoning", agent, entry)

    def record_trade(self, trade: dict):
        """Record a completed trade and update portfolio stats."""
        self.trade_history.append(trade)
        self.portfolio["total_trades"] += 1
        pnl = trade.get("pnl", 0)
        self.portfolio["total_pnl"] += pnl
        if pnl > 0:
            self.portfolio["winning_trades"] += 1
        total = self.portfolio["total_trades"]
        wins = self.portfolio["winning_trades"]
        self.portfolio["win_rate"] = (wins / total * 100) if total > 0 else 0.0
        self.portfolio["equity"] = self.portfolio["balance"] + self.portfolio["total_pnl"]
        self.emit_event("trade_completed", "orchestrator", trade)

    def snapshot(self) -> dict:
        """Return a full state snapshot for the dashboard."""
        return {
            "agents": self.agent_statuses,
            "portfolio": self.portfolio,
            "market_data": self.market_data,
            "recent_trades": self.trade_history[-10:],
            "recent_reasoning": self.reasoning_log[-20:],
            "trading_active": self.trading_active,
        }
