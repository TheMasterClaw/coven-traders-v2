"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import CommandCenter from "@/components/CommandCenter";
import Shop from "@/components/Shop";
import FleetManager from "@/components/FleetManager";
import TechTree from "@/components/TechTree";
import MarketRadar from "@/components/MarketRadar";
import { GameAPI } from "@/lib/api";

const SpaceMap = dynamic(() => import("@/components/SpaceMap"), { ssr: false });

const MOCK_SECTORS = [
  { id: "core_alpha", name: "Alpha Prime", x: 0, y: 0, z: 0, type: "core" as const, yieldMultiplier: 1.0, riskLevel: 1, playerCount: 1240, isLocked: false },
  { id: "core_beta", name: "Beta Station", x: 5, y: 2, z: -3, type: "core" as const, yieldMultiplier: 1.2, riskLevel: 1, playerCount: 890, isLocked: false },
  { id: "outer_gamma", name: "Gamma Belt", x: -8, y: 4, z: 6, type: "outer" as const, yieldMultiplier: 2.5, riskLevel: 4, playerCount: 340, isLocked: false },
  { id: "outer_delta", name: "Delta Void", x: 10, y: -5, z: 8, type: "outer" as const, yieldMultiplier: 3.0, riskLevel: 5, playerCount: 180, isLocked: false },
  { id: "wormhole_epsilon", name: "Epsilon Gate", x: -5, y: -8, z: -5, type: "wormhole" as const, yieldMultiplier: 4.0, riskLevel: 3, playerCount: 420, isLocked: false },
  { id: "black_zeta", name: "Zeta Shadow", x: 12, y: 8, z: -10, type: "black_market" as const, yieldMultiplier: 5.0, riskLevel: 5, playerCount: 95, isLocked: true },
  { id: "nebula_eta", name: "Eta Cloud", x: -12, y: -3, z: 12, type: "nebula" as const, yieldMultiplier: 3.5, riskLevel: 2, playerCount: 560, isLocked: false },
];

export default function Dashboard() {
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"map" | "fleets" | "tech" | "radar" | "shop" | "leaderboard">("map");
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState("");
  const [balance, setBalance] = useState("100.00");

  const api = new GameAPI();

  const connectWallet = async () => {
    // Mock wallet connection — replace with Circle wallet SDK
    setWalletAddress("0x..." + Math.random().toString(36).slice(2, 8));
    setWalletConnected(true);
  };

  return (
    <div className="min-h-screen bg-black">
      {/* Top nav */}
      <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-2xl">🐾</div>
            <div>
              <div className="text-sm font-bold text-white">COVEN TRADERS</div>
              <div className="text-[10px] text-gray-500">IDLE RPG · REAL USDC · AI DISCIPLES</div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {walletConnected ? (
              <>
                <div className="text-xs text-gray-400">
                  {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
                </div>
                <div className="text-sm font-mono text-green-400">${balance} USDC</div>
              </>
            ) : (
              <button
                onClick={connectWallet}
                className="bg-cyan-900/50 hover:bg-cyan-800/50 border border-cyan-600 text-cyan-400 text-xs font-mono py-2 px-4 rounded"
              >
                CONNECT WALLET
              </button>
            )}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-4">
            <CommandCenter
              playerId="demo-player"
              wsUrl="ws://localhost:8001"
              token="demo-token"
            />

            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-2">
              <div className="text-xs text-gray-500 uppercase">Navigation</div>
              {[
                { id: "map", label: "🗺️ Sector Map", desc: "Explore the galaxy" },
                { id: "fleets", label: "🚀 Fleet Manager", desc: "Deploy disciples" },
                { id: "tech", label: "🔬 Tech Tree", desc: "Research upgrades" },
                { id: "radar", label: "📡 Market Radar", desc: "Trading signals" },
                { id: "shop", label: "🛒 Market", desc: "Buy boosts & packs" },
                { id: "leaderboard", label: "🏆 Leaderboard", desc: "Season rankings" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`w-full text-left p-3 rounded transition-colors ${
                    activeTab === tab.id
                      ? "bg-cyan-900/30 border border-cyan-700"
                      : "bg-black/30 border border-gray-800 hover:border-gray-600"
                  }`}
                >
                  <div className="text-sm font-bold">{tab.label}</div>
                  <div className="text-[10px] text-gray-500">{tab.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Main content */}
          <div className="lg:col-span-3">
            {activeTab === "map" && (
              <div className="space-y-4">
                <SpaceMap
                  sectors={MOCK_SECTORS}
                  selectedSector={selectedSector}
                  onSelectSector={(s) => setSelectedSector(s.id)}
                  playerFleets={[{ sectorId: "core_alpha", count: 3 }]}
                />
                {selectedSector && (
                  <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-lg font-bold">
                          {MOCK_SECTORS.find((s) => s.id === selectedSector)?.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          Yield: {MOCK_SECTORS.find((s) => s.id === selectedSector)?.yieldMultiplier}x ·
                          Risk: {"⚠️".repeat(MOCK_SECTORS.find((s) => s.id === selectedSector)?.riskLevel || 0)}
                        </div>
                      </div>
                      <button className="bg-green-900/50 hover:bg-green-800/50 border border-green-700 text-green-400 text-xs font-mono py-2 px-4 rounded">
                        DEPLOY FLEET
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "shop" && (
              <Shop
                playerId="demo-player"
                api={api}
                walletBalance={balance}
              />
            )}

            {activeTab === "fleets" && (
              <FleetManager playerId="demo-player" api={api} />
            )}

            {activeTab === "tech" && (
              <TechTree />
            )}

            {activeTab === "radar" && (
              <MarketRadar />
            )}

            {activeTab === "leaderboard" && (
              <div className="bg-gray-900 border border-gray-700 rounded-lg p-8 text-center">
                <div className="text-4xl mb-4">🏆</div>
                <div className="text-lg font-bold">Leaderboard</div>
                <div className="text-sm text-gray-500">Coming in next build... Seasonal rankings with USDC prizes.</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
