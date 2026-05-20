"use client";

import { useEffect, useRef } from "react";

export function useSound() {
  const ctxRef = useRef<AudioContext | null>(null);

  const getCtx = () => {
    if (!ctxRef.current) {
      ctxRef.current = new AudioContext();
    }
    return ctxRef.current;
  };

  const playTone = (freq: number, duration: number, type: OscillatorType = "sine") => {
    const ctx = getCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    gain.gain.setValueAtTime(0.1, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  };

  const tradeWin = () => {
    playTone(523, 0.1, "sine");
    setTimeout(() => playTone(659, 0.1, "sine"), 100);
    setTimeout(() => playTone(784, 0.2, "sine"), 200);
  };

  const tradeLoss = () => {
    playTone(400, 0.2, "sawtooth");
    setTimeout(() => playTone(300, 0.3, "sawtooth"), 150);
  };

  const levelUp = () => {
    playTone(440, 0.1, "square");
    setTimeout(() => playTone(554, 0.1, "square"), 100);
    setTimeout(() => playTone(659, 0.1, "square"), 200);
    setTimeout(() => playTone(880, 0.3, "square"), 300);
  };

  const click = () => playTone(800, 0.05, "sine");

  return { tradeWin, tradeLoss, levelUp, click };
}

export function useHaptic() {
  const trigger = (pattern: number | number[] = 50) => {
    if (typeof navigator !== "undefined" && navigator.vibrate) {
      navigator.vibrate(pattern);
    }
  };

  const trade = () => trigger([30, 50, 30]);
  const error = () => trigger([100, 50, 100]);
  const success = () => trigger(50);

  return { trade, error, success };
}
