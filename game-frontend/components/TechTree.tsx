"use client";

import { useState } from "react";

interface TechNode {
  id: string;
  name: string;
  description: string;
  tier: number;
  maxTier: number;
  cost: string;
  effect: string;
  unlocked: boolean;
  prerequisites: string[];
  category: "combat" | "economy" | "exploration" | "diplomacy";
}

const TECH_TREE: TechNode[] = [
  // Combat
  { id: "weapon_systems", name: "Weapon Systems", description: "Increase fleet attack power by 10% per tier", tier: 0, maxTier: 5, cost: "50", effect: "+10% ATK", unlocked: true, prerequisites: [], category: "combat" },
  { id: "shield_tech", name: "Shield Tech", description: "Increase fleet defense by 10% per tier", tier: 0, maxTier: 5, cost: "50", effect: "+10% DEF", unlocked: true, prerequisites: [], category: "combat" },
  { id: "warp_drive", name: "Warp Drive", description: "Increase fleet speed by 15% per tier", tier: 0, maxTier: 3, cost: "100", effect: "+15% SPD", unlocked: false, prerequisites: ["weapon_systems"], category: "combat" },
  { id: "cloaking", name: "Cloaking Device", description: "Avoid enemy detection in high-risk sectors", tier: 0, maxTier: 1, cost: "500", effect: "Stealth", unlocked: false, prerequisites: ["warp_drive", "shield_tech"], category: "combat" },

  // Economy
  { id: "mining_laser", name: "Mining Laser", description: "Increase mining yield by 12% per tier", tier: 0, maxTier: 5, cost: "40", effect: "+12% Mining", unlocked: true, prerequisites: [], category: "economy" },
  { id: "trade_routes", name: "Trade Routes", description: "Reduce trading fees by 5% per tier", tier: 0, maxTier: 5, cost: "40", effect: "-5% Fees", unlocked: true, prerequisites: [], category: "economy" },
  { id: "auto_pilot", name: "Auto-Pilot", description: "Enable idle earnings for offline fleets", tier: 0, maxTier: 3, cost: "150", effect: "Idle Earnings", unlocked: false, prerequisites: ["mining_laser"], category: "economy" },
  { id: "quantum_trading", name: "Quantum Trading", description: "Execute trades at optimal market moments", tier: 0, maxTier: 1, cost: "750", effect: "+25% Trading", unlocked: false, prerequisites: ["trade_routes", "auto_pilot"], category: "economy" },

  // Exploration
  { id: "scanner_array", name: "Scanner Array", description: "Increase signal detection range by 20% per tier", tier: 0, maxTier: 5, cost: "60", effect: "+20% Range", unlocked: true, prerequisites: [], category: "exploration" },
  { id: "jump_gates", name: "Jump Gates", description: "Unlock access to distant sectors", tier: 0, maxTier: 3, cost: "120", effect: "New Sectors", unlocked: false, prerequisites: ["scanner_array"], category: "exploration" },
  { id: "deep_space", name: "Deep Space Probes", description: "Discover hidden black market locations", tier: 0, maxTier: 1, cost: "600", effect: "Black Markets", unlocked: false, prerequisites: ["jump_gates"], category: "exploration" },

  // Diplomacy
  { id: "negotiation", name: "Negotiation", description: "Better prices in shop and market", tier: 0, maxTier: 5, cost: "45", effect: "-8% Prices", unlocked: true, prerequisites: [], category: "diplomacy" },
  { id: "alliances", name: "Alliances", description: "Form fleet alliances for combined power", tier: 0, maxTier: 3, cost: "200", effect: "Fleet Alliances", unlocked: false, prerequisites: ["negotiation"], category: "diplomacy" },
];

const CATEGORY_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  combat: { bg: "bg-red-900/20", border: "border-red-700", text: "text-red-400" },
  economy: { bg: "bg-green-900/20", border: "border-green-700", text: "text-green-400" },
  exploration: { bg: "bg-blue-900/20", border: "border-blue-700", text: "text-blue-400" },
  diplomacy: { bg: "bg-purple-900/20", border: "border-purple-700", text: "text-purple-400" },
};

export default function TechTree() {
  const [techs, setTechs] = useState<TechNode[]>(TECH_TREE);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [researching, setResearching] = useState<string | null>(null);

  const filtered = selectedCategory === "all"
    ? techs
    : techs.filter((t) => t.category === selectedCategory);

  const handleResearch = async (techId: string) => {
    setResearching(techId);
    // Simulate research delay
    await new Promise((r) => setTimeout(r, 800));
    setTechs((prev) =>
      prev.map((t) =>
        t.id === techId && t.tier < t.maxTier
          ? { ...t, tier: t.tier + 1, unlocked: true }
          : t
      )
    );
    setResearching(null);
  };

  const categories = [
    { id: "all", label: "All Techs", icon: "🔬" },
    { id: "combat", label: "Combat", icon: "⚔️" },
    { id: "economy", label: "Economy", icon: "💰" },
    { id: "exploration", label: "Exploration", icon: "🌌" },
    { id: "diplomacy", label: "Diplomacy", icon: "🤝" },
  ];

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white font-mono">TECH TREE</h2>
          <div className="text-xs text-gray-500">Research upgrades to power up your empire</div>
        </div>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 overflow-x-auto">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`px-3 py-1.5 rounded text-xs font-mono whitespace-nowrap transition-colors ${
              selectedCategory === cat.id
                ? "bg-cyan-900/50 border border-cyan-600 text-cyan-400"
                : "bg-gray-800 border border-gray-700 text-gray-400 hover:text-white"
            }`}
          >
            {cat.icon} {cat.label}
          </button>
        ))}
      </div>

      {/* Tech Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((tech) => {
          const colors = CATEGORY_COLORS[tech.category];
          const canResearch = tech.unlocked && tech.tier < tech.maxTier;
          const isMaxed = tech.tier >= tech.maxTier;

          return (
            <div
              key={tech.id}
              className={`border rounded p-4 space-y-2 ${
                tech.unlocked ? colors.bg : "bg-gray-950/50 border-gray-800 opacity-60"
              } ${colors.border}`}
            >
              <div className="flex items-center justify-between">
                <div className="text-sm font-bold text-white">{tech.name}</div>
                <div className={`text-[10px] px-1.5 py-0.5 rounded ${colors.bg} ${colors.text} border ${colors.border}`}>
                  {tech.tier}/{tech.maxTier}
                </div>
              </div>

              <div className="text-xs text-gray-500">{tech.description}</div>

              {/* Progress bar */}
              <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${colors.text.replace("text", "bg")}`}
                  style={{ width: `${(tech.tier / tech.maxTier) * 100}%` }}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className={`text-xs font-mono ${colors.text}`}>{tech.effect}</div>
                <button
                  onClick={() => canResearch && handleResearch(tech.id)}
                  disabled={!canResearch || researching === tech.id}
                  className={`text-xs font-mono py-1 px-2 rounded transition-colors ${
                    isMaxed
                      ? "bg-gray-800 text-gray-500 cursor-default"
                      : canResearch
                      ? `${colors.bg} ${colors.text} border ${colors.border} hover:brightness-125`
                      : "bg-gray-800 text-gray-600 cursor-not-allowed"
                  }`}
                >
                  {researching === tech.id ? "..." : isMaxed ? "MAXED" : tech.unlocked ? `RESEARCH (${tech.cost})` : "LOCKED"}
                </button>
              </div>

              {tech.prerequisites.length > 0 && !tech.unlocked && (
                <div className="text-[10px] text-gray-600">
                  Requires: {tech.prerequisites.map((p) => TECH_TREE.find((t) => t.id === p)?.name).join(", ")}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
