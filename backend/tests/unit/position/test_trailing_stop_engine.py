"""
Unit tests for TrailingStopEngine (TDD - Red Phase).
All tests should FAIL before implementation.
"""

from decimal import Decimal

import pytest

from app.domain.position.schemas import TrailingStopConfig, TrailingStopResult
from app.domain.position.trailing_stop_engine import TrailingStopEngine


class TestTrailingStopEngine:
    """Test suite for TrailingStopEngine."""

    def setup_method(self):
        """Setup test instance."""
        self.engine = TrailingStopEngine()

    # ── RATCHET MECHANISM TESTS ──

    def test_hwm_updates_when_price_rises(self):
        """Test high water mark updates when price rises."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        result = self.engine.evaluate(
            current_price=Decimal("120"),
            high_water_mark=Decimal("100"),
            avg_price=Decimal("100"),
            config=config,
        )
        
        assert result.high_water_mark == Decimal("120.0000")
        assert not result.triggered

    def test_hwm_stays_fixed_when_price_falls(self):
        """Test high water mark stays fixed when price falls."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        # Use price above stop but below HWM to test ratchet without trigger
        result = self.engine.evaluate(
            current_price=Decimal("120"),  # Above stop (117) but below HWM (130)
            high_water_mark=Decimal("130"),
            avg_price=Decimal("100"),
            config=config,
        )
        
        assert result.high_water_mark == Decimal("130.0000")  # no change (ratchet)
        assert not result.triggered  # 120 > 117 → not triggered

    def test_hwm_stays_fixed_at_equal_price(self):
        """Test high water mark stays fixed when price equals HWM."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        result = self.engine.evaluate(
            current_price=Decimal("130"),
            high_water_mark=Decimal("130"),
            avg_price=Decimal("100"),
            config=config,
        )
        
        assert result.high_water_mark == Decimal("130.0000")
        assert not result.triggered

    def test_hwm_initial_set_to_avg_price_when_none(self):
        """Test HWM initially set to avg_price when None."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        result = self.engine.evaluate(
            current_price=Decimal("100"),
            high_water_mark=None,
            avg_price=Decimal("100"),
            config=config,
        )
        
        assert result.high_water_mark == Decimal("100.0000")

    def test_hwm_initial_uses_current_if_higher_than_avg(self):
        """Test HWM uses current price if higher than avg_price."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        result = self.engine.evaluate(
            current_price=Decimal("120"),
            high_water_mark=None,
            avg_price=Decimal("100"),
            config=config,
        )
        
        assert result.high_water_mark == Decimal("120.0000")

    # ── PERCENTAGE MODE TESTS ──

    @pytest.mark.parametrize(
        "hwm,current,trail_pct,expected_stop,expected_triggered",
        [
            # stop = hwm × (1 - trail_pct/100)
            (Decimal("130"), Decimal("120"), Decimal("10"),
             Decimal("117.0000"), False),  # 120 > 117 → hold

            (Decimal("130"), Decimal("117"), Decimal("10"),
             Decimal("117.0000"), True),   # 117 <= 117 → triggered

            (Decimal("130"), Decimal("116"), Decimal("10"),
             Decimal("117.0000"), True),   # 116 < 117 → triggered

            (Decimal("100"), Decimal("95"), Decimal("5"),
             Decimal("95.0000"), True),    # exact 5% from 100

            (Decimal("100"), Decimal("95.0001"), Decimal("5"),
             Decimal("95.0000"), False),   # just above stop → hold
        ]
    )
    def test_percentage_mode_trigger(
        self, hwm, current, trail_pct, expected_stop, expected_triggered
    ):
        """Test percentage mode trigger conditions."""
        config = TrailingStopConfig(mode="percentage", trail_pct=trail_pct)
        
        result = self.engine.evaluate(
            current_price=current,
            high_water_mark=hwm,
            avg_price=Decimal("100"),  # doesn't matter for this test
            config=config,
        )
        
        assert result.stop_price == expected_stop
        assert result.triggered == expected_triggered
        assert result.action == ("full_exit" if expected_triggered else "hold")

    # ── ATR MODE TESTS ──

    @pytest.mark.parametrize(
        "hwm,current,atr_mult,atr_val,expected_stop,expected_triggered",
        [
            # stop = hwm - (atr_mult × atr_val)
            (Decimal("130"), Decimal("122"), Decimal("2"), Decimal("4"),
             Decimal("122.0000"), True),   # stop=130-8=122, 122<=122

            (Decimal("130"), Decimal("122.0001"), Decimal("2"), Decimal("4"),
             Decimal("122.0000"), False),  # just above stop → hold

            (Decimal("130"), Decimal("120"), Decimal("3"), Decimal("5"),
             Decimal("115.0000"), False),  # stop=130-15=115, 120>115

            (Decimal("100"), Decimal("85"), Decimal("2"), Decimal("10"),
             Decimal("80.0000"), False),   # stop=100-20=80, 85>80
        ]
    )
    def test_atr_mode_trigger(
        self, hwm, current, atr_mult, atr_val, expected_stop, expected_triggered
    ):
        """Test ATR mode trigger conditions."""
        config = TrailingStopConfig(
            mode="atr",
            atr_multiplier=atr_mult,
            atr_value=atr_val
        )
        
        result = self.engine.evaluate(
            current_price=current,
            high_water_mark=hwm,
            avg_price=Decimal("100"),  # doesn't matter for this test
            config=config,
        )
        
        assert result.stop_price == expected_stop
        assert result.triggered == expected_triggered
        assert result.action == ("full_exit" if expected_triggered else "hold")

    # ── PRICE SEQUENCE TESTS ──

    def test_rising_then_falling_sequence(self):
        """Simulate realistic price movement with ratchet mechanism."""
        prices = [
            Decimal("100"), Decimal("105"), Decimal("110"), 
            Decimal("120"), Decimal("130"), Decimal("125"), 
            Decimal("120"), Decimal("118"), Decimal("117")
        ]
        avg_price = Decimal("100")
        trail_pct = Decimal("10")
        config = TrailingStopConfig(mode="percentage", trail_pct=trail_pct)

        hwm = None  # Start with None
        
        # Expected behavior:
        expected_results = [
            # price=100: hwm=100, stop=90, hold
            (Decimal("100"), Decimal("100.0000"), Decimal("90.0000"), False),
            # price=105: hwm=105, stop=94.5, hold  
            (Decimal("105"), Decimal("105.0000"), Decimal("94.5000"), False),
            # price=110: hwm=110, stop=99, hold
            (Decimal("110"), Decimal("110.0000"), Decimal("99.0000"), False),
            # price=120: hwm=120, stop=108, hold
            (Decimal("120"), Decimal("120.0000"), Decimal("108.0000"), False),
            # price=130: hwm=130, stop=117, hold
            (Decimal("130"), Decimal("130.0000"), Decimal("117.0000"), False),
            # price=125: hwm=130, stop=117, hold  ← HWM stays at 130
            (Decimal("125"), Decimal("130.0000"), Decimal("117.0000"), False),
            # price=120: hwm=130, stop=117, hold
            (Decimal("120"), Decimal("130.0000"), Decimal("117.0000"), False),
            # price=118: hwm=130, stop=117, hold
            (Decimal("118"), Decimal("130.0000"), Decimal("117.0000"), False),
            # price=117: hwm=130, stop=117, TRIGGERED ← full_exit
            (Decimal("117"), Decimal("130.0000"), Decimal("117.0000"), True),
        ]

        for i, (price, expected_hwm, expected_stop, expected_triggered) in enumerate(expected_results):
            result = self.engine.evaluate(
                current_price=price,
                high_water_mark=hwm,
                avg_price=avg_price,
                config=config,
            )
            
            assert result.current_price == price, f"Step {i}: wrong current_price"
            assert result.high_water_mark == expected_hwm, f"Step {i}: wrong HWM"
            assert result.stop_price == expected_stop, f"Step {i}: wrong stop_price"
            assert result.triggered == expected_triggered, f"Step {i}: wrong triggered"
            
            # Update HWM for next iteration (simulate persistence)
            hwm = result.high_water_mark

    def test_never_triggered_in_uptrend(self):
        """Test trailing stop never triggers in pure uptrend."""
        prices = [Decimal("100"), Decimal("105"), Decimal("110"), Decimal("115"), Decimal("120")]
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        hwm = None
        for price in prices:
            result = self.engine.evaluate(
                current_price=price,
                high_water_mark=hwm,
                avg_price=Decimal("100"),
                config=config,
            )
            
            assert not result.triggered, f"Should not trigger at price {price}"
            assert result.action == "hold"
            hwm = result.high_water_mark

    def test_immediately_triggered_on_drop(self):
        """Test immediate trigger when price drops below stop."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("5"))
        
        result = self.engine.evaluate(
            current_price=Decimal("94"),
            high_water_mark=None,  # First eval
            avg_price=Decimal("100"),
            config=config,
        )
        
        # hwm set to max(100, 94) = 100, stop = 100 * 0.95 = 95
        # 94 < 95 → triggered immediately
        assert result.high_water_mark == Decimal("100.0000")
        assert result.stop_price == Decimal("95.0000") 
        assert result.triggered
        assert result.action == "full_exit"

    # ── DISTANCE TO STOP TESTS ──

    def test_distance_to_stop_calculation(self):
        """Test distance to stop percentage calculation."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        result = self.engine.evaluate(
            current_price=Decimal("120"),
            high_water_mark=Decimal("130"),
            avg_price=Decimal("100"),
            config=config,
        )
        
        # stop = 130 * 0.9 = 117
        # distance = (120-117)/120 * 100 = 2.5000%
        assert result.stop_price == Decimal("117.0000")
        assert result.distance_to_stop_pct == Decimal("2.5000")

    def test_distance_to_stop_when_triggered(self):
        """Test distance to stop when triggered (negative or zero)."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        result = self.engine.evaluate(
            current_price=Decimal("116"),  # Below stop of 117
            high_water_mark=Decimal("130"),
            avg_price=Decimal("100"),
            config=config,
        )
        
        assert result.triggered
        assert result.distance_to_stop_pct <= Decimal("0")

    # ── EDGE CASES ──

    def test_zero_trail_pct_raises(self):
        """Test zero trail_pct raises validation error."""
        with pytest.raises(ValueError):
            TrailingStopConfig(mode="percentage", trail_pct=Decimal("0"))

    def test_missing_trail_pct_for_percentage_mode_raises(self):
        """Test missing trail_pct for percentage mode raises validation error."""
        with pytest.raises(ValueError, match="trail_pct required"):
            TrailingStopConfig(mode="percentage")

    def test_missing_atr_for_atr_mode_raises(self):
        """Test missing ATR values for ATR mode raises validation error."""
        with pytest.raises(ValueError, match="atr_multiplier and atr_value required"):
            TrailingStopConfig(mode="atr", atr_multiplier=Decimal("2"))

    def test_trail_distance_pct_calculation(self):
        """Test trail distance percentage calculation."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        result = self.engine.evaluate(
            current_price=Decimal("120"),
            high_water_mark=Decimal("130"),
            avg_price=Decimal("100"),
            config=config,
        )
        
        # trail_distance = (130-117)/130 * 100 = 10.0000%
        assert result.trail_distance_pct == Decimal("10.0000")

    def test_hwm_precision_decimal(self):
        """Test HWM maintains decimal precision."""
        config = TrailingStopConfig(mode="percentage", trail_pct=Decimal("10"))
        
        result = self.engine.evaluate(
            current_price=Decimal("100.1234"),
            high_water_mark=None,
            avg_price=Decimal("100"),
            config=config,
        )
        
        assert result.high_water_mark == Decimal("100.1234")
        # Ensure precision is maintained in calculations
        assert isinstance(result.high_water_mark, Decimal)
        assert isinstance(result.stop_price, Decimal)
        assert isinstance(result.trail_distance_pct, Decimal)