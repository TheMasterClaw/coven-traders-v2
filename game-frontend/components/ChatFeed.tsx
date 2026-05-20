"use client";

import { useState, useRef, useEffect } from "react";

interface ChatMessage {
  id: string;
  user: string;
  message: string;
  timestamp: string;
  type: "chat" | "trade" | "system";
}

const MOCK_MESSAGES: ChatMessage[] = [
  { id: "1", user: "VoidWalker", message: "Just deployed to Zeta Shadow. High risk, high reward 🚀", timestamp: "2m ago", type: "chat" },
  { id: "2", user: "System", message: "NebulaKing's fleet earned $234 in the last hour", timestamp: "5m ago", type: "system" },
  { id: "3", user: "CryptoClaw", message: "ETH looking bullish on the 4h. Signal strength 87%", timestamp: "8m ago", type: "trade" },
  { id: "4", user: "ArcTrader", message: "Anyone else seeing the funding rate arb opportunity?", timestamp: "12m ago", type: "chat" },
  { id: "5", user: "System", message: "New sector unlocked: Theta Nebula (Yield 4.5x)", timestamp: "15m ago", type: "system" },
];

export default function ChatFeed() {
  const [messages, setMessages] = useState(MOCK_MESSAGES);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const send = () => {
    if (!input.trim()) return;
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        user: "You",
        message: input,
        timestamp: "now",
        type: "chat",
      },
    ]);
    setInput("");
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 flex flex-col h-96">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Global Feed</div>
      
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-2 mb-2">
        {messages.map((m) => (
          <div key={m.id} className="text-sm">
            <span className={`font-bold ${
              m.type === "system" ? "text-yellow-400" :
              m.type === "trade" ? "text-green-400" :
              m.user === "You" ? "text-cyan-400" : "text-gray-300"
            }`}>
              {m.user}
            </span>
            <span className="text-gray-500 text-[10px] ml-2">{m.timestamp}</span>
            <div className="text-gray-400 text-xs mt-0.5">{m.message}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Type a message..."
          className="flex-1 bg-black border border-gray-700 rounded px-3 py-2 text-sm text-white focus:border-cyan-500 outline-none"
        />
        <button
          onClick={send}
          className="bg-cyan-700 hover:bg-cyan-600 text-white px-4 py-2 rounded text-sm"
        >
          Send
        </button>
      </div>
    </div>
  );
}
