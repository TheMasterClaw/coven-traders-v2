/**
 * Agent Marketplace
 * 
 * Players can:
 * 1. Deploy their own AI disciple agents (bring-your-own-agent)
 * 2. Browse and rent pre-built agents from other players
 * 3. Sell their trained agents on the open market
 * 4. Connect external agents via API keys
 * 
 * All transactions in USDC. Platform takes 5% commission.
 */

export interface AgentListing {
  id: string;
  sellerId: string;
  sellerName: string;
  name: string;
  description: string;
  specialization: string;
  tier: "common" | "rare" | "epic" | "legendary";
  power: number;
  speed: number;
  luck: number;
  defense: number;
  winRate: number;
  totalTrades: number;
  profitGenerated: string;
  price: string;
  currency: "USDC";
  isRental: boolean;
  rentalPricePerDay?: string;
  meshyModelUrl?: string;
  strategySummary: string;
  createdAt: string;
}

export interface DeployedAgent {
  id: string;
  playerId: string;
  name: string;
  specialization: string;
  tier: string;
  apiEndpoint?: string;
  apiKey?: string;
  isExternal: boolean;
  status: "idle" | "active" | "paused" | "error";
  earnings: string;
  lastTradeAt?: string;
  config: object;
}

const PLATFORM_FEE_BP = 500; // 5%

export class AgentMarketplace {
  private listings: Map<string, AgentListing> = new Map();
  private deployed: Map<string, DeployedAgent> = new Map();
  private playerAgents: Map<string, Set<string>> = new Map(); // playerId -> agentIds

  // --- Listing Management ---

  listAgent(listing: Omit<AgentListing, "id" | "createdAt">): AgentListing {
    const full: AgentListing = {
      ...listing,
      id: `listing_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      createdAt: new Date().toISOString(),
    };
    this.listings.set(full.id, full);
    return full;
  }

  delistAgent(listingId: string): boolean {
    return this.listings.delete(listingId);
  }

  getListings(filters?: {
    specialization?: string;
    tier?: string;
    maxPrice?: string;
    isRental?: boolean;
  }): AgentListing[] {
    let results = Array.from(this.listings.values());
    
    if (filters?.specialization) {
      results = results.filter((l) => l.specialization === filters.specialization);
    }
    if (filters?.tier) {
      results = results.filter((l) => l.tier === filters.tier);
    }
    if (filters?.maxPrice) {
      results = results.filter((l) => parseFloat(l.price) <= parseFloat(filters.maxPrice!));
    }
    if (filters?.isRental !== undefined) {
      results = results.filter((l) => l.isRental === filters.isRental);
    }
    
    // Sort by profit generated (descending)
    return results.sort((a, b) => parseFloat(b.profitGenerated) - parseFloat(a.profitGenerated));
  }

  getListing(listingId: string): AgentListing | undefined {
    return this.listings.get(listingId);
  }

  // --- Purchase / Rental ---

  async purchaseAgent(buyerId: string, listingId: string): Promise<DeployedAgent> {
    const listing = this.listings.get(listingId);
    if (!listing) throw new Error("Listing not found");
    if (listing.isRental) throw new Error("This is a rental listing");

    // Calculate fees
    const price = parseFloat(listing.price);
    const platformFee = (price * PLATFORM_FEE_BP) / 10000;
    const sellerReceives = price - platformFee;

    // In real implementation: transfer USDC via Circle
    console.log(`Purchase: buyer=${buyerId}, seller=${listing.sellerId}, price=${price}, fee=${platformFee}`);

    // Create deployed agent for buyer
    const agent = this.deployAgent({
      playerId: buyerId,
      name: listing.name,
      specialization: listing.specialization,
      tier: listing.tier,
      isExternal: false,
      status: "idle",
      earnings: "0",
      config: {},
    });

    // Remove from marketplace
    this.listings.delete(listingId);

    return agent;
  }

  async rentAgent(renterId: string, listingId: string, days: number): Promise<DeployedAgent> {
    const listing = this.listings.get(listingId);
    if (!listing) throw new Error("Listing not found");
    if (!listing.isRental || !listing.rentalPricePerDay) throw new Error("Not available for rent");

    const totalPrice = parseFloat(listing.rentalPricePerDay) * days;
    const platformFee = (totalPrice * PLATFORM_FEE_BP) / 10000;

    console.log(`Rental: renter=${renterId}, days=${days}, total=${totalPrice}, fee=${platformFee}`);

    return this.deployAgent({
      playerId: renterId,
      name: `${listing.name} (Rental)`,
      specialization: listing.specialization,
      tier: listing.tier,
      isExternal: false,
      status: "idle",
      earnings: "0",
      config: { rentalExpiry: Date.now() + days * 86400000 },
    });
  }

  // --- Deploy / Connect External Agents ---

  deployAgent(config: Omit<DeployedAgent, "id">): DeployedAgent {
    const agent: DeployedAgent = {
      ...config,
      id: `agent_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    };
    
    this.deployed.set(agent.id, agent);
    
    if (!this.playerAgents.has(config.playerId)) {
      this.playerAgents.set(config.playerId, new Set());
    }
    this.playerAgents.get(config.playerId)!.add(agent.id);
    
    return agent;
  }

  connectExternalAgent(
    playerId: string,
    name: string,
    specialization: string,
    apiEndpoint: string,
    apiKey: string
  ): DeployedAgent {
    return this.deployAgent({
      playerId,
      name,
      specialization,
      tier: "custom",
      apiEndpoint,
      apiKey,
      isExternal: true,
      status: "idle",
      earnings: "0",
      config: { connectedAt: new Date().toISOString() },
    });
  }

  getPlayerAgents(playerId: string): DeployedAgent[] {
    const ids = this.playerAgents.get(playerId);
    if (!ids) return [];
    return Array.from(ids)
      .map((id) => this.deployed.get(id))
      .filter((a): a is DeployedAgent => a !== undefined);
  }

  getAgent(agentId: string): DeployedAgent | undefined {
    return this.deployed.get(agentId);
  }

  updateAgentStatus(agentId: string, status: DeployedAgent["status"]): void {
    const agent = this.deployed.get(agentId);
    if (agent) {
      agent.status = status;
    }
  }

  updateAgentEarnings(agentId: string, earnings: string): void {
    const agent = this.deployed.get(agentId);
    if (agent) {
      agent.earnings = earnings;
      agent.lastTradeAt = new Date().toISOString();
    }
  }

  pauseAgent(agentId: string): void {
    this.updateAgentStatus(agentId, "paused");
  }

  resumeAgent(agentId: string): void {
    this.updateAgentStatus(agentId, "active");
  }

  // --- Coaching Integration ---

  applyCoaching(agentId: string, strategyConfig: object): void {
    const agent = this.deployed.get(agentId);
    if (!agent) throw new Error("Agent not found");
    
    agent.config = {
      ...agent.config,
      strategy: strategyConfig,
      strategyUpdatedAt: new Date().toISOString(),
    };
    
    // If external, push strategy to their endpoint
    if (agent.isExternal && agent.apiEndpoint) {
      this.pushStrategyToExternal(agent, strategyConfig);
    }
  }

  private async pushStrategyToExternal(agent: DeployedAgent, strategy: object): Promise<void> {
    if (!agent.apiEndpoint || !agent.apiKey) return;
    
    try {
      const res = await fetch(`${agent.apiEndpoint}/strategy`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": agent.apiKey,
        },
        body: JSON.stringify(strategy),
      });
      
      if (!res.ok) {
        console.error(`Failed to push strategy to ${agent.name}:`, await res.text());
        agent.status = "error";
      }
    } catch (e) {
      console.error(`Error pushing strategy to ${agent.name}:`, e);
      agent.status = "error";
    }
  }

  // --- Stats ---

  getMarketplaceStats(): object {
    const listings = Array.from(this.listings.values());
    return {
      totalListings: listings.length,
      totalVolume: listings.reduce((sum, l) => sum + parseFloat(l.profitGenerated), 0).toFixed(2),
      avgPrice: listings.length > 0
        ? (listings.reduce((sum, l) => sum + parseFloat(l.price), 0) / listings.length).toFixed(2)
        : "0",
      byTier: {
        common: listings.filter((l) => l.tier === "common").length,
        rare: listings.filter((l) => l.tier === "rare").length,
        epic: listings.filter((l) => l.tier === "epic").length,
        legendary: listings.filter((l) => l.tier === "legendary").length,
      },
    };
  }
}

export default AgentMarketplace;
