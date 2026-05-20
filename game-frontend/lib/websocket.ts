/**
 * WebSocket client for real-time game state synchronization
 * 
 * Connects to the idle engine backend for:
 * - Live earnings updates
 * - Fleet status changes
 * - Battle events
 * - Signal feed
 * - Leaderboard updates
 */

export interface GameState {
  playerId: string;
  walletAddress: string;
  commandCenter: {
    level: number;
    xp: number;
    xpToNext: number;
    totalEarnings: string;
    fleetPower: number;
  };
  fleets: Fleet[];
  activeBoosts: Boost[];
  currentSector: string;
  lastSync: number;
}

export interface Fleet {
  id: string;
  name: string;
  specialization: string;
  tier: string;
  power: number;
  speed: number;
  luck: number;
  defense: number;
  status: "idle" | "mining" | "trading" | "battling";
  earningsPerSecond: string;
}

export interface Boost {
  typeId: string;
  name: string;
  multiplier: number;
  expiry: number;
}

export interface SignalEvent {
  source: string;
  asset: string;
  direction: "bull" | "bear" | "neutral";
  confidence: number;
  timestamp: string;
}

export class GameWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number = 3000;
  private maxReconnects: number = 10;
  private reconnectCount: number = 0;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private pingInterval: NodeJS.Timeout | null = null;

  constructor(url: string) {
    this.url = url;
  }

  connect(playerId: string, token: string): void {
    this.ws = new WebSocket(`${this.url}?playerId=${playerId}&token=${token}`);
    
    this.ws.onopen = () => {
      console.log("[WS] Connected");
      this.reconnectCount = 0;
      this.startPing();
      this.emit("connected", {});
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        this.emit(msg.type, msg.payload);
      } catch (e) {
        console.error("[WS] Parse error:", e);
      }
    };

    this.ws.onclose = () => {
      console.log("[WS] Disconnected");
      this.stopPing();
      this.attemptReconnect(playerId, token);
    };

    this.ws.onerror = (err) => {
      console.error("[WS] Error:", err);
    };
  }

  private attemptReconnect(playerId: string, token: string): void {
    if (this.reconnectCount >= this.maxReconnects) {
      console.error("[WS] Max reconnects reached");
      this.emit("disconnected", { permanent: true });
      return;
    }
    this.reconnectCount++;
    setTimeout(() => {
      console.log(`[WS] Reconnecting (${this.reconnectCount}/${this.maxReconnects})...`);
      this.connect(playerId, token);
    }, this.reconnectInterval);
  }

  private startPing(): void {
    this.pingInterval = setInterval(() => {
      this.send({ type: "ping", payload: {} });
    }, 30000);
  }

  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  send(msg: { type: string; payload: any }): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  on(event: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
    return () => this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, data: any): void {
    this.listeners.get(event)?.forEach((cb) => cb(data));
  }

  disconnect(): void {
    this.stopPing();
    this.ws?.close();
    this.ws = null;
  }

  // Convenience methods
  onEarningsUpdate(callback: (earnings: { perSecond: string; total: string }) => void): () => void {
    return this.on("earnings_update", callback);
  }

  onSignal(callback: (signal: SignalEvent) => void): () => void {
    return this.on("signal", callback);
  }

  onBattleStart(callback: (battle: any) => void): () => void {
    return this.on("battle_start", callback);
  }

  onLeaderboardUpdate(callback: (board: any[]) => void): () => void {
    return this.on("leaderboard", callback);
  }

  requestSync(): void {
    this.send({ type: "request_sync", payload: {} });
  }

  activateBoost(boostTypeId: string): void {
    this.send({ type: "activate_boost", payload: { boostTypeId } });
  }

  deployFleet(fleetId: string, sectorId: string): void {
    this.send({ type: "deploy_fleet", payload: { fleetId, sectorId } });
  }
}

export default GameWebSocket;
