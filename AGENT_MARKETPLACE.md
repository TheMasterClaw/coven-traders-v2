# AGENT MARKETPLACE — Coven Traders

## Overview
Users can deploy their own AI trading agents, connect them to the game, and either use them personally or rent/sell them to other players.

## Architecture

### Agent Registry Contract
- `registerAgent(bytes32 agentId, address owner, string metadataURI)`
- `updateAgentConfig(bytes32 agentId, bytes config)`
- `setAgentForSale(bytes32 agentId, uint256 price)`
- `setAgentForRent(bytes32 agentId, uint256 pricePerDay)`
- `purchaseAgent(bytes32 agentId)`
- `rentAgent(bytes32 agentId, uint256 days)`

### Agent Connector (Backend)
- WebSocket endpoint for agents to connect
- Heartbeat monitoring (agent health)
- Trade execution relay to Circle/Arc
- Performance tracking (PnL, Sharpe, win rate)

### Agent SDK
- Python package: `pip install coven-agent`
- Base class: `CovenAgent` with hooks for:
  - `on_signal(signal)` — receive trading signals
  - `on_market_data(data)` — receive price updates
  - `execute_trade(trade)` — submit trade to game
  - `get_status()` — return agent health/performance
- Example strategies included

## User Flow
1. User writes agent strategy in Python
2. Deploys agent via SDK or web UI
3. Agent connects to game via WebSocket
4. Game visualizes agent as a drone fleet
5. Agent trades real USDC based on signals
6. User can coach agent via natural language
7. User can list agent on marketplace

## Revenue
- 2.5% commission on agent sales
- 5% commission on agent rentals
- Premium SDK features: $9.99/mo
