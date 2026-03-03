"""
Deriv Trading Agent — FastAPI Backend
Multi-agent forex/CFD trading system with A2A protocol + Deriv WebSocket API
"""
import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.orchestrator import PortfolioOrchestrator
from app.deriv.client import DerivClient
from app.state import AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
agent_state = AgentState()
deriv_client = DerivClient()
orchestrator = PortfolioOrchestrator(agent_state, deriv_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks on startup."""
    logger.info("Starting Deriv Trading Agent backend...")
    # Connect to Deriv WebSocket
    asyncio.create_task(deriv_client.connect())
    yield
    logger.info("Shutting down...")
    await deriv_client.disconnect()


app = FastAPI(
    title="Deriv Trading Agent",
    description="Multi-agent forex/CFD trading system using A2A protocol",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class TradeRequest(BaseModel):
    symbol: str = "R_100"
    contract_type: str = "CALL"
    duration: int = 5
    duration_unit: str = "m"
    stake: float = 10.0
    basis: str = "stake"


class AnalysisRequest(BaseModel):
    symbol: str = "R_100"
    question: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "deriv_connected": deriv_client.connected,
        "agents": list(agent_state.agent_statuses.keys()),
    }


@app.get("/api/state")
async def get_state():
    """Return full agent state snapshot."""
    return agent_state.snapshot()


@app.get("/api/market/{symbol}")
async def get_market_data(symbol: str):
    """Get latest market data for a symbol."""
    data = agent_state.market_data.get(symbol)
    if not data:
        # Fetch from Deriv
        data = await deriv_client.get_tick(symbol)
    return data or {"symbol": symbol, "price": None, "error": "No data available"}


@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio state."""
    return agent_state.portfolio


@app.get("/api/trades")
async def get_trades():
    """Get trade history."""
    return {"trades": agent_state.trade_history[-50:]}


@app.post("/api/analyze")
async def analyze(req: AnalysisRequest):
    """Run multi-agent analysis on a symbol."""
    try:
        result = await orchestrator.analyze(req.symbol, req.question)
        return result
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trade")
async def execute_trade(req: TradeRequest):
    """Execute a trade via the orchestrator."""
    try:
        result = await orchestrator.execute_trade(
            symbol=req.symbol,
            contract_type=req.contract_type,
            duration=req.duration,
            duration_unit=req.duration_unit,
            stake=req.stake,
            basis=req.basis,
        )
        return result
    except Exception as e:
        logger.error(f"Trade error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/start-trading")
async def start_trading():
    """Start autonomous trading loop."""
    if agent_state.trading_active:
        return {"status": "already_running"}
    asyncio.create_task(orchestrator.run_trading_loop())
    return {"status": "started"}


@app.post("/api/stop-trading")
async def stop_trading():
    """Stop autonomous trading loop."""
    agent_state.trading_active = False
    return {"status": "stopped"}


@app.get("/api/stream")
async def stream_events(request: Request):
    """SSE endpoint — streams agent events to the dashboard."""
    async def event_generator() -> AsyncGenerator[str, None]:
        last_idx = 0
        while True:
            if await request.is_disconnected():
                break
            events = agent_state.events[last_idx:]
            for event in events:
                yield f"data: {json.dumps(event)}\n\n"
                last_idx += 1
            # Also send periodic state snapshot
            yield f"data: {json.dumps({'type': 'snapshot', 'data': agent_state.snapshot()})}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/symbols")
async def get_symbols():
    """Get available trading symbols."""
    return {
        "symbols": [
            {"id": "R_100", "name": "Volatility 100 Index", "type": "synthetic"},
            {"id": "R_75", "name": "Volatility 75 Index", "type": "synthetic"},
            {"id": "R_50", "name": "Volatility 50 Index", "type": "synthetic"},
            {"id": "R_25", "name": "Volatility 25 Index", "type": "synthetic"},
            {"id": "frxEURUSD", "name": "EUR/USD", "type": "forex"},
            {"id": "frxGBPUSD", "name": "GBP/USD", "type": "forex"},
            {"id": "frxUSDJPY", "name": "USD/JPY", "type": "forex"},
            {"id": "frxAUDUSD", "name": "AUD/USD", "type": "forex"},
        ]
    }
