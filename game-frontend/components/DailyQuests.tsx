"use client";

import { useState } from "react";

interface Quest {
  id: string;
  title: string;
  description: string;
  reward: string;
  progress: number;
  max: number;
  completed: boolean;
  expiresIn: string;
}

const MOCK_QUESTS: Quest[] = [
  { id: "q1", title: "Daily Trader", description: "Execute 5 trades today", reward: "50 BOOST", progress: 3, max: 5, completed: false, expiresIn: "14h" },
  { id: "q2", title: "HODL Master", description: "Hold a position for 6 hours", reward: "100 BOOST", progress: 4, max: 6, completed: false, expiresIn: "14h" },
  { id: "q3", title: "Profit Hunter", description: "Make $50 in profit", reward: "25 USDC", progress: 50, max: 50, completed: true, expiresIn: "14h" },
  { id: "q4", title: "Sector Explorer", description: "Deploy to 3 different sectors", reward: "75 BOOST", progress: 1, max: 3, completed: false, expiresIn: "14h" },
];

export default function DailyQuests() {
  const [quests, setQuests] = useState(MOCK_QUESTS);

  const claim = (id: string) => {
    setQuests((prev) => prev.map((q) => (q.id === id ? { ...q, completed: true } : q)));
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-500 uppercase tracking-wider">Daily Quests</div>
        <div className="text-[10px] text-cyan-400">⏰ Resets in 14h</div>
      </div>

      <div className="space-y-2">
        {quests.map((q) => (
          <div
            key={q.id}
            className={`border rounded-lg p-3 ${
              q.completed ? "border-green-800 bg-green-950/20" : "border-gray-800 bg-black/30"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-bold">{q.title}</div>
                <div className="text-xs text-gray-500">{q.description}</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-yellow-400">+{q.reward}</div>
                {q.progress >= q.max && !q.completed && (
                  <button
                    onClick={() => claim(q.id)}
                    className="text-[10px] bg-green-700 hover:bg-green-600 text-white px-2 py-0.5 rounded mt-1"
                  >
                    Claim
                  </button>
                )}
              </div>
            </div>
            <div className="mt-2 h-1.5 bg-gray-800 rounded-full">
              <div
                className={`h-full rounded-full transition-all ${
                  q.completed ? "bg-green-500" : "bg-cyan-500"
                }`}
                style={{ width: `${Math.min((q.progress / q.max) * 100, 100)}%` }}
              />
            </div>
            <div className="text-[10px] text-gray-600 mt-0.5">
              {q.progress}/{q.max}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
