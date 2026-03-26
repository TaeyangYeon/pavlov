from app.domain.ai.schemas import AIPromptInput


def build_prompt(input_data: AIPromptInput) -> str:
    """
    Build AI prompt from validated input data.

    Pure function with no side effects.
    Returns complete prompt string ready for AI API call.
    """

    # System role and requirements
    prompt_parts = [
        (
            "당신은 전문 투자 분석가입니다. 다음 시장 데이터와 기술적 지표를 "
            "바탕으로 투자 전략을 제시해주세요."
        ),
        "",
        f"**분석 시장**: {input_data.market}",
        f"**분석 일자**: {input_data.date}",
        "",
    ]

    # Market analysis section
    if input_data.filtered_stocks:
        prompt_parts.extend(["## 기술적 필터를 통과한 종목들", ""])

        for stock in input_data.filtered_stocks:
            prompt_parts.extend(
                [
                    f"### {stock.ticker} ({stock.name})",
                    f"- 현재가: ${stock.close:.2f}",
                    f"- 거래량 비율: {stock.volume_ratio:.2f}x",
                    f"- RSI(14): {stock.rsi_14:.1f}",
                    f"- MA(20): ${stock.ma_20:.2f}",
                    f"- MA(60): ${stock.ma_60:.2f}",
                    f"- ATR(14): {stock.atr_14:.2f}",
                    "",
                ]
            )
    else:
        prompt_parts.extend(
            ["## 기술적 필터를 통과한 종목들", "필터를 통과한 종목이 없습니다.", ""]
        )

    # Current positions section
    if input_data.held_positions:
        prompt_parts.extend(["## 현재 보유 포지션", ""])

        for position in input_data.held_positions:
            pnl_sign = "+" if position.current_pnl_pct >= 0 else ""
            prompt_parts.extend(
                [
                    f"### {position.ticker}",
                    f"- 평균단가: ${position.avg_price:.2f}",
                    f"- 보유수량: {position.quantity}주",
                    f"- 현재 손익률: {pnl_sign}{position.current_pnl_pct:.2f}%",
                    "",
                ]
            )
    else:
        prompt_parts.extend(["## 현재 보유 포지션", "보유 중인 포지션이 없습니다.", ""])

    # Output format instructions
    prompt_parts.extend(
        [
            "## 출력 요구사항",
            "",
            "다음 JSON 형식으로 정확히 응답해주세요:",
            "",
            "```json",
            "{",
            '  "market_summary": "시장 전반 상황 분석 (최대 200자)",',
            '  "strategies": [',
            "    {",
            '      "ticker": "종목코드",',
            '      "action": "hold|buy|partial_sell|full_exit",',
            '      "take_profit": [',
            '        {"pct": 5.0, "sell_ratio": 0.5},',
            '        {"pct": 10.0, "sell_ratio": 0.5}',
            "      ],",
            '      "stop_loss": [',
            '        {"pct": -3.0, "sell_ratio": 1.0}',
            "      ],",
            '      "rationale": "전략 근거 (최대 100자)",',
            '      "confidence": 0.8',
            "    }",
            "  ]",
            "}",
            "```",
            "",
            "## 전략 수립 가이드라인",
            "",
            "1. **신뢰도 점수 (confidence)**:",
            "   - 0.8-1.0: 매우 확실한 전략",
            "   - 0.6-0.7: 보통 확실성",
            "   - 0.3-0.5: 낮은 확실성",
            "   - 0.3 미만: 권장하지 않음",
            "",
            "2. **액션별 요구사항**:",
            '   - "buy": take_profit 레벨 필수 설정',
            '   - "full_exit": stop_loss 레벨 설정하지 말 것',
            '   - "partial_sell": 적절한 비율로 분할 매도',
            "",
            "3. **리스크 관리**:",
            "   - take_profit의 sell_ratio 합계는 1.0 이하",
            "   - stop_loss는 명확한 손실 한계점 설정",
            "   - 보유 포지션의 현재 손익률 고려",
            "",
            "반드시 JSON 형식으로만 응답하고, 추가 설명은 포함하지 마세요.",
        ]
    )

    return "\n".join(prompt_parts)
