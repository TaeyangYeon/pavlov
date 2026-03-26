from app.domain.ai.schemas import AIPromptOutput, ValidationResult


def validate_ai_output(output: AIPromptOutput) -> ValidationResult:
    """
    Validate AI output according to business rules.
    
    Returns ValidationResult instead of raising exceptions.
    """
    errors = []
    
    # Validate each strategy
    for i, strategy in enumerate(output.strategies):
        strategy_prefix = f"Strategy {i+1} ({strategy.ticker})"
        
        # Rule 1: Reject strategies with confidence < 0.3
        if strategy.confidence < 0.3:
            errors.append(f"{strategy_prefix}: Confidence {strategy.confidence} is below minimum threshold 0.3")
        
        # Rule 2: Buy action must have take_profit levels
        if strategy.action == "buy" and not strategy.take_profit:
            errors.append(f"{strategy_prefix}: Buy action requires take_profit levels to be defined")
        
        # Rule 3: Full exit action should not have stop_loss levels
        if strategy.action == "full_exit" and strategy.stop_loss:
            errors.append(f"{strategy_prefix}: Full exit action should not have stop_loss levels")
        
        # Rule 4: Validate take_profit sell_ratio totals
        if strategy.take_profit:
            total_tp_ratio = sum(level.sell_ratio for level in strategy.take_profit)
            if total_tp_ratio > 1.0:
                errors.append(f"{strategy_prefix}: Take profit sell_ratio total ({total_tp_ratio:.2f}) exceeds 1.0")
        
        # Rule 5: Validate stop_loss sell_ratio totals
        if strategy.stop_loss:
            total_sl_ratio = sum(level.sell_ratio for level in strategy.stop_loss)
            if total_sl_ratio > 1.0:
                errors.append(f"{strategy_prefix}: Stop loss sell_ratio total ({total_sl_ratio:.2f}) exceeds 1.0")
        
        # Rule 6: Validate ticker is valid string
        if not strategy.ticker or not isinstance(strategy.ticker, str) or not strategy.ticker.strip():
            errors.append(f"{strategy_prefix}: Ticker must be a valid non-empty string")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors
    )