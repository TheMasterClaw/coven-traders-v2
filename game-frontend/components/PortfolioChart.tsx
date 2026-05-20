"use client";

import { useEffect, useRef } from "react";

interface DataPoint {
  time: string;
  value: number;
}

const MOCK_DATA: DataPoint[] = Array.from({ length: 30 }, (_, i) => ({
  time: `Day ${i + 1}`,
  value: 100 + Math.sin(i * 0.3) * 20 + i * 2 + Math.random() * 10,
}));

export default function PortfolioChart() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const padding = 40;

    const values = MOCK_DATA.map((d) => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    // Grid
    ctx.strokeStyle = "#1f2937";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding + (h - 2 * padding) * (i / 4);
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(w - padding, y);
      ctx.stroke();
    }

    // Line
    ctx.strokeStyle = "#06b6d4";
    ctx.lineWidth = 2;
    ctx.beginPath();
    MOCK_DATA.forEach((d, i) => {
      const x = padding + (w - 2 * padding) * (i / (MOCK_DATA.length - 1));
      const y = padding + (h - 2 * padding) * (1 - (d.value - min) / range);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Fill
    ctx.fillStyle = "rgba(6, 182, 212, 0.1)";
    ctx.lineTo(w - padding, h - padding);
    ctx.lineTo(padding, h - padding);
    ctx.closePath();
    ctx.fill();

    // Labels
    ctx.fillStyle = "#6b7280";
    ctx.font = "10px monospace";
    ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const val = min + range * (1 - i / 4);
      const y = padding + (h - 2 * padding) * (i / 4);
      ctx.fillText(`$${val.toFixed(0)}`, padding - 5, y + 3);
    }
  }, []);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Portfolio Performance (30D)</div>
      <canvas
        ref={canvasRef}
        className="w-full h-48"
        style={{ width: "100%", height: "192px" }}
      />
      <div className="flex justify-between mt-2 text-[10px] text-gray-600">
        <span>Sharpe: 1.84</span>
        <span>Max DD: -12.3%</span>
        <span>Win Rate: 62%</span>
      </div>
    </div>
  );
}
