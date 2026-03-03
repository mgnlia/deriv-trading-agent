"""
Market Analysis Agent
Computes technical indicators (RSI, MACD, Bollinger Bands) and generates
buy/sell signals with confidence scores.
"""
import logging
import time
from typing import Any

import numpy as np

from app.state import AgentState

logger = logging.getLogger(__name__)


class MarketAnalysisAgent:
    """
    Agent 1: Technical analysis + signal generation.
    Uses RSI, MACD, Bollinger Bands, and trend analysis.
    """

    NAME = "market_analysis"

    def __init__(self, state: AgentState):
        self.state = state

    async def analyze(self, symbol: str, prices: list[float]) -> dict[str, Any]:
        """
        Run full technical analysis on price history.
        Returns signals with confidence scores.
        """
        self.state.update_agent_status(self.NAME, status="analyzing", last_action=f"Analyzing {symbol}")
        self.state.log_reasoning(self.NAME, "start", f"Starting technical analysis for {symbol} with {len(prices)} candles")

        if len(prices) < 26:
            self.state.log_reasoning(self.NAME, "warning", f"Insufficient data ({len(prices)} candles), need ≥26 for MACD")
            return self._insufficient_data_signal(symbol)

        prices_arr = np.array(prices, dtype=float)

        # RSI
        rsi = self._compute_rsi(prices_arr)
        self.state.log_reasoning(self.NAME, "rsi", f"RSI(14) = {rsi:.2f}")

        # MACD
        macd_line, signal_line, histogram = self._compute_macd(prices_arr)
        self.state.log_reasoning(self.NAME, "macd", f"MACD = {macd_line:.4f}, Signal = {signal_line:.4f}, Hist = {histogram:.4f}")

        # Bollinger Bands
        upper, middle, lower = self._compute_bollinger(prices_arr)
        current_price = prices_arr[-1]
        bb_position = (current_price - lower) / (upper - lower) if upper != lower else 0.5
        self.state.log_reasoning(self.NAME, "bollinger", f"BB position = {bb_position:.2f} (0=lower, 1=upper), price={current_price:.4f}")

        # Trend (EMA crossover)
        ema_fast = self._ema(prices_arr, 9)[-1]
        ema_slow = self._ema(prices_arr, 21)[-1]
        trend = "bullish" if ema_fast > ema_slow else "bearish"
        self.state.log_reasoning(self.NAME, "trend", f"EMA9={ema_fast:.4f} vs EMA21={ema_slow:.4f} → {trend}")

        # Signal generation
        signal, confidence = self._generate_signal(rsi, macd_line, signal_line, histogram, bb_position, trend)
        self.state.log_reasoning(self.NAME, "signal", f"Signal: {signal} (confidence: {confidence:.1%})")

        result = {
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "indicators": {
                "rsi": round(rsi, 2),
                "macd": round(macd_line, 6),
                "macd_signal": round(signal_line, 6),
                "macd_histogram": round(histogram, 6),
                "bb_upper": round(upper, 4),
                "bb_middle": round(middle, 4),
                "bb_lower": round(lower, 4),
                "bb_position": round(bb_position, 3),
                "ema_fast": round(ema_fast, 4),
                "ema_slow": round(ema_slow, 4),
                "trend": trend,
            },
            "current_price": round(current_price, 5),
            "timestamp": time.time(),
        }

        self.state.update_agent_status(
            self.NAME,
            status="done",
            last_action=f"{signal} signal ({confidence:.0%})",
            confidence=confidence,
        )
        self.state.market_data[symbol] = result
        return result

    def _generate_signal(
        self,
        rsi: float,
        macd: float,
        macd_signal: float,
        histogram: float,
        bb_pos: float,
        trend: str,
    ) -> tuple[str, float]:
        """Combine indicators into a trading signal with confidence."""
        bull_points = 0
        bear_points = 0
        total = 0

        # RSI (oversold = buy, overbought = sell)
        if rsi < 30:
            bull_points += 2
        elif rsi < 45:
            bull_points += 1
        elif rsi > 70:
            bear_points += 2
        elif rsi > 55:
            bear_points += 1
        total += 2

        # MACD crossover
        if histogram > 0 and macd > macd_signal:
            bull_points += 2
        elif histogram < 0 and macd < macd_signal:
            bear_points += 2
        total += 2

        # Bollinger Band position
        if bb_pos < 0.2:  # Near lower band
            bull_points += 1
        elif bb_pos > 0.8:  # Near upper band
            bear_points += 1
        total += 1

        # Trend alignment
        if trend == "bullish":
            bull_points += 1
        else:
            bear_points += 1
        total += 1

        # Determine signal
        if bull_points > bear_points:
            signal = "CALL"  # Deriv: buy call (price goes up)
            confidence = bull_points / total
        elif bear_points > bull_points:
            signal = "PUT"   # Deriv: buy put (price goes down)
            confidence = bear_points / total
        else:
            signal = "NEUTRAL"
            confidence = 0.5

        return signal, round(confidence, 3)

    def _compute_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        k = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = prices[i] * k + ema[i - 1] * (1 - k)
        return ema

    def _compute_macd(
        self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[float, float, float]:
        ema_fast = self._ema(prices, fast)
        ema_slow = self._ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._ema(macd_line, signal)
        histogram = macd_line[-1] - signal_line[-1]
        return macd_line[-1], signal_line[-1], histogram

    def _compute_bollinger(
        self, prices: np.ndarray, period: int = 20, num_std: float = 2.0
    ) -> tuple[float, float, float]:
        recent = prices[-period:]
        middle = np.mean(recent)
        std = np.std(recent)
        return middle + num_std * std, middle, middle - num_std * std

    def _insufficient_data_signal(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "signal": "NEUTRAL",
            "confidence": 0.0,
            "indicators": {},
            "current_price": 0.0,
            "timestamp": time.time(),
            "error": "Insufficient price history",
        }
