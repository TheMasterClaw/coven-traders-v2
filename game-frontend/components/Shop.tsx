"use client";

import { useState } from "react";
import { GameAPI } from "@/lib/api";

interface ShopItem {
  id: string;
  name: string;
  description: string;
  price: string;
  currency: "USDC";
  category: "boost" | "cosmetic" | "pack" | "pass";
  icon: string;
  popular?: boolean;
  limited?: boolean;
}

const SHOP_ITEMS: ShopItem[] = [
  {
    id: "boost_2x_1h",
    name: "2x Speed Boost",
    description: "Double earnings for 1 hour",
    price: "0.99",
    currency: "USDC",
    category: "boost",
    icon: "⚡",
    popular: true,
  },
  {
    id: "boost_4x_30m",
    name: "4x Speed Boost",
    description: "Quadruple earnings for 30 minutes",
    price: "1.99",
    currency: "USDC",
    category: "boost",
    icon: "🚀",
  },
  {
    id: "boost_offline_8h",
    name: "Offline Boost",
    description: "8 hours of offline earnings instantly",
    price: "2.99",
    currency: "USDC",
    category: "boost",
    icon: "💤",
  },
  {
    id: "pack_starter",
    name: "Starter Fleet Pack",
    description: "3 Common fleets + 500 bonus earnings",
    price: "4.99",
    currency: "USDC",
    category: "pack",
    icon: "📦",
    popular: true,
  },
  {
    id: "pack_whale",
    name: "Whale Fleet Pack",
    description: "10 fleets guaranteed 1 Epic+",
    price: "49.99",
    currency: "USDC",
    category: "pack",
    icon: "🐋",
    limited: true,
  },
  {
    id: "skin_cyber",
    name: "Cyber Disciple Skin",
    description: "Neon cyberpunk aesthetic for all fleets",
    price: "2.99",
    currency: "USDC",
    category: "cosmetic",
    icon: "🎨",
  },
  {
    id: "skin_gold",
    name: "Golden Admiral Skin",
    description: "Prestigious gold-plated command center",
    price: "4.99",
    currency: "USDC",
    category: "cosmetic",
    icon: "👑",
    limited: true,
  },
  {
    id: "battle_pass_s1",
    name: "Season 1 Battle Pass",
    description: "60 tiers of exclusive rewards",
    price: "9.99",
    currency: "USDC",
    category: "pass",
    icon: "🎫",
    popular: true,
  },
];

interface ShopProps {
  playerId: string;
  api: GameAPI;
  walletBalance: string;
}

export default function Shop({ playerId, api, walletBalance }: ShopProps) {
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [purchasing, setPurchasing] = useState<string | null>(null);

  const categories = [
    { id: "all", label: "All", icon: "🛒" },
    { id: "boost", label: "Boosts", icon: "⚡" },
    { id: "pack", label: "Packs", icon: "📦" },
    { id: "cosmetic", label: "Skins", icon: "🎨" },
    { id: "pass", label: "Passes", icon: "🎫" },
  ];

  const filtered = activeCategory === "all"
    ? SHOP_ITEMS
    : SHOP_ITEMS.filter((i) => i.category === activeCategory);

  const handlePurchase = async (item: ShopItem) => {
    setPurchasing(item.id);
    try {
      await api.purchaseItem(playerId, item.id);
      alert(`Purchased ${item.name}!`);
    } catch (e: any) {
      alert(`Purchase failed: ${e?.message || 'Unknown error'}`);
    } finally {
      setPurchasing(null);
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white font-mono">MARKET</h2>
        <div className="text-sm font-mono text-green-400">
          Balance: ${parseFloat(walletBalance).toFixed(2)} USDC
        </div>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 overflow-x-auto">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-3 py-1.5 rounded text-xs font-mono whitespace-nowrap transition-colors ${
              activeCategory === cat.id
                ? "bg-cyan-900/50 border border-cyan-600 text-cyan-400"
                : "bg-gray-800 border border-gray-700 text-gray-400 hover:text-white"
            }`}
          >
            {cat.icon} {cat.label}
          </button>
        ))}
      </div>

      {/* Items grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="bg-black/40 border border-gray-800 rounded p-4 space-y-3 hover:border-gray-600 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="text-3xl">{item.icon}</div>
              <div className="flex gap-1">
                {item.popular && (
                  <span className="text-[10px] bg-orange-900/50 text-orange-400 px-1.5 py-0.5 rounded">POPULAR</span>
                )}
                {item.limited && (
                  <span className="text-[10px] bg-red-900/50 text-red-400 px-1.5 py-0.5 rounded">LIMITED</span>
                )}
              </div>
            </div>

            <div>
              <div className="text-sm font-bold text-white">{item.name}</div>
              <div className="text-xs text-gray-500">{item.description}</div>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-lg font-mono font-bold text-green-400">
                {item.price} {item.currency}
              </div>
              <button
                onClick={() => handlePurchase(item)}
                disabled={purchasing === item.id || parseFloat(walletBalance) < parseFloat(item.price)}
                className="bg-green-900/50 hover:bg-green-800/50 disabled:bg-gray-800 disabled:text-gray-600 border border-green-700 text-green-400 text-xs font-mono py-1.5 px-3 rounded transition-colors"
              >
                {purchasing === item.id ? "..." : "BUY"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
