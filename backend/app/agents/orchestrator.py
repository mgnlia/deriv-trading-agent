"""
Portfolio Orchestrator Agent
Coordinates Market Analysis → Risk Management → Trade Execution.
Makes final trade decisions and maintains portfolio state.
"""
import asyncio
import logging
import time
from typing import Any, Optional

from app.agents.market_analysis import MarketAnalysisAgent
from app.agents.risk_management import RiskManagementAgent
from app.agents.trade_execution import TradeExecutionAgent
from app.deriv.client import DerivClient
from app.state import AgentState

logger = logging.getLogger(__name__)

TRADING_SYMBOLS = ["R_100", "R_75", "frxEURUSD", "frxGBPUSD"]
LOOP_INTERVAL = 60  # seconds between trading cycles


class PortfolioOrchestrator:
    """
    Agent 4: Master coordinator.
    Runs the A2A pipeline: analyze → assess risk → execute → monitor.
    """

    NAME = "orchestrator"

    def __init__(self, state: AgentState, deriv_client: DerivClient):
        self.state = state
        self.deriv = deriv_client
        self.market_agent = MarketAnalysisAgent(state)
        self.risk_agent = RiskManagementAgent(state)
        self.execution_agent = TradeExecutionAgent(state, deriv_client)

    async def analyze(self, symbol: str, question: str = "") -> dict[str, Any]:
        """
        Run full analysis pipeline on a symbol without executing a trade.
        Used by the /api/analyze endpoint.
        """
        self.state.update_agent_status(self.NAME, status="analyzing", last_action=f"Analyzing {symbol}")
        self.state.log_reasoning(self.NAME, "start", f"Orchestrating analysis for {symbol}")

        # Fetch price history
        history = await self.deriv.get_history(symbol, count=100, granularity=60)
        prices = self._extract_prices(history)

        if not prices:
            return {"error": f"No price data for {symbol}"}

        # Step 1: Market Analysis
        self.state.log_reasoning(self.NAME, "pipeline", "Step 1/3: Market Analysis Agent")
        analysis = await self.market_agent.analyze(symbol, prices)

        # Step 2: Risk Assessment
        self.state.log_reasoning(self.NAME, "pipeline", "Step 2/3: Risk Management Agent")
        risk = await self.risk_agent.evaluate(analysis, self.state.portfolio)

        # Step 3: Decision
        decision = "TRADE" if risk.get("approved") else "HOLD"
        self.state.log_reasoning(
            self.NAME, "decision",
            f"Decision: {decision} — {risk.get('reasoning', risk.get('reason', 'N/A'))}"
        )
        self.state.update_agent_status(
            self.NAME,
            status="idle",
            last_action=f"{decision}: {symbol}",
            decision=decision,
        )

        return {
            "symbol": symbol,
            "decision": decision,
            "analysis": analysis,
            "risk_assessment": risk,
            "timestamp": time.time(),
        }

    async def execute_trade(
        self,
        symbol: str,
        contract_type: str,
        duration: int,
        duration_unit: str,
        stake: float,
        basis: str,
    ) -> dict[str, Any]:
        """
        Execute a specific trade (manual trigger from API).
        """
        self.state.log_reasoning(self.NAME, "manual_trade", f"Manual trade: {contract_type} {symbol} ${stake}")

        # Build a synthetic risk assessment for manual trades
        risk_assessment = {
            "approved": True,
            "symbol": symbol,
            "signal": contract_type,
            "stake": stake,
            "confidence": 1.0,  # Manual override
            "reasoning": "Manual trade execution",
        }

        result = await self.execution_agent.execute(risk_assessment)
        return result

    async def run_trading_loop(self):
        """
        Autonomous trading loop.
        Cycles through symbols, analyzes, and executes approved trades.
        """
        self.state.trading_active = True
        self.state.log_reasoning(self.NAME, "loop_start", "Autonomous trading loop started")
        self.state.emit_event("trading_started", self.NAME, {"symbols": TRADING_SYMBOLS})

        cycle = 0
        while self.state.trading_active:
            cycle += 1
            self.state.log_reasoning(self.NAME, "cycle", f"Trading cycle #{cycle} — scanning {len(TRADING_SYMBOLS)} symbols")

            for symbol in TRADING_SYMBOLS:
                if not self.state.trading_active:
                    break

                try:
                    # Fetch history
                    history = await self.deriv.get_history(symbol, count=100, granularity=60)
                    prices = self._extract_prices(history)

                    if not prices:
                        continue

                    # Analyze
                    analysis = await self.market_agent.analyze(symbol, prices)

                    # Risk check
                    risk = await self.risk_agent.evaluate(analysis, self.state.portfolio)

                    # Execute if approved
                    if risk.get("approved"):
                        self.state.log_reasoning(
                            self.NAME, "executing",
                            f"Executing approved {risk['signal']} on {symbol} (${risk['stake']})"
                        )
                        await self.execution_agent.execute(risk)
                    else:
                        self.state.log_reasoning(
                            self.NAME, "skipped",
                            f"Skipping {symbol}: {risk.get('reason', 'Not approved')}"
                        )

                    # Small delay between symbols
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    self.state.log_reasoning(self.NAME, "error", f"Error on {symbol}: {str(e)}")

            # Wait before next cycle
            self.state.log_reasoning(self.NAME, "cycle_end", f"Cycle #{cycle} complete. Next in {LOOP_INTERVAL}s")
            await asyncio.sleep(LOOP_INTERVAL)

        self.state.log_reasoning(self.NAME, "loop_stop", "Autonomous trading loop stopped")
        self.state.emit_event("trading_stopped", self.NAME, {})
        self.state.update_agent_status(self.NAME, status="idle", last_action="Trading stopped")

    def _extract_prices(self, history: Any) -> list[float]:
        """Extract closing prices from Deriv history response."""
        if isinstance(history, dict):
            # Candles format
            if "candles" in history:
                return [float(c.get("close", 0)) for c in history["candles"] if c.get("close")]
            # Tick history format
            if "prices" in history:
                return [float(p) for p in history["prices"] if p]
        if isinstance(history, list):
            return [float(c.get("close", c.get("quote", 0))) for c in history if c]
        return []
