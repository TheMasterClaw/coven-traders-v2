"use client";

import { useState } from "react";

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
  rarity: "common" | "rare" | "epic" | "legendary";
  progress: number;
  max: number;
}

const MOCK_ACHIEVEMENTS: Achievement[] = [
  { id: "first_trade", name: "First Blood", description: "Execute your first trade", icon: "🩸", unlocked: true, rarity: "common", progress: 1, max: 1 },
  { id: "profit_100", name: "Centurion", description: "Earn $100 in profit", icon: "💰", unlocked: true, rarity: "common", progress: 100, max: 100 },
  { id: "deploy_10", name: "Fleet Commander", description: "Deploy 10 disciples", icon: "🚀", unlocked: false, rarity: "rare", progress: 7, max: 10 },
  { id: "win_streak_5", name: "Hot Streak", description: "5 profitable trades in a row", icon: "🔥", unlocked: false, rarity: "rare", progress: 3, max: 5 },
  { id: "hodl_24h", name: "Diamond Hands", description: "Hold a position for 24 hours", icon: "💎", unlocked: false, rarity: "epic", progress: 18, max: 24 },
  { id: "top_10", name: "Galactic Legend", description: "Reach top 10 on leaderboard", icon: "👑", unlocked: false, rarity: "legendary", progress: 0, max: 1 },
];

const RARITY_COLORS = {
  common: "border-gray-600 bg-gray-900",
  rare: "border-blue-600 bg-blue-950",
  epic: "border-purple-600 bg-purple-950",
  legendary: "border-yellow-600 bg-yellow-950",
};

export default function Achievements() {
  const [filter, setFilter] = useState<"all" | "unlocked" | "locked">("all");

  const filtered = MOCK_ACHIEVEMENTS.filter((a) => {
    if (filter === "unlocked") return a.unlocked;
    if (filter === "locked") return !a.unlocked;
    return true;
  });

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-500 uppercase tracking-wider">Achievements</div>
        <div className="flex gap-1">
          {(["all", "unlocked", "locked"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-[10px] px-2 py-1 rounded capitalize ${
                filter === f ? "bg-cyan-900 text-cyan-400" : "bg-gray-800 text-gray-500"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2">
        {filtered.map((a) => (
          <div
            key={a.id}
            className={`border rounded-lg p-3 flex items-center gap-3 ${
              a.unlocked ? RARITY_COLORS[a.rarity] : "border-gray-800 bg-black/30 opacity-50"
            }`}
          >
            <div className="text-2xl">{a.icon}</div>
            <div className="flex-1">
              <div className="text-sm font-bold">{a.name}</div>
              <div className="text-xs text-gray-500">{a.description}</div>
              <div className="mt-1 h-1 bg-gray-800 rounded-full">
                <div
                  className="h-full bg-cyan-500 rounded-full transition-all"
                  style={{ width: `${(a.progress / a.max) * 100}%` }}
                />
              </div>
              <div className="text-[10px] text-gray-600 mt-0.5">
                {a.progress}/{a.max} · {a.rarity}
              </div>
            </div>
            {a.unlocked && <div className="text-green-400 text-xs">✓</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
