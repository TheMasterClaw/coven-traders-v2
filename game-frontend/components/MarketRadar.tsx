"use client";

import { useState, useEffect } from "react";

interface Signal {
  id: string;
  type: "buy" | "sell" | "arbitrage" | "alert";
  asset: string;
  sector: string;
  confidence: number;
  timestamp: string;
  price: string;
  targetPrice: string;
  urgency: "low" | "medium" | "high" | "critical";
}

const MOCK_SIGNALS: Signal[] = [
  { id: "s1", type: "buy", asset: "ETH", sector: "core_alpha", confidence: 87, timestamp: "2m ago", price: "3,245.00", targetPrice: "3,500.00", urgency: "high" },
  { id: "s2", type: "arbitrage", asset: "BTC", sector: "outer_gamma", confidence: 92, timestamp: "5m ago", price: "67,200.00", targetPrice: "67,800.00", urgency: "critical" },
  { id: "s3", type: "sell", asset: "SOL", sector: "wormhole_epsilon", confidence: 64, timestamp: "12m ago", price: "145.00", targetPrice: "132.00", urgency: "medium" },
  { id: "s4", type: "alert", asset: "USDC", sector: "core_alpha", confidence: 95, timestamp: "1m ago", price: "1.00", targetPrice: "1.00", urgency: "low" },
  { id: "s5", type: "buy", asset: "LINK", sector: "nebula_beta", confidence: 78, timestamp: "8m ago", price: "18.50", targetPrice: "22.00", urgency: "medium" },
  { id: "s6", type: "arbitrage", asset: "UNI", sector: "outer_gamma", confidence: 81, timestamp: "15m ago", price: "9.20", targetPrice: "9.85", urgency: "high" },
];

const TYPE_ICONS: Record<string, string> = {
  buy: "📈",
  sell: "📉",
  arbitrage: "⚡",
  alert: "🔔",
};

const TYPE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  buy: { bg: "bg-green-900/20", border: "border-green-700", text: "text-green-400" },
  sell: { bg: "bg-red-900/20", border: "border-red-700", text: "text-red-400" },
  arbitrage: { bg: "bg-yellow-900/20", border: "border-yellow-700", text: "text-yellow-400" },
  alert: { bg: "bg-blue-900/20", border: "border-blue-700", text: "text-blue-400" },
};

const URGENCY_PULSE: Record<string, string> = {
  low: "",
  medium: "animate-pulse",
  high: "animate-pulse",
  critical: "animate-ping",
};

export default function MarketRadar() {
  const [signals, setSignals] = useState<Signal[]>(MOCK_SIGNALS);
  const [filter, setFilter] = useState<string>("all");
  const [scanning, setScanning] = useState(false);

  const filtered = filter === "all"
    ? signals
    : signals.filter((s) => s.type === filter);

  const handleScan = () => {
    setScanning(true);
    setTimeout(() => {
      const newSignal: Signal = {
        id: `s${Date.now()}`,
        type: ["buy", "sell", "arbitrage", "alert"][Math.floor(Math.random() * 4)] as Signal["type"],
        asset: ["ETH", "BTC", "SOL", "LINK", "UNI", "AAVE"][Math.floor(Math.random() * 6)],
        sector: ["core_alpha", "outer_gamma", "nebula_beta", "wormhole_epsilon"][Math.floor(Math.random() * 4)],
        confidence: Math.floor(Math.random() * 40) + 60,
        timestamp: "just now",
        price: (Math.random() * 1000).toFixed(2),
        targetPrice: (Math.random() * 1200).toFixed(2),
        urgency: ["low", "medium", "high", "critical"][Math.floor(Math.random() * 4)] as Signal["urgency"],
      };
      setSignals((prev) => [newSignal, ...prev].slice(0, 12));
      setScanning(false);
    }, 1500);
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white font-mono">MARKET RADAR</h2>
          <div className="text-xs text-gray-500">Real-time trading signals across sectors</div>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className={`text-xs font-mono py-2 px-4 rounded border transition-colors ${
            scanning
              ? "bg-gray-800 border-gray-700 text-gray-500"
              : "bg-cyan-900/50 border-cyan-600 text-cyan-400 hover:bg-cyan-800/50"
          }`}
        >
          {scanning ? "🔍 SCANNING..." : "🔍 DEEP SCAN"}
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {[
          { id: "all", label: "All Signals" },
          { id: "buy", label: "📈 Buy" },
          { id: "sell", label: "📉 Sell" },
          { id: "arbitrage", label: "⚡ Arbitrage" },
          { id: "alert", label: "🔔 Alerts" },
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
      </div>

      {/* Signals List */}
      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {filtered.map((signal) => {
          const colors = TYPE_COLORS[signal.type];
          const profit = parseFloat(signal.targetPrice) - parseFloat(signal.price);
          const profitPercent = (profit / parseFloat(signal.price)) * 100;

          return (
            <div
              key={signal.id}
              className={`border rounded p-3 space-y-2 ${colors.bg} ${colors.border}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{TYPE_ICONS[signal.type]}</span>
                  <div>
                    <div className="text-sm font-bold text-white">{signal.asset}</div>
                    <div className="text-[10px] text-gray-500">{signal.sector.replace("_", " ").toUpperCase()}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-xs font-mono ${colors.text}`}>
                    {signal.confidence}% confidence
                  </div>
                  <div className="text-[10px] text-gray-500">{signal.timestamp}</div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="font-mono text-gray-400">
                  ${signal.price} → <span className={profit > 0 ? "text-green-400" : "text-red-400"}>${signal.targetPrice}</span>
                </div>
                <div className={`font-mono ${profit > 0 ? "text-green-400" : "text-red-400"}`}>
                  {profit > 0 ? "+" : ""}{profitPercent.toFixed(2)}%
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex-1 h-1 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${colors.text.replace("text", "bg")}`}
                    style={{ width: `${signal.confidence}%` }}
                  />
                </div>
                {signal.urgency === "critical" && (
                  <span className="text-red-500 text-xs">🔥</span>
                )}
              </div>

              <div className="flex gap-2">
                <button className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-mono py-1.5 px-2 rounded transition-colors">
                  VIEW CHART
                </button>
                <button className={`flex-1 text-xs font-mono py-1.5 px-2 rounded transition-colors ${colors.bg} ${colors.text} border ${colors.border}`}>
                  EXECUTE
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
