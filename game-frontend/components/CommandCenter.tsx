"use client";

import { useState, useEffect } from "react";
import { GameWebSocket } from "@/lib/websocket";

interface CommandCenterProps {
  playerId: string;
  wsUrl: string;
  token: string;
}

interface PlayerStats {
  level: number;
  xp: number;
  xpToNext: number;
  totalEarnings: string;
  fleetPower: number;
  activeFleets: number;
  maxFleets: number;
  currentSector: string;
  earningsPerSecond: string;
}

export default function CommandCenter({ playerId, wsUrl, token }: CommandCenterProps) {
  const [stats, setStats] = useState<PlayerStats | null>(null);
  const [liveEarnings, setLiveEarnings] = useState<string>("0");
  const [ws, setWs] = useState<GameWebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socket = new GameWebSocket(wsUrl);
    socket.on("connected", () => setIsConnected(true));
    socket.on("disconnected", () => setIsConnected(false));
    socket.on("state_update", (data) => {
      setStats(data);
      setLiveEarnings(data.totalEarnings);
    });
    socket.on("earnings_update", (data) => {
      setLiveEarnings(data.total);
    });
    socket.connect(playerId, token);
    setWs(socket);

    return () => socket.disconnect();
  }, [playerId, wsUrl, token]);

  const xpPercent = stats ? (stats.xp / stats.xpToNext) * 100 : 0;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white font-mono">COMMAND CENTER</h2>
          <div className="text-xs text-gray-500">Level {stats?.level || 0} · {stats?.activeFleets || 0}/{stats?.maxFleets || 0} Fleets</div>
        </div>
        <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
      </div>

      {/* XP Bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-400">
          <span>XP</span>
          <span>{stats?.xp || 0} / {stats?.xpToNext || 100}</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500"
            style={{ width: `${xpPercent}%` }}
          />
        </div>
      </div>

      {/* Earnings Display */}
      <div className="bg-black/50 border border-gray-800 rounded p-4 space-y-2">
        <div className="text-xs text-gray-500 uppercase tracking-wider">Total Earnings</div>
        <div className="text-3xl font-mono font-bold text-green-400">
          ${parseFloat(liveEarnings).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 6 })}
        </div>
        <div className="text-xs text-gray-500">
          +${parseFloat(stats?.earningsPerSecond || "0").toFixed(6)}/sec
        </div>
      </div>

      {/* Fleet Power */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-black/30 border border-gray-800 rounded p-3">
          <div className="text-xs text-gray-500">Fleet Power</div>
          <div className="text-xl font-mono font-bold text-cyan-400">{stats?.fleetPower || 0}</div>
        </div>
        <div className="bg-black/30 border border-gray-800 rounded p-3">
          <div className="text-xs text-gray-500">Current Sector</div>
          <div className="text-xl font-mono font-bold text-purple-400">{stats?.currentSector || "None"}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => ws?.requestSync()}
          className="flex-1 bg-cyan-900/50 hover:bg-cyan-800/50 border border-cyan-700 text-cyan-400 text-xs font-mono py-2 px-3 rounded transition-colors"
        >
          🔄 SYNC
        </button>
        <button
          className="flex-1 bg-purple-900/50 hover:bg-purple-800/50 border border-purple-700 text-purple-400 text-xs font-mono py-2 px-3 rounded transition-colors"
        >
          ⚡ BOOST
        </button>
        <button
          className="flex-1 bg-green-900/50 hover:bg-green-800/50 border border-green-700 text-green-400 text-xs font-mono py-2 px-3 rounded transition-colors"
        >
          💰 CLAIM
        </button>
      </div>
    </div>
  );
}
