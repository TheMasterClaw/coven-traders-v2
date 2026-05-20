/**
 * Agent Coaching System
 * 
 * Converts natural language instructions into trading strategy parameters.
 * Uses a lightweight prompt-to-strategy parser that maps user intent
 * to disciple agent behavior without requiring code changes.
 * 
 * Example inputs:
 * - "be aggressive when BTC pumps over 5%"
 * - "only trade ETH perps, max 2x leverage"
 * - "if funding rates go negative, go long immediately"
 * - "never risk more than 1% of portfolio per trade"
 */

export interface StrategyRule {
  id: string;
  condition: string;
  action: string;
  priority: number;
  active: boolean;
  createdAt: string;
}

export interface CoachingProfile {
  playerId: string;
  discipleId: string;
  riskTolerance: "conservative" | "moderate" | "aggressive" | "degen";
  maxLeverage: number;
  maxPositionSize: string;
  preferredAssets: string[];
  excludedAssets: string[];
  rules: StrategyRule[];
  autoCompound: boolean;
  stopLossPercent: number;
  takeProfitPercent: number;
}

const RISK_PROFILES: Record<string, Partial<CoachingProfile>> = {
  conservative: {
    maxLeverage: 2,
    maxPositionSize: "0.05",
    stopLossPercent: 2,
    takeProfitPercent: 5,
    autoCompound: false,
  },
  moderate: {
    maxLeverage: 5,
    maxPositionSize: "0.1",
    stopLossPercent: 5,
    takeProfitPercent: 10,
    autoCompound: true,
  },
  aggressive: {
    maxLeverage: 10,
    maxPositionSize: "0.25",
    stopLossPercent: 10,
    takeProfitPercent: 20,
    autoCompound: true,
  },
  degen: {
    maxLeverage: 50,
    maxPositionSize: "0.5",
    stopLossPercent: 25,
    takeProfitPercent: 50,
    autoCompound: true,
  },
};

export class CoachingEngine {
  private profiles: Map<string, CoachingProfile> = new Map();

  createProfile(playerId: string, discipleId: string, riskTolerance: string): CoachingProfile {
    const preset = RISK_PROFILES[riskTolerance] || RISK_PROFILES.moderate;
    const profile: CoachingProfile = {
      playerId,
      discipleId,
      riskTolerance: riskTolerance as any,
      maxLeverage: preset.maxLeverage!,
      maxPositionSize: preset.maxPositionSize!,
      preferredAssets: ["BTC", "ETH"],
      excludedAssets: [],
      rules: [],
      autoCompound: preset.autoCompound!,
      stopLossPercent: preset.stopLossPercent!,
      takeProfitPercent: preset.takeProfitPercent!,
    };
    this.profiles.set(`${playerId}:${discipleId}`, profile);
    return profile;
  }

  getProfile(playerId: string, discipleId: string): CoachingProfile | undefined {
    return this.profiles.get(`${playerId}:${discipleId}`);
  }

  /**
   * Parse natural language instruction into a structured rule.
   * This is the core magic — no coding required from the player.
   */
  parseInstruction(instruction: string): StrategyRule {
    const lower = instruction.toLowerCase();
    
    // Pattern matching for common trading instructions
    const patterns = [
      {
        regex: /(?:when|if)\s+(.+?)\s+(?:pumps?|goes? up|increases?)\s+(?:by\s+)?(\d+(?:\.\d+)?)%/i,
        action: (matches: RegExpMatchArray) => ({
          condition: `${matches[1].trim()} price increase > ${matches[2]}%`,
          action: "increase_position",
          priority: 5,
        }),
      },
      {
        regex: /(?:when|if)\s+(.+?)\s+(?:dumps?|goes? down|decreases?)\s+(?:by\s+)?(\d+(?:\.\d+)?)%/i,
        action: (matches: RegExpMatchArray) => ({
          condition: `${matches[1].trim()} price decrease > ${matches[2]}%`,
          action: "decrease_position_or_short",
          priority: 5,
        }),
      },
      {
        regex: /only trade\s+(.+)/i,
        action: (matches: RegExpMatchArray) => ({
          condition: "always",
          action: `whitelist_assets:${matches[1].trim()}`,
          priority: 10,
        }),
      },
      {
        regex: /never trade\s+(.+)/i,
        action: (matches: RegExpMatchArray) => ({
          condition: "always",
          action: `blacklist_assets:${matches[1].trim()}`,
          priority: 10,
        }),
      },
      {
        regex: /max(?:imum)?\s+(?:leverage|lev)\s+(?:of\s+)?(\d+)x?/i,
        action: (matches: RegExpMatchArray) => ({
          condition: "always",
          action: `set_max_leverage:${matches[1]}`,
          priority: 10,
        }),
      },
      {
        regex: /(?:stop loss|sl)\s+(?:at\s+)?(\d+(?:\.\d+)?)%/i,
        action: (matches: RegExpMatchArray) => ({
          condition: "always",
          action: `set_stop_loss:${matches[1]}`,
          priority: 10,
        }),
      },
      {
        regex: /(?:take profit|tp)\s+(?:at\s+)?(\d+(?:\.\d+)?)%/i,
        action: (matches: RegExpMatchArray) => ({
          condition: "always",
          action: `set_take_profit:${matches[1]}`,
          priority: 10,
        }),
      },
      {
        regex: /(?:if|when)\s+funding\s+(?:rate\s+)?(?:goes?\s+)?negative/i,
        action: () => ({
          condition: "funding_rate < 0",
          action: "open_long",
          priority: 8,
        }),
      },
      {
        regex: /(?:if|when)\s+open interest\s+(?:spikes?|increases?)/i,
        action: () => ({
          condition: "open_interest_change > 10%",
          action: "follow_trend",
          priority: 6,
        }),
      },
      {
        regex: /dca\s+(?:into\s+)?(.+?)\s+(?:every\s+)?(\d+)\s*(h|hour|d|day)/i,
        action: (matches: RegExpMatchArray) => ({
          condition: `time_interval:${matches[2]}${matches[3].startsWith("h") ? "h" : "d"}`,
          action: `dca_buy:${matches[1].trim()}`,
          priority: 4,
        }),
      },
    ];

    for (const pattern of patterns) {
      const matches = lower.match(pattern.regex);
      if (matches) {
        const parsed = pattern.action(matches);
        return {
          id: `rule_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
          condition: parsed.condition,
          action: parsed.action,
          priority: parsed.priority,
          active: true,
          createdAt: new Date().toISOString(),
        };
      }
    }

    // Fallback: store as free-text rule for LLM interpretation
    return {
      id: `rule_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      condition: "natural_language",
      action: instruction,
      priority: 3,
      active: true,
      createdAt: new Date().toISOString(),
    };
  }

  addRule(playerId: string, discipleId: string, instruction: string): StrategyRule {
    const profile = this.getProfile(playerId, discipleId);
    if (!profile) {
      throw new Error("Profile not found. Create one first.");
    }

    const rule = this.parseInstruction(instruction);
    profile.rules.push(rule);
    
    // Sort by priority (highest first)
    profile.rules.sort((a, b) => b.priority - a.priority);
    
    return rule;
  }

  removeRule(playerId: string, discipleId: string, ruleId: string): boolean {
    const profile = this.getProfile(playerId, discipleId);
    if (!profile) return false;
    
    const idx = profile.rules.findIndex((r) => r.id === ruleId);
    if (idx >= 0) {
      profile.rules.splice(idx, 1);
      return true;
    }
    return false;
  }

  toggleRule(playerId: string, discipleId: string, ruleId: string): boolean {
    const profile = this.getProfile(playerId, discipleId);
    if (!profile) return false;
    
    const rule = profile.rules.find((r) => r.id === ruleId);
    if (rule) {
      rule.active = !rule.active;
      return rule.active;
    }
    return false;
  }

  /**
   * Compile all active rules into a strategy config that the disciple agent can execute.
   */
  compileStrategy(playerId: string, discipleId: string): object {
    const profile = this.getProfile(playerId, discipleId);
    if (!profile) {
      throw new Error("Profile not found");
    }

    const activeRules = profile.rules.filter((r) => r.active);
    
    return {
      riskTolerance: profile.riskTolerance,
      maxLeverage: profile.maxLeverage,
      maxPositionSize: profile.maxPositionSize,
      preferredAssets: profile.preferredAssets,
      excludedAssets: profile.excludedAssets,
      autoCompound: profile.autoCompound,
      stopLossPercent: profile.stopLossPercent,
      takeProfitPercent: profile.takeProfitPercent,
      rules: activeRules.map((r) => ({
        condition: r.condition,
        action: r.action,
        priority: r.priority,
      })),
      compiledAt: new Date().toISOString(),
    };
  }

  /**
   * Get a human-readable summary of the current strategy.
   */
  summarizeStrategy(playerId: string, discipleId: string): string {
    const profile = this.getProfile(playerId, discipleId);
    if (!profile) return "No strategy configured.";

    const lines = [
      `Risk Profile: ${profile.riskTolerance.toUpperCase()}`,
      `Max Leverage: ${profile.maxLeverage}x`,
      `Position Size: ≤${profile.maxPositionSize} of portfolio`,
      `Stop Loss: ${profile.stopLossPercent}%`,
      `Take Profit: ${profile.takeProfitPercent}%`,
      `Auto-Compound: ${profile.autoCompound ? "ON" : "OFF"}`,
      ``,
      `Active Rules (${profile.rules.filter((r) => r.active).length}/${profile.rules.length}):`,
    ];

    for (const rule of profile.rules.filter((r) => r.active)) {
      lines.push(`  [P${rule.priority}] ${rule.condition} → ${rule.action}`);
    }

    return lines.join("\n");
  }
}

export default CoachingEngine;
