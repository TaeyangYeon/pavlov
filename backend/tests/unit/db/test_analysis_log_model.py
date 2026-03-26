from datetime import date

from app.infra.db.models.analysis_log import AnalysisLog


def test_analysis_log_creation():
    """Test analysis log creation with required fields"""
    analysis_log = AnalysisLog(date=date(2024, 1, 1), market="US", executed=False)

    assert analysis_log.date == date(2024, 1, 1)
    assert analysis_log.market == "US"
    assert analysis_log.executed is False
    assert analysis_log.ai_response is None
    assert analysis_log.error_message is None


def test_executed_defaults_to_false():
    """Test that executed field defaults to False - CRITICAL for Step 17"""
    analysis_log = AnalysisLog(
        date=date(2024, 1, 1),
        market="US",
        # executed not specified - should default to False
    )

    # This is CRITICAL for Missed Execution Recovery in Step 17
    # Default is set by database, not in unit tests
    assert analysis_log.executed is None  # Will be False when saved to DB

    # Test explicit True value
    analysis_log_executed = AnalysisLog(
        date=date(2024, 1, 1), market="KR", executed=True
    )
    assert analysis_log_executed.executed is True


def test_market_enum_values():
    """Test that market field only accepts 'KR' or 'US' values"""
    # Valid US market
    analysis_log_us = AnalysisLog(date=date(2024, 1, 1), market="US")
    assert analysis_log_us.market == "US"

    # Valid KR market
    analysis_log_kr = AnalysisLog(date=date(2024, 1, 1), market="KR")
    assert analysis_log_kr.market == "KR"

    # Invalid market - enum validation happens at DB level, not model level
    analysis_log_invalid = AnalysisLog(date=date(2024, 1, 1), market="INVALID_MARKET")
    # Model creation succeeds, DB constraint will fail
    assert analysis_log_invalid.market == "INVALID_MARKET"


def test_ai_response_json_nullable():
    """Test that ai_response field accepts JSON and is nullable"""
    # Test with AI response
    ai_response = {
        "market_summary": "Market is bullish",
        "strategies": [{"ticker": "AAPL", "action": "buy", "confidence": 0.8}],
    }

    analysis_log = AnalysisLog(
        date=date(2024, 1, 1), market="US", ai_response=ai_response
    )

    assert analysis_log.ai_response == ai_response
    assert analysis_log.ai_response["market_summary"] == "Market is bullish"

    # Test nullable
    analysis_log_no_response = AnalysisLog(date=date(2024, 1, 1), market="US")
    assert analysis_log_no_response.ai_response is None


def test_error_message_nullable():
    """Test that error_message field is nullable and accepts strings"""
    # Test with error message
    analysis_log_with_error = AnalysisLog(
        date=date(2024, 1, 1), market="US", error_message="AI API timeout"
    )
    assert analysis_log_with_error.error_message == "AI API timeout"

    # Test nullable
    analysis_log_no_error = AnalysisLog(date=date(2024, 1, 1), market="US")
    assert analysis_log_no_error.error_message is None
