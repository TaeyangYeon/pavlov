"""
Performance metrics collector for Step 26: Performance Optimization.
Provides thread-safe in-memory tracking of cache hit rates and AI costs.
"""

import threading
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any


@dataclass
class MarketMetrics:
    """Metrics for a specific market (KR or US)."""
    hits: int = 0
    misses: int = 0
    session_hits: int = 0
    session_misses: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate overall hit rate as percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    @property
    def session_hit_rate(self) -> float:
        """Calculate session hit rate as percentage."""
        total = self.session_hits + self.session_misses
        return (
            self.session_hits / total * 100
        ) if total > 0 else 0.0

    @property
    def total_requests(self) -> int:
        """Total number of requests (hits + misses)."""
        return self.hits + self.misses


class MetricsCollector:
    """
    Thread-safe in-memory metrics collector.
    Tracks cache hit rates and AI costs.
    Resets on app restart (acceptable for MVP).
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._markets: Dict[str, MarketMetrics] = {
            "KR": MarketMetrics(),
            "US": MarketMetrics(),
        }
        self._ai_calls: List[Dict[str, Any]] = []
        self._session_start = datetime.now()

    def record_cache_hit(self, ticker: str, market: str) -> None:
        """Record a cache hit for the given market."""
        with self._lock:
            if market not in self._markets:
                self._markets[market] = MarketMetrics()
            self._markets[market].hits += 1
            self._markets[market].session_hits += 1

    def record_cache_miss(self, ticker: str, market: str) -> None:
        """Record a cache miss for the given market."""
        with self._lock:
            if market not in self._markets:
                self._markets[market] = MarketMetrics()
            self._markets[market].misses += 1
            self._markets[market].session_misses += 1

    def get_hit_rate(self, market: str) -> float:
        """Get the overall hit rate for the given market."""
        with self._lock:
            m = self._markets.get(market, MarketMetrics())
            return m.hit_rate

    def get_session_hit_rate(self, market: str) -> float:
        """Get the session hit rate for the given market."""
        with self._lock:
            m = self._markets.get(market, MarketMetrics())
            return m.session_hit_rate

    def get_total_requests(self, market: str) -> int:
        """Get the total number of requests for the given market."""
        with self._lock:
            m = self._markets.get(market, MarketMetrics())
            return m.total_requests

    def record_ai_call(
        self,
        market: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal,
    ) -> None:
        """Record an AI API call with token usage and cost."""
        with self._lock:
            self._ai_calls.append({
                "market": market,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": float(cost_usd),
                "timestamp": datetime.now().isoformat(),
            })

    def get_total_ai_cost(self) -> Decimal:
        """Get the total AI cost across all calls."""
        with self._lock:
            return Decimal(str(
                sum(c["cost_usd"] for c in self._ai_calls)
            ))

    def get_ai_call_count(self) -> int:
        """Get the total number of AI calls made."""
        with self._lock:
            return len(self._ai_calls)

    def get_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all metrics."""
        with self._lock:
            return {
                "session_start": (
                    self._session_start.isoformat()
                ),
                "cache": {
                    market: {
                        "hit_rate": m.hit_rate,
                        "session_hit_rate": m.session_hit_rate,
                        "total_requests": m.total_requests,
                        "hits": m.hits,
                        "misses": m.misses,
                    }
                    for market, m in self._markets.items()
                },
                "ai": {
                    "total_calls": len(self._ai_calls),
                    "total_cost_usd": float(
                        sum(
                            c["cost_usd"]
                            for c in self._ai_calls
                        )
                    ),
                    "avg_cost_per_call": float(
                        sum(
                            c["cost_usd"]
                            for c in self._ai_calls
                        ) / max(len(self._ai_calls), 1)
                    ),
                    "calls": self._ai_calls[-10:],  # last 10 calls only
                },
            }

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        with self._lock:
            for market in self._markets:
                self._markets[market] = MarketMetrics()
            self._ai_calls = []
            self._session_start = datetime.now()


# Global singleton instance
_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector singleton."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector