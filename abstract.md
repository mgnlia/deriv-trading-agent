# Deriv Trading Agent — Project Abstract

## Overview

**Deriv Trading Agent** is a multi-agent AI system for autonomous forex and CFD trading, built using the Agent-to-Agent (A2A) protocol and the Deriv WebSocket API. Unlike single-agent trading bots, this system coordinates four specialized AI agents that collaborate in real time to analyze markets, assess risk, execute trades, and manage portfolio state.

## Architecture

The system implements Google's A2A protocol to enable structured agent-to-agent communication:

```
User / Dashboard
       │
       ▼
Portfolio Orchestrator (Agent 4)
       │
       ├─► Market Analysis Agent (Agent 1)
       │       RSI, MACD, Bollinger Bands, EMA crossover
       │       → Signal: CALL/PUT/NEUTRAL + confidence score
       │
       ├─► Risk Management Agent (Agent 2)
       │       Kelly Criterion position sizing
       │       VaR (95%), drawdown limits, win-rate tracking
       │       → Approve/Reject + stake size
       │
       └─► Trade Execution Agent (Agent 3)
               Deriv WebSocket API (wss://ws.binaryws.com)
               Contract placement, monitoring, P&L settlement
```

## Technical Stack

- **Backend**: Python + FastAPI + WebSockets
- **AI Agents**: 4 specialized agents with A2A protocol
- **Market Data**: Deriv WebSocket API (real-time ticks, OHLC history)
- **Technical Analysis**: RSI(14), MACD(12,26,9), Bollinger Bands(20,2), EMA(9,21)
- **Risk Engine**: Kelly Criterion (half-Kelly), VaR(95%), max 2% per trade
- **Frontend**: Next.js + TypeScript + Tailwind CSS + Recharts
- **Real-time**: SSE (Server-Sent Events) for live dashboard updates
- **Deployment**: Docker Compose (local), Vercel (frontend), Railway (backend)

## Key Innovations

1. **True Multi-Agent Coordination**: Each agent has a distinct role and communicates via structured A2A messages. The orchestrator synthesizes all agent outputs before making trade decisions.

2. **Transparent Reasoning**: Every agent logs its reasoning steps in real time, visible in the dashboard. Users can see exactly why each trade was approved or rejected.

3. **Risk-First Architecture**: The Risk Management Agent operates as a mandatory gate — no trade executes without explicit approval based on portfolio-level risk metrics.

4. **Deriv Integration**: Native WebSocket integration with Deriv's API for real-time market data and trade execution on synthetic indices and forex pairs.

5. **Demo-Mode Fallback**: Works without API keys — mock data mode enables judges to run and test the full pipeline locally.

## Trading Strategy

- **Instruments**: Volatility Indices (R_100, R_75, R_50), Forex (EUR/USD, GBP/USD)
- **Contract Type**: Binary options (CALL/PUT), 5-minute duration
- **Signal Generation**: Multi-indicator consensus (RSI + MACD + Bollinger + Trend)
- **Position Sizing**: Half-Kelly Criterion, capped at 2% portfolio risk per trade
- **Risk Limits**: Max 3 concurrent positions, 5% daily loss limit, min 60% confidence

## Demo

- **Live Dashboard**: https://deriv-trading-agent.vercel.app
- **API**: https://deriv-trading-agent.railway.app
- **Docker**: `docker-compose up` — runs full stack locally in 2 minutes

## Team

Built for the lablab.ai Rise of AI Agents Hackathon (April 6-11, 2026)
Sponsor: Deriv | Prize: $50,000
