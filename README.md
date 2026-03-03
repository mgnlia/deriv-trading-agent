# 🤖 Deriv Trading Agent

> Multi-agent AI trading system for forex/CFD markets using the A2A protocol + Deriv WebSocket API

[![CI](https://github.com/mgnlia/deriv-trading-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/mgnlia/deriv-trading-agent/actions)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    React Dashboard (Next.js)                     │
│   Portfolio Stats │ Agent Status │ Reasoning Log │ Trade History │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SSE / REST
┌──────────────────────────▼──────────────────────────────────────┐
│                 Portfolio Orchestrator (FastAPI)                  │
│                                                                   │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│   │   Market     │  │    Risk      │  │   Trade Execution    │  │
│   │  Analysis    │  │ Management   │  │       Agent          │  │
│   │   Agent      │  │   Agent      │  │                      │  │
│   │              │  │              │  │  Deriv WebSocket API │  │
│   │ RSI/MACD/BB  │  │ Kelly/VaR    │  │  wss://ws.binaryws  │  │
│   └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Role | Key Logic |
|-------|------|-----------|
| **Market Analysis** | Technical signals | RSI(14), MACD(12,26,9), Bollinger Bands(20,2), EMA crossover |
| **Risk Management** | Position sizing & approval | Kelly Criterion, VaR(95%), 2% max risk/trade |
| **Trade Execution** | Order placement & monitoring | Deriv WebSocket API, P&L tracking |
| **Portfolio Orchestrator** | Coordination & decisions | A2A pipeline, autonomous trading loop |

## Quick Start

### Docker Compose (recommended)

```bash
git clone https://github.com/mgnlia/deriv-trading-agent
cd deriv-trading-agent

# Optional: add your OpenAI key for LLM-enhanced analysis
echo "OPENAI_API_KEY=your-key" > .env

docker-compose up
```

- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd backend
pip install uv
uv pip install --system -e .
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + connection status |
| GET | `/api/state` | Full agent state snapshot |
| GET | `/api/stream` | SSE stream of real-time events |
| GET | `/api/market/{symbol}` | Latest market data |
| GET | `/api/portfolio` | Portfolio stats |
| GET | `/api/trades` | Trade history |
| POST | `/api/analyze` | Run multi-agent analysis |
| POST | `/api/trade` | Execute manual trade |
| POST | `/api/start-trading` | Start autonomous loop |
| POST | `/api/stop-trading` | Stop autonomous loop |

## Trading Instruments

| Symbol | Name | Type |
|--------|------|------|
| R_100 | Volatility 100 Index | Synthetic |
| R_75 | Volatility 75 Index | Synthetic |
| R_50 | Volatility 50 Index | Synthetic |
| frxEURUSD | EUR/USD | Forex |
| frxGBPUSD | GBP/USD | Forex |

## Risk Management

- **Max risk per trade**: 2% of portfolio (Kelly Criterion, half-Kelly)
- **Max concurrent positions**: 3
- **Daily loss limit**: 5%
- **Minimum signal confidence**: 60%
- **Position sizing**: Kelly = (bp - q) / b, where b=0.85 (Deriv payout), capped at 2%

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (optional) | OpenAI key for LLM-enhanced analysis |
| `DERIV_APP_ID` | `1089` | Deriv app ID (1089 = public demo) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for frontend |

## Deployment

**Frontend** (Vercel):
```bash
cd frontend
vercel --prod
```

**Backend** (Railway):
```bash
cd backend
railway up
```

## Demo Mode

The system works without any API keys:
- Deriv connection: falls back to realistic mock data (synthetic price feeds)
- OpenAI: not required for core trading logic (technical analysis is pure Python)

## License

MIT
