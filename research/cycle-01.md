# Research Cycle 1 — Coven Traders Improvements

## 1. Add Real-Time WebSocket Price Ticker
**Why:** Static demo looks dead. Live price feeds make it feel real.
**How:** Coinbase WebSocket → React component → displayed in Command Center
**Impact:** HIGH

## 2. Add Particle Effects for Trades
**Why:** Every trade should feel like a laser battle. Visual feedback = engagement.
**How:** Canvas 2D particles on trade events, green/red bursts
**Impact:** HIGH

## 3. Add Sound Effects
**Why:** Audio immersion. Trade pings, level-up chimes, boss fight alarms.
**How:** Web Audio API, generated sfx
**Impact:** MEDIUM

## 4. Add Onboarding Flow
**Why:** New users need to understand idle + real money concept.
**How:** 3-step tutorial: deploy fleet → watch first trade → claim earnings
**Impact:** HIGH

## 5. Add Social Features (Guilds/Alliances)
**Why:** Idle games thrive on social. Guild wars = tournament teams.
**How:** Smart contract for guilds, shared treasury, collective missions
**Impact:** MEDIUM

## 6. Add Push Notifications
**Why:** Re-engagement. "Your fleet just earned $12.50 while you were away"
**How:** Web Push API + service worker
**Impact:** MEDIUM

## 7. Add Mobile-First Responsive Design
**Why:** Most users will play on phone.
**How:** Tailwind responsive, touch-friendly, PWA manifest
**Impact:** HIGH

## 8. Add Dark/Light Theme Toggle
**Why:** Accessibility + user preference.
**How:** next-themes, toggle in nav
**Impact:** LOW

## 9. Add Analytics Dashboard
**Why:** Track player behavior, optimize monetization.
**How:** Mixpanel/Amplitude, custom events
**Impact:** MEDIUM

## 10. Add Referral System
**Why:** Viral growth. "Invite a disciple, earn 10% of their trades"
**How:** Referral code in URL, smart contract tracking
**Impact:** HIGH
