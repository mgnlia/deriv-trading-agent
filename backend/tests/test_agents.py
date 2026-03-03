"""
Tests for the trading agents.
"""
import asyncio
import pytest
from app.state import AgentState
from app.agents.market_analysis import MarketAnalysisAgent
from app.agents.risk_management import RiskManagementAgent


@pytest.fixture
def state():
    return AgentState()


@pytest.mark.asyncio
async def test_market_analysis_insufficient_data(state):
    agent = MarketAnalysisAgent(state)
    result = await agent.analyze("R_100", [100.0, 101.0, 99.0])
    assert result["signal"] == "NEUTRAL"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_market_analysis_with_data(state):
    agent = MarketAnalysisAgent(state)
    # Generate 100 synthetic prices
    import math
    prices = [100 + 5 * math.sin(i * 0.1) + i * 0.01 for i in range(100)]
    result = await agent.analyze("R_100", prices)
    assert result["signal"] in ("CALL", "PUT", "NEUTRAL")
    assert 0.0 <= result["confidence"] <= 1.0
    assert "rsi" in result["indicators"]
    assert "macd" in result["indicators"]


@pytest.mark.asyncio
async def test_risk_management_rejects_low_confidence(state):
    agent = RiskManagementAgent(state)
    signal = {"symbol": "R_100", "signal": "CALL", "confidence": 0.40}
    result = await agent.evaluate(signal, state.portfolio)
    assert not result["approved"]
    assert "Confidence" in result["reason"]


@pytest.mark.asyncio
async def test_risk_management_approves_high_confidence(state):
    agent = RiskManagementAgent(state)
    signal = {"symbol": "R_100", "signal": "CALL", "confidence": 0.75}
    result = await agent.evaluate(signal, state.portfolio)
    assert result["approved"]
    assert result["stake"] > 0


@pytest.mark.asyncio
async def test_risk_management_rejects_neutral(state):
    agent = RiskManagementAgent(state)
    signal = {"symbol": "R_100", "signal": "NEUTRAL", "confidence": 0.80}
    result = await agent.evaluate(signal, state.portfolio)
    assert not result["approved"]


def test_state_emit_event(state):
    state.emit_event("test", "orchestrator", {"msg": "hello"})
    assert len(state.events) == 1
    assert state.events[0]["type"] == "test"


def test_state_record_trade(state):
    trade = {"contract_id": "123", "stake": 10, "pnl": 8.5, "symbol": "R_100"}
    state.record_trade(trade)
    assert state.portfolio["total_trades"] == 1
    assert state.portfolio["winning_trades"] == 1
    assert state.portfolio["total_pnl"] == 8.5
