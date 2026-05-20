# END-TO-END WIRING — Coven Traders

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  SIGNAL AGGREGATOR (Python, async)                                  │
│  ├── On-chain listeners → Redis pub/sub channel: "signals:onchain" │
│  ├── Social scrapers    → Redis pub/sub channel: "signals:social"  │
│  ├── News feeds         → Redis pub/sub channel: "signals:news"    │
│  ├── Technical analysis → Redis pub/sub channel: "signals:tech"    │
│  ├── Prediction markets → Redis pub/sub channel: "signals:pred"    │
│  └── Cross-market arb   → Redis pub/sub channel: "signals:arb"     │
│                                                                     │
│  → Normalizer unifies to Signal schema                              │
│  → Publishes to "signals:normalized"                                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DISCIPLE AGENTS (Python, per-specialization)                       │
│  Each agent subscribes to relevant signal channels                  │
│  → Generates trade decisions                                        │
│  → Publishes to Redis: "trades:proposed"                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  COACHING SYSTEM (Python, FastAPI)                                  │
│  → Receives NL instructions from players                            │
│  → Updates agent strategy parameters                                │
│  → Publishes config changes to Redis: "config:update"               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  IDLE ENGINE (Python, background worker)                            │
│  → Calculates offline earnings every minute                         │
│  → Applies boosts, updates player resources                         │
│  → Publishes state to Redis: "state:player:{id}"                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  GAME FRONTEND (Next.js + Three.js)                                 │
│  → WebSocket connection to Redis for real-time updates              │
│  → Renders 3D space map, fleet battles, command center              │
│  → Shows live trades as space combat animations                     │
│  → Micro-transaction shop (boosts, gacha, battle pass)              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BLOCKCHAIN (Arc L2 — Circle stack)                                 │
│  → CrusadeEscrow: tournament entry fees + prize distribution        │
│  → AgentRegistry: NFT ownership of agents                           │
│  → DiscipleNFT: fleet avatar ownership                              │
│  → BoostToken: time accelerator NFTs                                │
│  → FleetGacha: verifiable random fleet drops                        │
│  → Treasury: protocol fee collection                                │
│  → Circle Wallet: USDC deposits/withdrawals/CCTP                    │
│  → Paymaster: gasless transactions for players                      │
└─────────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Signal Aggregator
- `GET /health` — service status
- `GET /signals/latest?source=&asset=` — latest signals
- `WS /ws/signals` — real-time signal stream

### Disciple Agents
- `POST /agent/{id}/trade` — submit trade
- `GET /agent/{id}/performance` — PnL, win rate, etc.
- `WS /ws/agent/{id}` — agent status stream

### Coaching System
- `POST /coach` — apply coaching instruction
- `GET /suggest/{agent_id}` — get coaching suggestions
- `GET /history/{agent_id}` — coaching history

### Idle Engine
- `GET /player/{id}/state` — current resources, levels
- `POST /player/{id}/boost` — activate boost
- `GET /player/{id}/offline-catchup` — calculate offline earnings

### Game Frontend
- `GET /api/shop` — available items
- `POST /api/purchase` — buy item (USDC)
- `POST /api/gacha/pull` — gacha pull
- `GET /api/battle-pass` — current progress

### Marketplace
- `GET /api/marketplace/listings` — browse agents
- `POST /api/marketplace/buy` — purchase agent
- `POST /api/marketplace/rent` — rent agent
- `POST /api/marketplace/list` — list your agent

## Environment Variables

```bash
# Redis
REDIS_URL=redis://localhost:6379

# Circle/Arc
ARC_RPC_URL=https://rpc-testnet.arc.network
ARC_CHAIN_ID=4242
USDC_CONTRACT=0x...
CIRCLE_API_KEY=...
PAYMASTER_ENDPOINT=...

# Meshy
MESHY_API_KEY=msy_...

# OpenAI (for coaching LLM)
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://...
```

## Startup Sequence

1. Start Redis: `redis-server`
2. Start Signal Aggregator: `python -m signal-aggregator.main`
3. Start Idle Engine: `python -m idle-engine.calculator`
4. Start Coaching API: `uvicorn agent-coaching.api:app --port 8001`
5. Start Game Frontend: `cd game-frontend && npm run dev`
6. Deploy contracts: `npx hardhat run scripts/deploy.ts --network arcTestnet`
