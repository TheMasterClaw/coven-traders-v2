/**
 * Orchestrator — End-to-End Wiring
 * 
 * Connects all subsystems:
 * Signal Aggregator → Disciple Agents → Game Engine → Blockchain
 * 
 * Flow:
 * 1. SignalAggregator polls all sources, normalizes, publishes to Redis
 * 2. Orchestrator subscribes to Redis, routes signals to relevant disciples
 * 3. Disciples evaluate signals against their coaching strategy
 * 4. Valid trades are submitted to Circle wallet → Arc blockchain
 * 5. Game engine syncs earnings, updates player state
 * 6. Frontend receives real-time updates via WebSocket
 */

import { Redis } from "ioredis";
import { CoachingEngine } from "../agent-coaching/engine";
import { AgentMarketplace } from "../agent-marketplace/marketplace";

interface Signal {
  source: string;
  asset: string;
  direction: "bull" | "bear" | "neutral";
  confidence: number;
  timestamp: string;
  expiry: string;
  metadata: Record<string, any>;
}

interface TradeDecision {
  agentId: string;
  playerId: string;
  action: "long" | "short" | "close" | "hold";
  asset: string;
  size: string;
  leverage: number;
  stopLoss?: string;
  takeProfit?: string;
  reason: string;
  signalId: string;
}

export class Orchestrator {
  private redis: Redis;
  private coaching: CoachingEngine;
  private marketplace: AgentMarketplace;
  private isRunning: boolean = false;
  private signalChannel = "signals:raw";
  private tradeChannel = "trades:pending";

  constructor(redisUrl: string) {
    this.redis = new Redis(redisUrl);
    this.coaching = new CoachingEngine();
    this.marketplace = new AgentMarketplace();
  }

  async start(): Promise<void> {
    this.isRunning = true;
    console.log("[Orchestrator] Starting...");

    // Subscribe to signal feed
    this.redis.subscribe(this.signalChannel);
    this.redis.on("message", (channel, message) => {
      if (channel === this.signalChannel) {
        this.handleSignal(JSON.parse(message));
      }
    });

    // Start trade execution loop
    this.startTradeExecutionLoop();

    console.log("[Orchestrator] Running. Waiting for signals...");
  }

  async stop(): Promise<void> {
    this.isRunning = false;
    await this.redis.quit();
    console.log("[Orchestrator] Stopped.");
  }

  /**
   * Handle incoming signal — route to all relevant agents
   */
  private async handleSignal(signal: Signal): Promise<void> {
    console.log(`[Orchestrator] Signal: ${signal.source} → ${signal.asset} ${signal.direction} (${signal.confidence})`);

    // Find all active agents that care about this asset
    const allAgents = this.getAllActiveAgents();
    
    for (const agent of allAgents) {
      const profile = this.coaching.getProfile(agent.playerId, agent.id);
      if (!profile) continue;

      // Check if agent trades this asset
      if (profile.excludedAssets.includes(signal.asset)) continue;
      if (profile.preferredAssets.length > 0 && !profile.preferredAssets.includes(signal.asset)) continue;

      // Evaluate signal against coaching rules
      const decision = this.evaluateSignal(agent, profile, signal);
      
      if (decision && decision.action !== "hold") {
        // Queue trade for execution
        await this.redis.publish(this.tradeChannel, JSON.stringify(decision));
        console.log(`[Orchestrator] Trade queued: ${agent.name} → ${decision.action} ${decision.asset}`);
      }
    }
  }

  /**
   * Evaluate a signal against an agent's coaching strategy
   */
  private evaluateSignal(agent: any, profile: any, signal: Signal): TradeDecision | null {
    const strategy = this.coaching.compileStrategy(agent.playerId, agent.id);
    const rules = (strategy as any).rules || [];

    // Default: follow signal direction if confidence > 0.7
    let action: "long" | "short" | "close" | "hold" = "hold";
    
    if (signal.confidence >= 0.7) {
      if (signal.direction === "bull") action = "long";
      else if (signal.direction === "bear") action = "short";
    }

    // Apply coaching rules
    for (const rule of rules) {
      if (!rule.active) continue;
      
      // Simple rule evaluation (expandable)
      if (rule.condition.includes("price increase") && signal.direction === "bull") {
        action = "long";
      }
      if (rule.condition.includes("price decrease") && signal.direction === "bear") {
        action = "short";
      }
      if (rule.condition.includes("funding_rate < 0") && signal.metadata?.fundingRate < 0) {
        action = "long";
      }
    }

    if (action === "hold") return null;

    // Calculate position size based on risk tolerance
    const maxSize = parseFloat(profile.maxPositionSize);
    const size = (maxSize * signal.confidence).toFixed(6);

    return {
      agentId: agent.id,
      playerId: agent.playerId,
      action,
      asset: signal.asset,
      size,
      leverage: profile.maxLeverage,
      stopLoss: profile.stopLossPercent.toString(),
      takeProfit: profile.takeProfitPercent.toString(),
      reason: `${signal.source} signal: ${signal.direction} (${signal.confidence})`,
      signalId: signal.timestamp,
    };
  }

  /**
   * Trade execution loop — processes pending trades
   */
  private startTradeExecutionLoop(): void {
    const loop = async () => {
      while (this.isRunning) {
        try {
          const tradeJson = await this.redis.lpop("trades:queue");
          if (tradeJson) {
            const trade: TradeDecision = JSON.parse(tradeJson);
            await this.executeTrade(trade);
          }
        } catch (e) {
          console.error("[Orchestrator] Trade execution error:", e);
        }
        await new Promise((r) => setTimeout(r, 1000));
      }
    };
    loop();
  }

  /**
   * Execute a trade via Circle wallet on Arc
   */
  private async executeTrade(trade: TradeDecision): Promise<void> {
    console.log(`[Orchestrator] Executing trade: ${trade.action} ${trade.asset} x${trade.leverage}`);

    // In production:
    // 1. Get player's Circle wallet
    // 2. Call perp DEX contract on Arc via Circle's contract execution API
    // 3. Record trade on-chain
    // 4. Update game state with earnings/losses

    // Mock execution for now
    const mockProfit = (Math.random() - 0.3) * parseFloat(trade.size) * trade.leverage;
    const profitStr = mockProfit.toFixed(6);

    // Update agent earnings
    this.marketplace.updateAgentEarnings(trade.agentId, profitStr);

    // Publish game state update
    await this.redis.publish(`player:${trade.playerId}:updates`, JSON.stringify({
      type: "trade_executed",
      trade,
      profit: profitStr,
      timestamp: new Date().toISOString(),
    }));

    console.log(`[Orchestrator] Trade complete: profit=${profitStr} USDC`);
  }

  private getAllActiveAgents(): any[] {
    // In production: query from database
    // Mock for now
    return [];
  }

  // --- Health / Metrics ---

  async getMetrics(): Promise<object> {
    const signalCount = await this.redis.get("metrics:signals:total") || "0";
    const tradeCount = await this.redis.get("metrics:trades:total") || "0";
    const profitTotal = await this.redis.get("metrics:profit:total") || "0";

    return {
      signalsProcessed: parseInt(signalCount),
      tradesExecuted: parseInt(tradeCount),
      totalProfit: parseFloat(profitTotal).toFixed(2),
      activeAgents: this.getAllActiveAgents().length,
      uptime: process.uptime(),
    };
  }
}

export default Orchestrator;
