# Agora Coven Traders — Monetization Layer

All micro-transactions denominated in USDC on Arc EVM L2.

## Structure

```
monetization/
├── configs/
│   ├── shop_config.yaml      # SKU catalog, bundles, sale events
│   └── battle_pass.yaml      # Season 03: Astral Drift (free + premium tracks)
├── drop_rates/
│   ├── standard_pool.json    # Common→Epic gacha pool (on-chain verifiable)
│   └── ancient_pool.json     # Rare→Legendary gacha pool (on-chain verifiable)
├── analytics/
│   ├── __init__.py
│   └── revenue_engine.py     # Python analytics engine (KPIs, forecast, gacha audit)
├── contracts/
│   ├── GachaRateCommitment.sol   # Daily rate hash commitments
│   ├── GachaPullVRF.sol          # Commit-reveal VRF pull system
│   └── ShopUSDC.sol              # USDC shop with bundles & sales
└── README.md
```

## Key Features

1. **Shop Config (YAML)**
   - 5 categories: boosts, cosmetics, resource packs, battle pass, gacha
   - Bundles with discount percentages
   - Flash & seasonal sale events
   - All prices in USDC (6 decimals)

2. **Gacha Fleet System (JSON + Solidity)**
   - Two pools: Standard (Common→Epic) and Ancient (Rare→Legendary)
   - On-chain verifiable drop rates via `GachaRateCommitment.sol`
   - Commit-reveal with Chainlink VRF (`GachaPullVRF.sol`)
   - Soft pity (incrementing odds) + hard pity (guaranteed rarity)
   - 10-pull guarantees (Rare+ / Epic+)
   - Daily keccak256 rate commitments for public audit

3. **Battle Pass (YAML)**
   - 100 tiers, 92-day season
   - Free track + Premium track ($9.99) + Premium+ ($19.99 with 10-tier skip)
   - Milestone rewards every 10 tiers
   - Seasonal events: Mid-Season Surge (2x XP), Final Push (1.5x XP)
   - XP from idle production, trading, PvP, guild contributions, quests

4. **Revenue Analytics (Python)**
   - Ingests transactions & gacha pulls
   - Daily metrics: gross/net revenue, ARPU, ARPPU, conversion, refunds
   - Category breakdown with AOV
   - Gacha pool analytics: expected vs actual rarity distribution, pity triggers
   - 7-day moving average revenue forecast
   - Rate commitment hash computation for on-chain verification
   - Exports JSON dashboard

## Quick Start

```bash
cd ~/covenant/agora-coven-traders/monetization
python3 analytics/revenue_engine.py
```

This runs the demo, generating synthetic data and exporting `analytics/dashboard_latest.json`.

## On-Chain Verification Flow

1. Oracle commits daily rate hash to `GachaRateCommitment`
2. Player calls `commitPull()` → VRF request initiated
3. Chainlink fulfills randomness
4. Player calls `revealPull()` with entropy proof
5. Analytics engine computes commitment hash from JSON and compares on-chain
6. All events indexed for public audit
