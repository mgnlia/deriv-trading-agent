"""
Deriv WebSocket API Client
Connects to wss://ws.binaryws.com/websockets/v3 for real-time forex/CFD data.
Demo mode — no API key required for market data.
"""
import asyncio
import json
import logging
import time
from typing import Any, Callable, Optional

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

DERIV_WS_URL = "wss://ws.binaryws.com/websockets/v3?app_id=1089"


class DerivClient:
    """
    Async WebSocket client for the Deriv API.
    Handles connection, subscriptions, and request/response matching.
    """

    def __init__(self):
        self.ws: Optional[Any] = None
        self.connected = False
        self._req_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._subscriptions: dict[str, list[Callable]] = {}
        self._tick_cache: dict[str, dict] = {}
        self._recv_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Connect to Deriv WebSocket and start receive loop."""
        while True:
            try:
                logger.info(f"Connecting to Deriv API: {DERIV_WS_URL}")
                async with websockets.connect(DERIV_WS_URL) as ws:
                    self.ws = ws
                    self.connected = True
                    logger.info("Connected to Deriv API")
                    await self._recv_loop()
            except Exception as e:
                logger.error(f"Deriv connection error: {e}")
                self.connected = False
                self.ws = None
                await asyncio.sleep(5)  # Reconnect after 5s

    async def disconnect(self):
        """Disconnect from Deriv API."""
        self.connected = False
        if self.ws:
            await self.ws.close()

    async def _recv_loop(self):
        """Receive messages and dispatch to handlers."""
        try:
            async for raw in self.ws:
                try:
                    msg = json.loads(raw)
                    await self._dispatch(msg)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON: {raw[:100]}")
        except ConnectionClosed:
            logger.warning("Deriv WebSocket connection closed")
            self.connected = False

    async def _dispatch(self, msg: dict):
        """Route incoming messages to pending futures or subscription callbacks."""
        req_id = msg.get("req_id")
        msg_type = msg.get("msg_type")

        # Resolve pending request
        if req_id and req_id in self._pending:
            fut = self._pending.pop(req_id)
            if not fut.done():
                if "error" in msg:
                    fut.set_exception(Exception(msg["error"]["message"]))
                else:
                    fut.set_result(msg)

        # Handle tick subscriptions
        if msg_type == "tick":
            tick = msg.get("tick", {})
            symbol = tick.get("symbol")
            if symbol:
                self._tick_cache[symbol] = {
                    "symbol": symbol,
                    "price": tick.get("quote"),
                    "bid": tick.get("bid"),
                    "ask": tick.get("ask"),
                    "timestamp": tick.get("epoch", time.time()),
                }
                # Notify subscribers
                for cb in self._subscriptions.get(f"tick:{symbol}", []):
                    try:
                        await cb(self._tick_cache[symbol])
                    except Exception as e:
                        logger.error(f"Tick callback error: {e}")

        # Handle OHLC subscriptions
        if msg_type == "ohlc":
            ohlc = msg.get("ohlc", {})
            symbol = ohlc.get("symbol")
            if symbol:
                for cb in self._subscriptions.get(f"ohlc:{symbol}", []):
                    try:
                        await cb(ohlc)
                    except Exception as e:
                        logger.error(f"OHLC callback error: {e}")

    async def _send(self, payload: dict, timeout: float = 10.0) -> dict:
        """Send a request and wait for response."""
        if not self.connected or not self.ws:
            # Return mock data if not connected (for testing)
            return self._mock_response(payload)

        self._req_id += 1
        payload["req_id"] = self._req_id
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[self._req_id] = fut

        await self.ws.send(json.dumps(payload))
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(self._req_id, None)
            logger.warning(f"Request timeout: {payload}")
            return self._mock_response(payload)

    def _mock_response(self, payload: dict) -> dict:
        """Return mock data when not connected (demo/testing mode)."""
        import random
        msg_type = list(payload.keys())[0]

        if msg_type == "ticks":
            symbol = payload["ticks"]
            base = {"R_100": 6543.21, "R_75": 2341.56, "R_50": 1234.78,
                    "frxEURUSD": 1.0856, "frxGBPUSD": 1.2634}.get(symbol, 100.0)
            price = base * (1 + random.uniform(-0.002, 0.002))
            return {
                "msg_type": "tick",
                "tick": {
                    "symbol": symbol,
                    "quote": round(price, 5),
                    "bid": round(price * 0.9999, 5),
                    "ask": round(price * 1.0001, 5),
                    "epoch": int(time.time()),
                }
            }

        if msg_type == "ticks_history":
            symbol = payload.get("ticks_history", "R_100")
            base = 6543.21
            count = payload.get("count", 100)
            prices = [round(base * (1 + random.uniform(-0.01, 0.01)), 2) for _ in range(count)]
            times = [int(time.time()) - (count - i) * 60 for i in range(count)]
            return {
                "msg_type": "history",
                "history": {"prices": prices, "times": times}
            }

        if msg_type == "buy":
            return {
                "msg_type": "buy",
                "buy": {
                    "contract_id": random.randint(100000, 999999),
                    "buy_price": payload.get("price", 10.0),
                    "payout": payload.get("price", 10.0) * 1.85,
                    "transaction_id": random.randint(1000000, 9999999),
                    "purchase_time": int(time.time()),
                    "start_time": int(time.time()),
                    "longcode": "Demo trade",
                }
            }

        return {"msg_type": msg_type, "echo_req": payload}

    # ── Public API ─────────────────────────────────────────────────────────────

    async def get_tick(self, symbol: str) -> dict:
        """Get latest tick for a symbol."""
        if symbol in self._tick_cache:
            return self._tick_cache[symbol]
        resp = await self._send({"ticks": symbol})
        tick = resp.get("tick", {})
        return {
            "symbol": symbol,
            "price": tick.get("quote"),
            "bid": tick.get("bid"),
            "ask": tick.get("ask"),
            "timestamp": tick.get("epoch", time.time()),
        }

    async def get_history(self, symbol: str, count: int = 100, granularity: int = 60) -> dict:
        """Get historical OHLC data."""
        resp = await self._send({
            "ticks_history": symbol,
            "count": count,
            "end": "latest",
            "granularity": granularity,
            "style": "candles" if granularity > 0 else "ticks",
        })
        return resp.get("candles", resp.get("history", {}))

    async def subscribe_ticks(self, symbol: str, callback: Callable):
        """Subscribe to real-time ticks for a symbol."""
        key = f"tick:{symbol}"
        if key not in self._subscriptions:
            self._subscriptions[key] = []
            # Send subscription request
            await self._send({"ticks": symbol, "subscribe": 1})
        self._subscriptions[key].append(callback)

    async def buy_contract(
        self,
        symbol: str,
        contract_type: str,
        duration: int,
        duration_unit: str,
        stake: float,
        basis: str = "stake",
    ) -> dict:
        """Place a trade on Deriv."""
        # First get price proposal
        proposal_resp = await self._send({
            "proposal": 1,
            "amount": stake,
            "basis": basis,
            "contract_type": contract_type,
            "currency": "USD",
            "duration": duration,
            "duration_unit": duration_unit,
            "symbol": symbol,
        })

        proposal = proposal_resp.get("proposal", {})
        proposal_id = proposal.get("id")

        if not proposal_id:
            return {"error": "Could not get proposal", "details": proposal_resp}

        # Buy the contract
        buy_resp = await self._send({
            "buy": proposal_id,
            "price": stake,
        })

        return buy_resp.get("buy", buy_resp)

    async def get_portfolio(self) -> dict:
        """Get open contracts."""
        resp = await self._send({"portfolio": 1, "contract_type": []})
        return resp.get("portfolio", {"contracts": []})

    async def get_profit_table(self) -> dict:
        """Get closed contracts P&L."""
        resp = await self._send({
            "profit_table": 1,
            "description": 1,
            "limit": 25,
        })
        return resp.get("profit_table", {"transactions": []})
