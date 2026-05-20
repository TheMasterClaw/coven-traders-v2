/**
 * REST API client for game backend
 * 
 * Endpoints:
 * - POST /api/auth/connect → Connect wallet
 * - GET /api/player/{id} → Get player state
 * - POST /api/player/sync → Sync offline earnings
 * - GET /api/fleets → List available fleets
 * - POST /api/fleets/gacha → Pull random fleet
 * - GET /api/sectors → List sectors
 * - GET /api/leaderboard → Current rankings
 * - POST /api/crusades/{id}/enter → Enter crusade
 * - GET /api/shop/items → Shop catalog
 * - POST /api/shop/purchase → Buy item
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class GameAPI {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || API_BASE;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request(path: string, options: RequestInit = {}): Promise<any> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...options.headers as Record<string, string>,
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`API error ${res.status}: ${err}`);
    }

    return res.json();
  }

  async connectWallet(walletAddress: string, signature: string): Promise<{ token: string; player: any }> {
    return this.request("/api/auth/connect", {
      method: "POST",
      body: JSON.stringify({ walletAddress, signature }),
    });
  }

  async getPlayerState(playerId: string): Promise<any> {
    return this.request(`/api/player/${playerId}`);
  }

  async syncEarnings(playerId: string): Promise<{ earnings: string; breakdown: any }> {
    return this.request(`/api/player/${playerId}/sync`, { method: "POST" });
  }

  async getFleets(playerId: string): Promise<any[]> {
    return this.request(`/api/player/${playerId}/fleets`);
  }

  async gachaPull(playerId: string, packType: string): Promise<any> {
    return this.request("/api/fleets/gacha", {
      method: "POST",
      body: JSON.stringify({ playerId, packType }),
    });
  }

  async getSectors(): Promise<any[]> {
    return this.request("/api/sectors");
  }

  async getLeaderboard(season?: string): Promise<any[]> {
    const qs = season ? `?season=${season}` : "";
    return this.request(`/api/leaderboard${qs}`);
  }

  async enterCrusade(playerId: string, crusadeId: number): Promise<any> {
    return this.request(`/api/crusades/${crusadeId}/enter`, {
      method: "POST",
      body: JSON.stringify({ playerId }),
    });
  }

  async getShopItems(): Promise<any[]> {
    return this.request("/api/shop/items");
  }

  async purchaseItem(playerId: string, itemId: string, quantity: number = 1): Promise<any> {
    return this.request("/api/shop/purchase", {
      method: "POST",
      body: JSON.stringify({ playerId, itemId, quantity }),
    });
  }

  async getActiveSignals(): Promise<any[]> {
    return this.request("/api/signals");
  }
}

export default GameAPI;
