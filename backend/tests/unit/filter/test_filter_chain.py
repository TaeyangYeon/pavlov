"""
Unit tests for FilterChain.
Tests sequential filter application and orchestration logic.
"""

from unittest.mock import MagicMock

import pytest
from app.domain.filter.chain import FilterChain
from app.domain.filter.interfaces import FilterPort


class TestFilterChain:
    """Test filter chain orchestration and sequential application."""

    @pytest.fixture
    def mock_filters(self):
        """Create mock filters for testing chain logic."""
        # Mock filter 1: removes stocks with even ticker length
        filter1 = MagicMock(spec=FilterPort)
        filter1.filter_name = "mock_filter_1"
        filter1.apply.side_effect = lambda stocks: [
            s for s in stocks if len(s["ticker"]) % 2 == 1
        ]

        # Mock filter 2: removes stocks with close price < 100
        filter2 = MagicMock(spec=FilterPort)
        filter2.filter_name = "mock_filter_2"
        filter2.apply.side_effect = lambda stocks: [
            s for s in stocks if s["close"] >= 100
        ]

        return [filter1, filter2]

    @pytest.fixture
    def sample_stocks(self):
        """Sample stocks for testing chain application."""
        return [
            {"ticker": "A", "close": 150},  # pass filter1, pass filter2 → FINAL
            {"ticker": "BB", "close": 200},  # fail filter1 → OUT
            {"ticker": "CCC", "close": 50},  # pass filter1, fail filter2 → OUT
            {"ticker": "DDDD", "close": 120},  # fail filter1 → OUT
            {"ticker": "EEEEE", "close": 300},  # pass filter1, pass filter2 → FINAL
        ]

    def test_chain_applies_filters_sequentially(self, mock_filters, sample_stocks):
        """FilterChain applies filters in sequence with correct counts."""
        chain = FilterChain(mock_filters)

        result = chain.apply(sample_stocks)

        # Expected: 5 → filter1 → 3 ("A", "CCC", "EEEEE") → filter2 → 2 ("A", "EEEEE")
        assert len(result) == 2
        assert result[0]["ticker"] == "A"
        assert result[1]["ticker"] == "EEEEE"

        # Verify both filters were called
        mock_filters[0].apply.assert_called_once()
        mock_filters[1].apply.assert_called_once()

    def test_chain_with_no_filters_returns_all_stocks(self, sample_stocks):
        """FilterChain with no filters returns original list unchanged."""
        empty_chain = FilterChain([])

        result = empty_chain.apply(sample_stocks)

        assert len(result) == len(sample_stocks)
        assert result == sample_stocks

    def test_chain_returns_empty_when_all_filtered(self, sample_stocks):
        """FilterChain returns empty list when all stocks filtered, no exception."""
        # Filter that rejects everything
        reject_all_filter = MagicMock(spec=FilterPort)
        reject_all_filter.filter_name = "reject_all"
        reject_all_filter.apply.return_value = []

        chain = FilterChain([reject_all_filter])

        result = chain.apply(sample_stocks)

        assert result == []
        assert isinstance(result, list)

    def test_chain_output_is_input_of_next_filter(self, sample_stocks):
        """Verify that output of filter N becomes input of filter N+1."""
        filter1 = MagicMock(spec=FilterPort)
        filter1.filter_name = "first"
        filter1.apply.return_value = [{"ticker": "INTERMEDIATE"}]

        filter2 = MagicMock(spec=FilterPort)
        filter2.filter_name = "second"
        filter2.apply.return_value = [{"ticker": "FINAL"}]

        chain = FilterChain([filter1, filter2])

        result = chain.apply(sample_stocks)

        # Verify filter1 received original input
        filter1.apply.assert_called_once_with(sample_stocks)

        # Verify filter2 received filter1's output as input
        filter2.apply.assert_called_once_with([{"ticker": "INTERMEDIATE"}])

        # Verify final result is filter2's output
        assert result == [{"ticker": "FINAL"}]

    def test_chain_with_single_filter(self, sample_stocks):
        """FilterChain with single filter works correctly."""
        single_filter = MagicMock(spec=FilterPort)
        single_filter.filter_name = "single"
        single_filter.apply.return_value = [sample_stocks[0]]  # Return first stock only

        chain = FilterChain([single_filter])

        result = chain.apply(sample_stocks)

        assert len(result) == 1
        assert result[0] == sample_stocks[0]
        single_filter.apply.assert_called_once_with(sample_stocks)

    def test_chain_does_not_mutate_input(self, mock_filters, sample_stocks):
        """FilterChain does not mutate the original input list."""
        original_length = len(sample_stocks)
        original_first_ticker = sample_stocks[0]["ticker"]

        chain = FilterChain(mock_filters)
        result = chain.apply(sample_stocks)

        # Verify original list is unchanged
        assert len(sample_stocks) == original_length
        assert sample_stocks[0]["ticker"] == original_first_ticker
        assert id(result) != id(sample_stocks)  # Different objects

    def test_chain_filter_count_tracking(self, mock_filters, sample_stocks):
        """FilterChain tracks stock counts after each filter."""
        chain = FilterChain(mock_filters)

        chain.apply(sample_stocks)

        # Check filter log was created
        filter_log = chain.filter_log
        assert len(filter_log) == 2

        # First filter: 5 → 3 stocks (removed 2)
        assert filter_log[0]["filter"] == "mock_filter_1"
        assert filter_log[0]["before"] == 5
        assert filter_log[0]["after"] == 3
        assert filter_log[0]["removed"] == 2

        # Second filter: 3 → 2 stocks (removed 1)
        assert filter_log[1]["filter"] == "mock_filter_2"
        assert filter_log[1]["before"] == 3
        assert filter_log[1]["after"] == 2
        assert filter_log[1]["removed"] == 1

    def test_chain_filter_log_property(self):
        """FilterChain filter_log property returns log of filter applications."""
        chain = FilterChain([])

        # Initially empty
        assert chain.filter_log == []

        # After applying (even with no filters)
        chain.apply([])
        assert chain.filter_log == []

    def test_chain_empty_input_returns_empty(self, mock_filters):
        """FilterChain with empty input returns empty list."""
        chain = FilterChain(mock_filters)

        result = chain.apply([])

        assert result == []
        assert isinstance(result, list)
