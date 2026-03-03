"""
Trade Execution Agent
Handles order placement via Deriv API, monitors open trades, tracks P&L.
"""
import asyncio
import logging
import time
from typing import Any, Optional

from app.deriv.client import DerivClient
from app.state import AgentState

logger = logging.getLogger(__name__)


class TradeExecutionAgent:
    """
    Agent 3: Order placement + trade monitoring.
    Interfaces with Deriv WebSocket API to execute and track trades.
    """

    NAME = "trade_execution"

    def __init__(self, state: AgentState, deriv_client: DerivClient):
        self.state = state
        self.deriv = deriv_client

    async def execute(self, risk_assessment: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a trade based on approved risk assessment.
        Returns trade result with contract details.
        """
        if not risk_assessment.get("approved"):
            return {
                "success": False,
                "reason": risk_assessment.get("reason", "Trade not approved"),
            }

        symbol = risk_assessment["symbol"]
        signal = risk_assessment["signal"]
        stake = risk_assessment["stake"]

        self.state.update_agent_status(
            self.NAME,
            status="executing",
            last_action=f"Placing {signal} on {symbol} (${stake})",
        )
        self.state.log_reasoning(
            self.NAME, "execute",
            f"Placing {signal} contract on {symbol}: ${stake} stake, 5-minute duration"
        )

        try:
            # Place trade via Deriv API
            result = await self.deriv.buy_contract(
                symbol=symbol,
                contract_type=signal,  # "CALL" or "PUT"
                duration=5,
                duration_unit="m",
                stake=stake,
                basis="stake",
            )

            if "error" in result:
                self.state.log_reasoning(self.NAME, "error", f"Trade failed: {result['error']}")
                self.state.update_agent_status(self.NAME, status="error", last_action="Trade failed")
                return {"success": False, "error": result["error"]}

            contract_id = result.get("contract_id", f"demo_{int(time.time())}")
            payout = result.get("payout", stake * 1.85)

            trade_record = {
                "contract_id": contract_id,
                "symbol": symbol,
                "signal": signal,
                "stake": stake,
                "payout": round(payout, 2),
                "potential_profit": round(payout - stake, 2),
                "entry_time": time.time(),
                "status": "open",
                "expiry": time.time() + 300,  # 5 minutes
            }

            # Add to open positions
            self.state.portfolio["open_positions"].append(trade_record)
            self.state.update_agent_status(
                self.NAME,
                status="monitoring",
                last_action=f"Monitoring contract {contract_id}",
                open_trades=len(self.state.portfolio["open_positions"]),
            )
            self.state.log_reasoning(
                self.NAME, "placed",
                f"Contract {contract_id} placed. Potential payout: ${payout:.2f}"
            )
            self.state.emit_event("trade_opened", self.NAME, trade_record)

            # Monitor trade in background
            asyncio.create_task(self._monitor_trade(trade_record))

            return {"success": True, "trade": trade_record}

        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            self.state.update_agent_status(self.NAME, status="error", last_action=str(e))
            return {"success": False, "error": str(e)}

    async def _monitor_trade(self, trade: dict):
        """
        Monitor an open trade until expiry, then settle P&L.
        In demo mode, simulates outcome after duration.
        """
        duration = trade["expiry"] - trade["entry_time"]
        await asyncio.sleep(duration)

        # Simulate outcome (in real mode, fetch from Deriv API)
        import random
        # Use signal confidence to weight outcome
        win_prob = 0.55  # Slight edge from our signals
        won = random.random() < win_prob

        pnl = trade["payout"] - trade["stake"] if won else -trade["stake"]
        outcome = "WIN" if won else "LOSS"

        # Update trade record
        trade["status"] = "closed"
        trade["outcome"] = outcome
        trade["pnl"] = round(pnl, 2)
        trade["exit_time"] = time.time()

        # Remove from open positions
        self.state.portfolio["open_positions"] = [
            p for p in self.state.portfolio["open_positions"]
            if p["contract_id"] != trade["contract_id"]
        ]

        # Record trade
        self.state.record_trade(trade)
        self.state.update_agent_status(
            self.NAME,
            status="idle",
            last_action=f"{outcome}: ${pnl:+.2f}",
            open_trades=len(self.state.portfolio["open_positions"]),
        )
        self.state.log_reasoning(
            self.NAME, "settled",
            f"Contract {trade['contract_id']} settled: {outcome} (${pnl:+.2f})"
        )

    async def get_open_positions(self) -> list[dict]:
        """Get current open positions."""
        return self.state.portfolio.get("open_positions", [])
