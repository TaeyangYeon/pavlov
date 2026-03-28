"""Enhanced unit tests for prompt_builder.py."""

from app.domain.ai.prompt_builder import build_prompt
from app.domain.ai.schemas import AIPromptInput, StockIndicators


class TestPromptBuilderEnhanced:
    """Test enhanced prompt builder functionality."""

    def test_prompt_contains_json_schema_template(self):
        """Test that prompt includes JSON schema template."""
        # Setup test data
        prompt_input = AIPromptInput(
            market="KR",
            date="2024-01-01",
            filtered_stocks=[
                StockIndicators(
                    ticker="005930",
                    name="삼성전자",
                    market="KR",
                    close=80000.0,
                    volume_ratio=1.2,
                    rsi_14=65.0,
                    ma_20=78000.0,
                    ma_60=76000.0,
                    atr_14=2000.0
                )
            ],
            held_positions=[]
        )

        # Build prompt
        prompt = build_prompt(prompt_input)

        # Verify JSON schema template is included
        assert "market_summary" in prompt
        assert '"strategies": [' in prompt
        assert '"ticker": "종목코드"' in prompt
        assert '"action": "hold|buy|partial_sell|full_exit"' in prompt

    def test_prompt_contains_korean_instruction(self):
        """Test that prompt contains Korean language instruction."""
        # Setup test data
        prompt_input = AIPromptInput(
            market="KR",
            date="2024-01-01",
            filtered_stocks=[],
            held_positions=[]
        )

        # Build prompt
        prompt = build_prompt(prompt_input)

        # Verify Korean instruction
        assert "한국어" in prompt

    def test_prompt_contains_confidence_instruction(self):
        """Test that prompt contains confidence range instruction."""
        # Setup test data
        prompt_input = AIPromptInput(
            market="KR",
            date="2024-01-01",
            filtered_stocks=[],
            held_positions=[]
        )

        # Build prompt
        prompt = build_prompt(prompt_input)

        # Verify confidence range instruction
        assert "0.0" in prompt
        assert "1.0" in prompt
        assert "confidence" in prompt

    def test_prompt_contains_max_length_instructions(self):
        """Test that prompt contains max length instructions."""
        # Setup test data
        prompt_input = AIPromptInput(
            market="KR",
            date="2024-01-01",
            filtered_stocks=[],
            held_positions=[]
        )

        # Build prompt
        prompt = build_prompt(prompt_input)

        # Verify max length instructions
        assert "200자 이내" in prompt  # market_summary max length
        assert "100자 이내" in prompt  # rationale max length

    def test_prompt_ends_with_json_instruction(self):
        """Test that prompt ends with JSON-only instruction."""
        # Setup test data
        prompt_input = AIPromptInput(
            market="KR",
            date="2024-01-01",
            filtered_stocks=[],
            held_positions=[]
        )

        # Build prompt
        prompt = build_prompt(prompt_input)

        # Verify prompt ends with JSON instruction
        lines = prompt.strip().split("\n")
        last_meaningful_lines = [line for line in lines[-10:] if line.strip()]

        # Should contain JSON-only instruction near the end
        json_instruction_found = False
        for line in last_meaningful_lines:
            if "JSON" in line and ("외" in line or "포함하지 말" in line):
                json_instruction_found = True
                break

        assert json_instruction_found, "Prompt should end with JSON-only instruction"

