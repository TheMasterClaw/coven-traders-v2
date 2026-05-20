"use client";

import { useState } from "react";

interface OnboardingProps {
  onComplete: () => void;
}

export default function Onboarding({ onComplete }: OnboardingProps) {
  const [step, setStep] = useState(0);
  const [fleetName, setFleetName] = useState("");

  const steps = [
    {
      title: "Welcome to Coven Traders",
      desc: "Command AI disciple fleets that trade real USDC across the galaxy. Even when you're offline, your fleets earn.",
      action: "Begin",
    },
    {
      title: "Deploy Your First Fleet",
      desc: "Name your fleet and choose a specialization. Each disciple has unique trading strategies.",
      action: "Deploy",
      input: true,
    },
    {
      title: "Watch Them Trade",
      desc: "Your fleet automatically analyzes markets and executes trades. Green = profit, Red = loss. Over time, they learn and improve.",
      action: "Observe",
    },
    {
      title: "Claim Your Earnings",
      desc: "Accumulated earnings can be claimed anytime. Use them to upgrade your fleet, buy boosts, or withdraw to your wallet.",
      action: "Start Earning",
    },
  ];

  const current = steps[step];

  return (
    <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-cyan-600 rounded-lg max-w-md w-full p-6 space-y-4">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Step {step + 1} of {steps.length}</span>
          <span>🐾 Coven Traders</span>
        </div>
        
        <div className="h-1 bg-gray-800 rounded-full">
          <div 
            className="h-full bg-cyan-500 rounded-full transition-all"
            style={{ width: `${((step + 1) / steps.length) * 100}%` }}
          />
        </div>

        <h2 className="text-xl font-bold text-white">{current.title}</h2>
        <p className="text-gray-400 text-sm">{current.desc}</p>

        {current.input && (
          <input
            type="text"
            placeholder="Fleet name..."
            value={fleetName}
            onChange={(e) => setFleetName(e.target.value)}
            className="w-full bg-black border border-gray-700 rounded p-3 text-white text-sm focus:border-cyan-500 outline-none"
          />
        )}

        <button
          onClick={() => step < steps.length - 1 ? setStep(step + 1) : onComplete()}
          className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 rounded transition-colors"
        >
          {current.action}
        </button>
      </div>
    </div>
  );
}
