"""
Risk Management Agent
Position sizing, stop-loss/take-profit calculation, portfolio risk metrics.
Implements Kelly Criterion and VaR-based position sizing.
"""
import logging
import math
import time
from typing import Any

from app.state import AgentState

logger = logging.getLogger(__name__)

# Risk parameters
MAX_RISK_PER_TRADE = 0.02      # Max 2% of portfolio per trade
MAX_PORTFOLIO_RISK = 0.10      # Max 10% total portfolio at risk
MIN_CONFIDENCE = 0.60          # Minimum signal confidence to trade
MAX_DAILY_LOSS = 0.05          # Stop trading if down 5% today


class RiskManagementAgent:
    """
    Agent 2: Risk assessment + position sizing.
    Approves/rejects trades based on portfolio risk limits.
    """

    NAME = "risk_management"

    def __init__(self, state: AgentState):
        self.state = state

    async def evaluate(
        self,
        signal: dict[str, Any],
        portfolio: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Evaluate a trading signal against risk limits.
        Returns: approved/rejected with position size and reasoning.
        """
        self.state.update_agent_status(self.NAME, status="evaluating", last_action="Evaluating trade risk")
        self.state.log_reasoning(self.NAME, "start", f"Evaluating {signal.get('signal')} signal for {signal.get('symbol')}")

        confidence = signal.get("confidence", 0.0)
        symbol = signal.get("symbol", "UNKNOWN")
        trade_signal = signal.get("signal", "NEUTRAL")

        # Check 1: Confidence threshold
        if confidence < MIN_CONFIDENCE:
            return self._reject(
                f"Confidence {confidence:.1%} below minimum {MIN_CONFIDENCE:.1%}",
                symbol, trade_signal
            )

        # Check 2: Neutral signal
        if trade_signal == "NEUTRAL":
            return self._reject("No directional signal", symbol, trade_signal)

        # Check 3: Portfolio balance
        balance = portfolio.get("balance", 0)
        equity = portfolio.get("equity", balance)
        if equity <= 0:
            return self._reject("Portfolio equity depleted", symbol, trade_signal)

        # Check 4: Daily loss limit
        total_pnl = portfolio.get("total_pnl", 0)
        initial_balance = portfolio.get("balance", 10000)
        daily_loss_pct = abs(min(total_pnl, 0)) / initial_balance
        if daily_loss_pct > MAX_DAILY_LOSS:
            return self._reject(
                f"Daily loss limit reached ({daily_loss_pct:.1%} > {MAX_DAILY_LOSS:.1%})",
                symbol, trade_signal
            )

        # Check 5: Open positions limit
        open_positions = len(portfolio.get("open_positions", []))
        if open_positions >= 3:
            return self._reject(
                f"Max concurrent positions reached ({open_positions}/3)",
                symbol, trade_signal
            )

        # Position sizing: Kelly Criterion adjusted
        stake = self._calculate_position_size(confidence, equity)
        self.state.log_reasoning(self.NAME, "sizing", f"Kelly-adjusted stake: ${stake:.2f} ({stake/equity:.1%} of equity)")

        # Risk metrics
        risk_metrics = self._compute_risk_metrics(portfolio, stake, equity)
        self.state.log_reasoning(self.NAME, "metrics", f"Risk metrics: {risk_metrics}")

        # Final approval
        self.state.update_agent_status(
            self.NAME,
            status="approved",
            last_action=f"Approved ${stake:.2f} stake",
            risk_level=risk_metrics["risk_level"],
        )

        return {
            "approved": True,
            "symbol": symbol,
            "signal": trade_signal,
            "stake": stake,
            "confidence": confidence,
            "risk_metrics": risk_metrics,
            "reasoning": f"Signal confidence {confidence:.1%} ≥ {MIN_CONFIDENCE:.1%}. Kelly-adjusted stake ${stake:.2f}.",
            "timestamp": time.time(),
        }

    def _calculate_position_size(self, confidence: float, equity: float) -> float:
        """
        Kelly Criterion: f = (bp - q) / b
        For binary options: b=0.85 (85% payout), p=confidence, q=1-p
        Capped at MAX_RISK_PER_TRADE.
        """
        b = 0.85   # Deriv typical payout
        p = confidence
        q = 1 - p
        kelly_fraction = (b * p - q) / b
        kelly_fraction = max(0, min(kelly_fraction, MAX_RISK_PER_TRADE))

        # Use half-Kelly for safety
        fraction = kelly_fraction * 0.5
        stake = equity * fraction

        # Clamp between $1 and $50
        return round(max(1.0, min(50.0, stake)), 2)

    def _compute_risk_metrics(self, portfolio: dict, stake: float, equity: float) -> dict:
        """Compute portfolio risk metrics."""
        risk_pct = stake / equity if equity > 0 else 0
        total_trades = portfolio.get("total_trades", 0)
        winning_trades = portfolio.get("winning_trades", 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.5

        # Simple VaR estimate (95% confidence, normal approximation)
        daily_return_std = 0.02  # Assume 2% daily std for synthetic indices
        var_95 = equity * daily_return_std * 1.645

        if risk_pct < 0.01:
            risk_level = "low"
        elif risk_pct < 0.02:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "stake_pct": round(risk_pct * 100, 2),
            "var_95": round(var_95, 2),
            "win_rate": round(win_rate * 100, 1),
            "risk_level": risk_level,
            "max_drawdown_allowed": round(MAX_DAILY_LOSS * 100, 1),
        }

    def _reject(self, reason: str, symbol: str, signal: str) -> dict:
        self.state.log_reasoning(self.NAME, "rejected", f"Trade rejected: {reason}")
        self.state.update_agent_status(
            self.NAME,
            status="rejected",
            last_action=f"Rejected: {reason}",
            risk_level="blocked",
        )
        return {
            "approved": False,
            "symbol": symbol,
            "signal": signal,
            "stake": 0.0,
            "reason": reason,
            "timestamp": time.time(),
        }
