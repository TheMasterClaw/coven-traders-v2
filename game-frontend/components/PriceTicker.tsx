"use client";

import { useEffect, useState } from "react";

interface PriceData {
  asset: string;
  price: number;
  change24h: number;
}

export default function PriceTicker() {
  const [prices, setPrices] = useState<PriceData[]>([
    { asset: "ETH", price: 0, change24h: 0 },
    { asset: "BTC", price: 0, change24h: 0 },
    { asset: "SOL", price: 0, change24h: 0 },
    { asset: "ARB", price: 0, change24h: 0 },
  ]);

  useEffect(() => {
    const ws = new WebSocket("wss://ws-feed.exchange.coinbase.com");
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: "subscribe",
        product_ids: ["ETH-USD", "BTC-USD", "SOL-USD"],
        channels: ["ticker"]
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "ticker") {
        setPrices(prev => prev.map(p => 
          p.asset === data.product_id.split("-")[0]
            ? { ...p, price: parseFloat(data.price), change24h: parseFloat(data.change_24h || 0) }
            : p
        ));
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Live Market Feed</div>
      <div className="space-y-2">
        {prices.map((p) => (
          <div key={p.asset} className="flex justify-between items-center">
            <span className="font-mono text-sm font-bold">{p.asset}</span>
            <div className="text-right">
              <div className="font-mono text-sm">${p.price > 0 ? p.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : "—"}</div>
              <div className={`text-xs ${p.change24h >= 0 ? "text-green-400" : "text-red-400"}`}>
                {p.change24h > 0 ? "+" : ""}{p.change24h.toFixed(2)}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
