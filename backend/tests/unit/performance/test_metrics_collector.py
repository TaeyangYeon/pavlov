"""
Unit tests for MetricsCollector (Step 26: Performance Optimization)
Tests cache hit rate calculation, market isolation, and thread safety.
"""

import pytest
from app.core.metrics import MetricsCollector, MarketMetrics, get_metrics_collector


class TestMarketMetrics:
    """Test the MarketMetrics dataclass."""
    
    def test_initial_state(self):
        """Test initial state of MarketMetrics."""
        metrics = MarketMetrics()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.session_hits == 0
        assert metrics.session_misses == 0
        assert metrics.hit_rate == 0.0
        assert metrics.session_hit_rate == 0.0
        assert metrics.total_requests == 0

    def test_hit_rate_all_hits(self):
        """Test hit rate calculation when all requests are hits."""
        metrics = MarketMetrics()
        metrics.hits = 5
        metrics.misses = 0
        assert metrics.hit_rate == 100.0

    def test_hit_rate_all_misses(self):
        """Test hit rate calculation when all requests are misses."""
        metrics = MarketMetrics()
        metrics.hits = 0
        metrics.misses = 5
        assert metrics.hit_rate == 0.0

    def test_hit_rate_mixed(self):
        """Test hit rate calculation with mixed hits/misses."""
        metrics = MarketMetrics()
        metrics.hits = 3
        metrics.misses = 1
        assert metrics.hit_rate == 75.0

    def test_session_hit_rate_mixed(self):
        """Test session hit rate calculation."""
        metrics = MarketMetrics()
        metrics.session_hits = 4
        metrics.session_misses = 1
        assert metrics.session_hit_rate == 80.0

    def test_total_requests_count(self):
        """Test total requests calculation."""
        metrics = MarketMetrics()
        metrics.hits = 3
        metrics.misses = 2
        assert metrics.total_requests == 5


class TestMetricsCollector:
    """Test the MetricsCollector class."""

    def test_initial_hit_rate_is_zero(self):
        """Test that initial hit rate is zero for any market."""
        collector = MetricsCollector()
        assert collector.get_hit_rate("KR") == 0.0
        assert collector.get_hit_rate("US") == 0.0

    def test_hit_rate_all_hits(self):
        """Test hit rate when only recording hits."""
        collector = MetricsCollector()
        for i in range(5):
            collector.record_cache_hit(f"TICKER{i}", "KR")
        assert collector.get_hit_rate("KR") == 100.0

    def test_hit_rate_all_misses(self):
        """Test hit rate when only recording misses."""
        collector = MetricsCollector()
        for i in range(5):
            collector.record_cache_miss(f"TICKER{i}", "KR")
        assert collector.get_hit_rate("KR") == 0.0

    def test_hit_rate_mixed(self):
        """Test hit rate with mixed hits and misses."""
        collector = MetricsCollector()
        # Record 3 hits, 1 miss = 75%
        for i in range(3):
            collector.record_cache_hit(f"TICKER{i}", "KR")
        collector.record_cache_miss("TICKER3", "KR")
        assert collector.get_hit_rate("KR") == 75.0

    def test_hit_rate_per_market_isolation(self):
        """Test that KR and US markets are tracked independently."""
        collector = MetricsCollector()
        
        # KR: 5 hits, 0 misses = 100%
        for i in range(5):
            collector.record_cache_hit(f"KR_TICKER{i}", "KR")
            
        # US: 0 hits, 5 misses = 0%
        for i in range(5):
            collector.record_cache_miss(f"US_TICKER{i}", "US")
            
        assert collector.get_hit_rate("KR") == 100.0
        assert collector.get_hit_rate("US") == 0.0

    def test_total_requests_count(self):
        """Test total request count calculation."""
        collector = MetricsCollector()
        collector.record_cache_hit("TICKER1", "KR")
        collector.record_cache_hit("TICKER2", "KR")
        collector.record_cache_miss("TICKER3", "KR")
        collector.record_cache_miss("TICKER4", "KR")
        assert collector.get_total_requests("KR") == 4

    def test_reset_clears_all_metrics(self):
        """Test that reset clears all metrics."""
        collector = MetricsCollector()
        
        # Add some data
        collector.record_cache_hit("TICKER1", "KR")
        collector.record_cache_miss("TICKER2", "US")
        collector.record_ai_call("KR", 1000, 200, 0.006)
        
        # Verify data exists
        assert collector.get_hit_rate("KR") > 0
        assert collector.get_ai_call_count() > 0
        
        # Reset and verify empty
        collector.reset()
        assert collector.get_hit_rate("KR") == 0.0
        assert collector.get_hit_rate("US") == 0.0
        assert collector.get_total_requests("KR") == 0
        assert collector.get_ai_call_count() == 0

    def test_session_vs_total_tracking(self):
        """Test session vs total tracking (both should be same initially)."""
        collector = MetricsCollector()
        
        # Record some data
        for i in range(10):
            collector.record_cache_hit(f"TICKER{i}", "KR")
        for i in range(2):
            collector.record_cache_miss(f"TICKER{i+10}", "KR")
        
        # Session and total should be same (no previous data)
        session_rate = collector.get_session_hit_rate("KR")
        total_rate = collector.get_hit_rate("KR")
        expected_rate = 10 / 12 * 100  # 83.33%
        
        assert session_rate == pytest.approx(expected_rate, rel=1e-2)
        assert total_rate == pytest.approx(expected_rate, rel=1e-2)

    def test_unknown_market_returns_zero(self):
        """Test that unknown market returns zero metrics."""
        collector = MetricsCollector()
        assert collector.get_hit_rate("UNKNOWN") == 0.0
        assert collector.get_total_requests("UNKNOWN") == 0

    def test_ai_call_recording(self):
        """Test AI call recording functionality."""
        from decimal import Decimal
        collector = MetricsCollector()
        
        collector.record_ai_call("KR", 1000, 200, Decimal("0.006"))
        collector.record_ai_call("US", 1500, 300, Decimal("0.009"))
        
        assert collector.get_ai_call_count() == 2
        assert collector.get_total_ai_cost() == Decimal("0.015")

    def test_summary_structure(self):
        """Test that get_summary returns proper structure."""
        collector = MetricsCollector()
        collector.record_cache_hit("TICKER1", "KR")
        collector.record_cache_miss("TICKER2", "KR")
        collector.record_ai_call("KR", 1000, 200, 0.006)
        
        summary = collector.get_summary()
        
        # Check structure
        assert "session_start" in summary
        assert "cache" in summary
        assert "ai" in summary
        
        # Check cache structure
        assert "KR" in summary["cache"]
        assert "US" in summary["cache"]
        kr_cache = summary["cache"]["KR"]
        assert "hit_rate" in kr_cache
        assert "session_hit_rate" in kr_cache
        assert "total_requests" in kr_cache
        assert "hits" in kr_cache
        assert "misses" in kr_cache
        
        # Check AI structure
        ai_data = summary["ai"]
        assert "total_calls" in ai_data
        assert "total_cost_usd" in ai_data
        assert "avg_cost_per_call" in ai_data
        assert "calls" in ai_data


class TestMetricsCollectorSingleton:
    """Test the singleton pattern of get_metrics_collector."""
    
    def test_singleton_returns_same_instance(self):
        """Test that get_metrics_collector returns the same instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2

    def test_singleton_maintains_state(self):
        """Test that singleton maintains state across calls."""
        collector1 = get_metrics_collector()
        collector1.record_cache_hit("TICKER1", "KR")
        
        collector2 = get_metrics_collector()
        assert collector2.get_hit_rate("KR") == 100.0