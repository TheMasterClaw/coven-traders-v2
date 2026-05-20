#!/usr/bin/env python3
"""
Agora Coven Traders — Revenue Analytics Engine
Processes on-chain USDC micro-transaction data from Arc L2,
generates dashboards, forecasts, and regulatory reports.
"""

from __future__ import annotations

import json
import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Transaction:
    txn_hash: str
    timestamp: datetime
    player_address: str
    sku: str
    category: str
    usdc_amount: Decimal
    quantity: int = 1
    season_id: Optional[str] = None


@dataclass
class GachaPull:
    pull_id: str
    txn_hash: str
    timestamp: datetime
    player_address: str
    pool_id: str
    item_id: str
    rarity: str
    pity_count: int
    entropy: str
    usdc_amount: Decimal


@dataclass
class DailyMetrics:
    date: str
    gross_revenue_usdc: Decimal = Decimal("0")
    net_revenue_usdc: Decimal = Decimal("0")
    txn_count: int = 0
    unique_payers: int = 0
    arpu: Decimal = Decimal("0")          # average revenue per user
    arppu: Decimal = Decimal("0")         # average revenue per paying user
    conversion_rate_percent: Decimal = Decimal("0")
    refunds_usdc: Decimal = Decimal("0")
    refund_count: int = 0


@dataclass
class CategoryMetrics:
    category: str
    revenue_usdc: Decimal = Decimal("0")
    txn_count: int = 0
    units_sold: int = 0
    avg_order_value: Decimal = Decimal("0")


@dataclass
class GachaAnalytics:
    pool_id: str
    total_pulls: int = 0
    revenue_usdc: Decimal = Decimal("0")
    rarity_distribution: Dict[str, int] = field(default_factory=dict)
    pity_triggered_count: int = 0
    expected_vs_actual: Dict[str, Tuple[Decimal, Decimal]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Revenue Engine
# ---------------------------------------------------------------------------

class RevenueEngine:
    """
    Ingests raw transaction logs (simulated or from indexer),
    computes KPIs, and emits JSON dashboard data.
    """

    PLATFORM_FEE_PERCENT = Decimal("0.10")   # 10% platform fee assumption
    REFUND_WINDOW_DAYS = 7

    def __init__(self, shop_config_path: str, drop_rates_dir: str) -> None:
        self.shop_config = self._load_yaml(shop_config_path)
        self.drop_rates: Dict[str, dict] = {}
        self._load_drop_rates(drop_rates_dir)
        self.transactions: List[Transaction] = []
        self.gacha_pulls: List[GachaPull] = []
        self.refunds: Dict[str, Transaction] = {}

    # -- loaders --------------------------------------------------------------

    @staticmethod
    def _load_yaml(path: str) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _load_drop_rates(self, directory: str) -> None:
        p = Path(directory)
        for fp in p.glob("*.json"):
            with open(fp, "r") as f:
                data = json.load(f)
                self.drop_rates[data["pool_id"]] = data

    # -- ingestion ------------------------------------------------------------

    def ingest_transaction(self, txn: Transaction) -> None:
        self.transactions.append(txn)

    def ingest_gacha_pull(self, pull: GachaPull) -> None:
        self.gacha_pulls.append(pull)

    def ingest_refund(self, original_txn_hash: str, refund_txn: Transaction) -> None:
        self.refunds[original_txn_hash] = refund_txn

    # -- core analytics -------------------------------------------------------

    def daily_metrics(self, start: datetime, end: datetime) -> List[DailyMetrics]:
        days = []
        cursor = start
        while cursor <= end:
            day_str = cursor.strftime("%Y-%m-%d")
            day_txns = [
                t for t in self.transactions
                if t.timestamp.strftime("%Y-%m-%d") == day_str
                and t.txn_hash not in self.refunds
            ]
            day_refunds = [
                r for r in self.refunds.values()
                if r.timestamp.strftime("%Y-%m-%d") == day_str
            ]

            gross = sum((t.usdc_amount * t.quantity for t in day_txns), Decimal("0"))
            refunds_total = sum((r.usdc_amount for r in day_refunds), Decimal("0"))
            net = gross - refunds_total
            unique = len({t.player_address for t in day_txns})
            dau = self._dau_estimate(cursor)  # stub; real impl queries player DB

            dm = DailyMetrics(
                date=day_str,
                gross_revenue_usdc=gross.quantize(Decimal("0.01")),
                net_revenue_usdc=net.quantize(Decimal("0.01")),
                txn_count=len(day_txns),
                unique_payers=unique,
                arpu=(gross / dau).quantize(Decimal("0.0001")) if dau else Decimal("0"),
                arppu=(gross / unique).quantize(Decimal("0.0001")) if unique else Decimal("0"),
                conversion_rate_percent=(Decimal(unique) / dau * 100).quantize(Decimal("0.01")) if dau else Decimal("0"),
                refunds_usdc=refunds_total.quantize(Decimal("0.01")),
                refund_count=len(day_refunds),
            )
            days.append(dm)
            cursor += timedelta(days=1)
        return days

    def category_breakdown(self) -> List[CategoryMetrics]:
        cats: Dict[str, CategoryMetrics] = {}
        for t in self.transactions:
            if t.txn_hash in self.refunds:
                continue
            if t.category not in cats:
                cats[t.category] = CategoryMetrics(category=t.category)
            cm = cats[t.category]
            cm.revenue_usdc += t.usdc_amount * t.quantity
            cm.txn_count += 1
            cm.units_sold += t.quantity
        for cm in cats.values():
            cm.avg_order_value = (cm.revenue_usdc / cm.txn_count).quantize(Decimal("0.01")) if cm.txn_count else Decimal("0")
        return list(cats.values())

    def gacha_pool_analytics(self, pool_id: str) -> GachaAnalytics:
        pool = self.drop_rates.get(pool_id)
        if not pool:
            raise ValueError(f"Unknown pool: {pool_id}")

        pulls = [p for p in self.gacha_pulls if p.pool_id == pool_id]
        ga = GachaAnalytics(pool_id=pool_id)
        ga.total_pulls = len(pulls)
        ga.revenue_usdc = sum((p.usdc_amount for p in pulls), Decimal("0"))

        rarity_counts: Dict[str, int] = {}
        for p in pulls:
            rarity_counts[p.rarity] = rarity_counts.get(p.rarity, 0) + 1
            if p.pity_count >= pool["pity"]["hard_pity_pull"]:
                ga.pity_triggered_count += 1
        ga.rarity_distribution = rarity_counts

        for rarity, tier in pool["rarity_tiers"].items():
            expected = Decimal(str(tier["base_drop_rate"])) * ga.total_pulls
            actual = Decimal(rarity_counts.get(rarity, 0))
            ga.expected_vs_actual[rarity] = (
                expected.quantize(Decimal("0.01")),
                actual.quantize(Decimal("0.01")),
            )
        return ga

    def forecast_revenue(self, days_ahead: int = 30) -> List[Dict]:
        """Simple moving-average forecast based on last 7 days."""
        if not self.transactions:
            return []
        end = max(t.timestamp for t in self.transactions)
        start = end - timedelta(days=6)
        daily = self.daily_metrics(start, end)
        avg_net = sum((d.net_revenue_usdc for d in daily), Decimal("0")) / len(daily)
        forecast = []
        for i in range(1, days_ahead + 1):
            fdate = (end + timedelta(days=i)).strftime("%Y-%m-%d")
            forecast.append({
                "date": fdate,
                "forecast_net_usdc": float(avg_net.quantize(Decimal("0.01"))),
                "confidence": "low" if len(daily) < 7 else "medium",
            })
        return forecast

    # -- dashboard export -----------------------------------------------------

    def generate_dashboard(self, start: datetime, end: datetime) -> dict:
        daily = self.daily_metrics(start, end)
        cats = self.category_breakdown()
        gacha = {pid: self.gacha_pool_analytics(pid) for pid in self.drop_rates}
        forecast = self.forecast_revenue()

        total_gross = sum((d.gross_revenue_usdc for d in daily), Decimal("0"))
        total_net = sum((d.net_revenue_usdc for d in daily), Decimal("0"))
        total_txns = sum(d.txn_count for d in daily)
        total_refunds = sum((d.refunds_usdc for d in daily), Decimal("0"))

        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "summary": {
                "gross_revenue_usdc": float(total_gross.quantize(Decimal("0.01"))),
                "net_revenue_usdc": float(total_net.quantize(Decimal("0.01"))),
                "total_transactions": total_txns,
                "total_refunds_usdc": float(total_refunds.quantize(Decimal("0.01"))),
                "refund_rate_percent": float((total_refunds / total_gross * 100).quantize(Decimal("0.01"))) if total_gross else 0.0,
            },
            "daily": [
                {
                    "date": d.date,
                    "gross": float(d.gross_revenue_usdc),
                    "net": float(d.net_revenue_usdc),
                    "txns": d.txn_count,
                    "unique_payers": d.unique_payers,
                    "arpu": float(d.arpu),
                    "arppu": float(d.arppu),
                    "conversion_rate": float(d.conversion_rate_percent),
                    "refunds": float(d.refunds_usdc),
                }
                for d in daily
            ],
            "category_breakdown": [
                {
                    "category": c.category,
                    "revenue_usdc": float(c.revenue_usdc.quantize(Decimal("0.01"))),
                    "transactions": c.txn_count,
                    "units_sold": c.units_sold,
                    "avg_order_value": float(c.avg_order_value),
                }
                for c in cats
            ],
            "gacha_analytics": {
                pid: {
                    "total_pulls": g.total_pulls,
                    "revenue_usdc": float(g.revenue_usdc.quantize(Decimal("0.01"))),
                    "rarity_distribution": g.rarity_distribution,
                    "pity_triggered": g.pity_triggered_count,
                    "expected_vs_actual": {
                        r: {"expected": float(e), "actual": float(a)}
                        for r, (e, a) in g.expected_vs_actual.items()
                    },
                }
                for pid, g in gacha.items()
            },
            "forecast": forecast,
        }

    def export_dashboard(self, start: datetime, end: datetime, out_path: str) -> None:
        data = self.generate_dashboard(start, end)
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Dashboard exported to {out_path}")

    # -- on-chain rate verification ------------------------------------------

    @staticmethod
    def compute_rate_commitment(pool_json_path: str) -> str:
        """Compute keccak256 commitment hash for a drop-rate JSON file."""
        with open(pool_json_path, "r") as f:
            data = json.load(f)
        # Strip signatures/audit fields that shouldn't be in commitment
        stripped = {k: v for k, v in data.items() if k != "verification"}
        payload = json.dumps(stripped, sort_keys=True, separators=(",", ":"))
        return "0x" + hashlib.sha3_256(payload.encode()).hexdigest()

    # -- helpers --------------------------------------------------------------

    def _dau_estimate(self, day: datetime) -> int:
        """Stub: real implementation queries player activity DB."""
        # Return a synthetic DAU based on unique payers * 10 as a rough proxy
        day_txns = [t for t in self.transactions if t.timestamp.date() == day.date()]
        unique_payers = len({t.player_address for t in day_txns})
        return max(unique_payers * 10, 1)


# ---------------------------------------------------------------------------
# CLI / Demo
# ---------------------------------------------------------------------------

def _demo():
    base = Path(__file__).parent.parent
    engine = RevenueEngine(
        shop_config_path=str(base / "configs" / "shop_config.yaml"),
        drop_rates_dir=str(base / "drop_rates"),
    )

    # Synthetic data
    now = datetime.utcnow()
    players = [f"0xPlayer{i:04d}" for i in range(1, 51)]
    skus = ["boost_2h", "pack_starter", "gacha_standard", "gacha_standard_10", "bp_premium"]
    cats = ["boosts", "resource_packs", "gacha", "gacha", "battle_pass"]
    prices = [Decimal("0.99"), Decimal("0.99"), Decimal("0.99"), Decimal("8.99"), Decimal("9.99")]

    import random
    random.seed(42)

    for i in range(500):
        idx = random.randrange(len(skus))
        t = Transaction(
            txn_hash=f"0x{hashlib.sha256(str(i).encode()).hexdigest()}",
            timestamp=now - timedelta(days=random.randint(0, 6), hours=random.randint(0, 23)),
            player_address=random.choice(players),
            sku=skus[idx],
            category=cats[idx],
            usdc_amount=prices[idx],
            quantity=random.randint(1, 3),
        )
        engine.ingest_transaction(t)

    # Synthetic gacha pulls
    rarities = ["common", "uncommon", "rare", "epic", "legendary"]
    rarity_weights = [60, 28, 9, 2.5, 0.5]
    for i in range(300):
        r = random.choices(rarities, weights=rarity_weights)[0]
        p = GachaPull(
            pull_id=f"pull_{i}",
            txn_hash=f"0x{hashlib.sha256(f'pull{i}'.encode()).hexdigest()}",
            timestamp=now - timedelta(days=random.randint(0, 6)),
            player_address=random.choice(players),
            pool_id="standard",
            item_id=f"item_{r}_{i}",
            rarity=r,
            pity_count=random.randint(1, 95),
            entropy=f"0x{hashlib.sha256(f'entropy{i}'.encode()).hexdigest()}",
            usdc_amount=Decimal("0.99"),
        )
        engine.ingest_gacha_pull(p)

    start = now - timedelta(days=6)
    end = now
    out = base / "analytics" / "dashboard_latest.json"
    engine.export_dashboard(start, end, str(out))

    # Print summary
    dash = engine.generate_dashboard(start, end)
    print("\n--- Revenue Summary ---")
    print(f"Gross: ${dash['summary']['gross_revenue_usdc']}")
    print(f"Net:   ${dash['summary']['net_revenue_usdc']}")
    print(f"Txns:  {dash['summary']['total_transactions']}")
    print(f"Refund Rate: {dash['summary']['refund_rate_percent']}%")

    print("\n--- Gacha Analytics (Standard Pool) ---")
    ga = dash["gacha_analytics"]["standard"]
    print(f"Total Pulls: {ga['total_pulls']}")
    for r, counts in ga["rarity_distribution"].items():
        eva = ga["expected_vs_actual"].get(r, {})
        print(f"  {r}: {counts} (expected {eva.get('expected', 0):.1f})")

    print("\n--- Rate Commitment (Standard Pool) ---")
    commitment = engine.compute_rate_commitment(str(base / "drop_rates" / "standard_pool.json"))
    print(f"Commitment: {commitment}")


if __name__ == "__main__":
    _demo()
