"use client";

import { useState } from "react";
import { GameAPI } from "@/lib/api";

interface Fleet {
  id: string;
  name: string;
  specialization: string;
  tier: "common" | "rare" | "epic" | "legendary" | "mythic";
  power: number;
  speed: number;
  luck: number;
  defense: number;
  status: "idle" | "mining" | "trading" | "battling";
  earningsPerSecond: string;
  sectorId?: string;
  level: number;
  xp: number;
}

interface FleetManagerProps {
  playerId: string;
  api: GameAPI;
}

const TIER_COLORS: Record<string, string> = {
  common: "text-gray-400",
  rare: "text-blue-400",
  epic: "text-purple-400",
  legendary: "text-orange-400",
  mythic: "text-red-400",
};

const TIER_BG: Record<string, string> = {
  common: "bg-gray-900/50 border-gray-700",
  rare: "bg-blue-900/20 border-blue-700",
  epic: "bg-purple-900/20 border-purple-700",
  legendary: "bg-orange-900/20 border-orange-700",
  mythic: "bg-red-900/20 border-red-700",
};

const MOCK_FLEETS: Fleet[] = [
  { id: "f1", name: "Alpha Vanguard", specialization: "perp_warrior", tier: "rare", power: 120, speed: 85, luck: 40, defense: 60, status: "mining", earningsPerSecond: "0.00045", sectorId: "core_alpha", level: 5, xp: 340 },
  { id: "f2", name: "Beta Oracle", specialization: "oracle_seer", tier: "epic", power: 200, speed: 60, luck: 90, defense: 45, status: "trading", earningsPerSecond: "0.00082", sectorId: "outer_gamma", level: 8, xp: 720 },
  { id: "f3", name: "Gamma Trader", specialization: "market_maker", tier: "common", power: 80, speed: 70, luck: 55, defense: 50, status: "idle", earningsPerSecond: "0.00021", level: 3, xp: 120 },
  { id: "f4", name: "Delta Hunter", specialization: "signal_hunter", tier: "legendary", power: 350, speed: 95, luck: 75, defense: 30, status: "battling", earningsPerSecond: "0.00150", sectorId: "wormhole_epsilon", level: 12, xp: 1500 },
];

export default function FleetManager({ playerId, api }: FleetManagerProps) {
  const [selectedFleet, setSelectedFleet] = useState<Fleet | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("power");

  const filtered = filter === "all"
    ? MOCK_FLEETS
    : MOCK_FLEETS.filter((f) => f.status === filter || f.tier === filter);

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === "power") return b.power - a.power;
    if (sortBy === "speed") return b.speed - a.speed;
    if (sortBy === "luck") return b.luck - a.luck;
    if (sortBy === "earnings") return parseFloat(b.earningsPerSecond) - parseFloat(a.earningsPerSecond);
    return 0;
  });

  const totalPower = MOCK_FLEETS.reduce((sum, f) => sum + f.power, 0);
  const activeFleets = MOCK_FLEETS.filter((f) => f.status !== "idle").length;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white font-mono">FLEET MANAGER</h2>
          <div className="text-xs text-gray-500">{activeFleets}/{MOCK_FLEETS.length} Active · {totalPower} Total Power</div>
        </div>
        <button className="bg-cyan-900/50 hover:bg-cyan-800/50 border border-cyan-600 text-cyan-400 text-xs font-mono py-2 px-4 rounded transition-colors">
          🎲 GACHA PULL
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {[
          { id: "all", label: "All" },
          { id: "idle", label: "Idle" },
          { id: "mining", label: "Mining" },
          { id: "trading", label: "Trading" },
          { id: "battling", label: "Battling" },
        ].map((f) => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
              filter === f.id
                ? "bg-cyan-900/50 border border-cyan-600 text-cyan-400"
                : "bg-gray-800 border border-gray-700 text-gray-400 hover:text-white"
            }`}
          >
            {f.label}
          </button>
        ))}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-gray-400 text-xs font-mono py-1 px-2 rounded ml-auto"
        >
          <option value="power">Sort: Power</option>
          <option value="speed">Sort: Speed</option>
          <option value="luck">Sort: Luck</option>
          <option value="earnings">Sort: Earnings</option>
        </select>
      </div>

      {/* Fleet Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {sorted.map((fleet) => (
          <div
            key={fleet.id}
            onClick={() => setSelectedFleet(fleet)}
            className={`border rounded p-4 space-y-2 cursor-pointer hover:border-gray-500 transition-colors ${TIER_BG[fleet.tier]}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-bold text-white">{fleet.name}</div>
                <div className={`text-[10px] uppercase tracking-wider ${TIER_COLORS[fleet.tier]}`}>
                  {fleet.tier} · Lv.{fleet.level}
                </div>
              </div>
              <div className={`text-xs px-2 py-0.5 rounded ${
                fleet.status === "idle" ? "bg-gray-800 text-gray-400" :
                fleet.status === "mining" ? "bg-green-900/50 text-green-400" :
                fleet.status === "trading" ? "bg-blue-900/50 text-blue-400" :
                "bg-red-900/50 text-red-400"
              }`}>
                {fleet.status.toUpperCase()}
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-2 text-center">
              <div className="bg-black/30 rounded p-1">
                <div className="text-[10px] text-gray-500">PWR</div>
                <div className="text-xs font-mono text-white">{fleet.power}</div>
              </div>
              <div className="bg-black/30 rounded p-1">
                <div className="text-[10px] text-gray-500">SPD</div>
                <div className="text-xs font-mono text-white">{fleet.speed}</div>
              </div>
              <div className="bg-black/30 rounded p-1">
                <div className="text-[10px] text-gray-500">LCK</div>
                <div className="text-xs font-mono text-white">{fleet.luck}</div>
              </div>
              <div className="bg-black/30 rounded p-1">
                <div className="text-[10px] text-gray-500">DEF</div>
                <div className="text-xs font-mono text-white">{fleet.defense}</div>
              </div>
            </div>

            <div className="text-xs text-green-400 font-mono">
              +${parseFloat(fleet.earningsPerSecond).toFixed(6)}/sec
            </div>
          </div>
        ))}
      </div>

      {/* Selected Fleet Detail */}
      {selectedFleet && (
        <div className="bg-black/50 border border-gray-700 rounded p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-lg font-bold text-white">{selectedFleet.name}</div>
              <div className={`text-xs uppercase ${TIER_COLORS[selectedFleet.tier]}`}>{selectedFleet.tier}</div>
            </div>
            <button
              onClick={() => setSelectedFleet(null)}
              className="text-gray-500 hover:text-white text-xs"
            >
              ✕ CLOSE
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button className="bg-purple-900/50 hover:bg-purple-800/50 border border-purple-700 text-purple-400 text-xs font-mono py-2 px-3 rounded transition-colors">
              ⬆️ UPGRADE
            </button>
            <button className="bg-orange-900/50 hover:bg-orange-800/50 border border-orange-700 text-orange-400 text-xs font-mono py-2 px-3 rounded transition-colors">
              🔀 MERGE
            </button>
            <button className="bg-green-900/50 hover:bg-green-800/50 border border-green-700 text-green-400 text-xs font-mono py-2 px-3 rounded transition-colors">
              🚀 DEPLOY
            </button>
            <button className="bg-red-900/50 hover:bg-red-800/50 border border-red-700 text-red-400 text-xs font-mono py-2 px-3 rounded transition-colors">
              ⏹️ RECALL
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
