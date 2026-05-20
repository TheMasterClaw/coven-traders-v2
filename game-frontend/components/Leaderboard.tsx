"use client";

import { useState } from "react";

interface Leader {
  rank: number;
  name: string;
  fleet: string;
  profit: number;
  winRate: number;
  trades: number;
  isMe?: boolean;
}

const MOCK_LEADERS: Leader[] = [
  { rank: 1, name: "VoidWalker", fleet: "Shadow Fleet", profit: 12450, winRate: 78, trades: 342 },
  { rank: 2, name: "NebulaKing", fleet: "Starborn", profit: 11200, winRate: 71, trades: 289 },
  { rank: 3, name: "CryptoClaw", fleet: "Diamond Hands", profit: 9800, winRate: 65, trades: 410 },
  { rank: 4, name: "ArcTrader", fleet: "CCTP Express", profit: 8450, winRate: 62, trades: 198 },
  { rank: 5, name: "MasterClaw", fleet: "🐾 Disciples", profit: 7200, winRate: 58, trades: 156, isMe: true },
  { rank: 6, name: "SignalHunter", fleet: "Alpha Seekers", profit: 6100, winRate: 55, trades: 267 },
  { rank: 7, name: "YieldFarmer", fleet: "DeFi Drones", profit: 5400, winRate: 52, trades: 389 },
  { rank: 8, name: "PerpWarrior", fleet: "Liquidation Squad", profit: 4800, winRate: 49, trades: 512 },
  { rank: 9, name: "HODLer", fleet: "Forever Hold", profit: 3200, winRate: 88, trades: 45 },
  { rank: 10, name: "DayTrader", fleet: "Quick Flip", profit: 2100, winRate: 42, trades: 892 },
];

export default function Leaderboard() {
  const [sortBy, setSortBy] = useState<"profit" | "winRate" | "trades">("profit");

  const sorted = [...MOCK_LEADERS].sort((a, b) => b[sortBy] - a[sortBy]);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-500 uppercase tracking-wider">Season 1 Leaderboard</div>
        <div className="flex gap-1">
          {(["profit", "winRate", "trades"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSortBy(s)}
              className={`text-[10px] px-2 py-1 rounded capitalize ${
                sortBy === s ? "bg-cyan-900 text-cyan-400" : "bg-gray-800 text-gray-500"
              }`}
            >
              {s === "winRate" ? "Win %" : s}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-1">
        {sorted.map((l) => (
          <div
            key={l.rank}
            className={`flex items-center gap-3 p-2 rounded ${
              l.isMe ? "bg-cyan-950/30 border border-cyan-800" : "bg-black/20"
            }`}
          >
            <div className={`w-6 text-center text-sm font-bold ${
              l.rank <= 3 ? "text-yellow-400" : "text-gray-500"
            }`}>
              {l.rank <= 3 ? ["🥇", "🥈", "🥉"][l.rank - 1] : l.rank}
            </div>
            <div className="flex-1">
              <div className="text-sm font-bold">{l.name} {l.isMe && "(You)"}</div>
              <div className="text-[10px] text-gray-500">{l.fleet}</div>
            </div>
            <div className="text-right">
              <div className="text-sm font-mono text-green-400">+${l.profit.toLocaleString()}</div>
              <div className="text-[10px] text-gray-500">
                {l.winRate}% WR · {l.trades} trades
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
