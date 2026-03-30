"""
Strategy Integration Engine.
Merges AI strategies with position engine results.
Final orchestrator of Phase 3.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.domain.ai.schemas import AIPromptOutput, StockStrategy
from app.domain.position.schemas import (
    TpSlEvaluationResponse,
    TrailingStopConfig,
    TrailingStopEvaluationResponse,
)
from app.domain.position.service import PositionService
from app.domain.strategy.change_detector import ChangeDetector
from app.domain.strategy.schemas import (
    ACTION_SEVERITY,
    StrategyRunResult,
    UnifiedStrategy,
)
from app.infra.db.repositories.strategy_output_repository import (
    StrategyOutputRepository,
)


class StrategyIntegrationEngine:
    """
    Merges AI strategies with position engine results.
    Final orchestrator of Phase 3.

    Depends on abstractions only (SOLID D principle).
    """

    def __init__(
        self,
        position_service: PositionService,
        strategy_repository: StrategyOutputRepository,
        change_detector: ChangeDetector,
    ):
        self._position_service = position_service
        self._strategy_repository = strategy_repository
        self._change_detector = change_detector

    async def run(
        self,
        market: str,
        run_date: date,
        ai_output: AIPromptOutput | None,
        analysis_log_id: UUID | None,
        trailing_configs: dict[str, TrailingStopConfig] | None = None,
    ) -> StrategyRunResult:
        """
        Run full strategy integration for a market.

        Args:
            market: "KR" or "US"
            run_date: analysis date
            ai_output: from AnalysisPipeline (may be None)
            analysis_log_id: for DB linkage
            trailing_configs: {ticker: config} optional

        Returns:
            Complete strategy run result
        """
        if trailing_configs is None:
            trailing_configs = {}

        strategies: list[UnifiedStrategy] = []

        # Step 1: Get AI strategies (if available)
        ai_strategies: dict[str, StockStrategy] = {}
        if ai_output:
            ai_strategies = {s.ticker: s for s in ai_output.strategies}

        # Step 2: Get open positions
        open_positions = await self._position_service.get_open_positions()
        position_tickers = {p.ticker for p in open_positions}

        # Step 3: Process AI tickers (may or may not have position)
        for ticker, ai_strat in ai_strategies.items():
            tp_sl_result = None
            trailing_result = None

            # Evaluate position engine if position exists
            if ticker in position_tickers:
                position = next(p for p in open_positions if p.ticker == ticker)
                try:
                    tp_sl_result = await self._position_service.evaluate_tp_sl(
                        position.id,
                        # Use AI confidence as proxy price signal
                        # Real price from market data in Step 16
                        position.avg_price
                        * Decimal(str(1 + ai_strat.confidence * 0.1)),
                        ai_strat.take_profit,
                        ai_strat.stop_loss,
                    )
                    if ticker in trailing_configs:
                        trailing_result = (
                            await self._position_service.evaluate_trailing_stop(
                                position.id,
                                position.avg_price
                                * Decimal(str(1 + ai_strat.confidence * 0.1)),
                                trailing_configs[ticker],
                            )
                        )
                except Exception as e:
                    print(f"[Strategy] Position eval failed for {ticker}: {e}")

            # Merge AI + position engine
            unified = self._merge(
                ticker=ticker,
                market=market,
                ai_strategy=ai_strat,
                tp_sl_result=tp_sl_result,
                trailing_result=trailing_result,
            )

            # Change detection
            last = await self._strategy_repository.get_latest(ticker, market, run_date)
            unified.changed_from_last = self._change_detector.has_changed(unified, last)

            # Save if changed
            if unified.changed_from_last and analysis_log_id:
                await self._strategy_repository.save(analysis_log_id, unified)

            strategies.append(unified)

        # Step 4: Process position-only tickers
        # (open positions not covered by AI output)
        for position in open_positions:
            if position.ticker in ai_strategies:
                continue  # already processed above

            tp_sl_result = None
            trailing_result = None
            try:
                tp_sl_result = await self._position_service.evaluate_tp_sl(
                    position.id,
                    position.avg_price,
                    [],  # no AI TP levels
                    [],  # no AI SL levels
                )
                if position.ticker in trailing_configs:
                    trailing_result = (
                        await self._position_service.evaluate_trailing_stop(
                            position.id,
                            position.avg_price,
                            trailing_configs[position.ticker],
                        )
                    )
            except Exception:
                pass

            unified = self._merge(
                ticker=position.ticker,
                market=market,
                ai_strategy=None,
                tp_sl_result=tp_sl_result,
                trailing_result=trailing_result,
            )

            last = await self._strategy_repository.get_latest(
                position.ticker, market, run_date
            )
            unified.changed_from_last = self._change_detector.has_changed(unified, last)

            if unified.changed_from_last and analysis_log_id:
                await self._strategy_repository.save(analysis_log_id, unified)

            strategies.append(unified)

        changed_count = sum(1 for s in strategies if s.changed_from_last)

        return StrategyRunResult(
            market=market,
            run_date=run_date,
            strategies=strategies,
            total_tickers_analyzed=len(strategies),
            changed_count=changed_count,
            analysis_log_id=analysis_log_id,
        )

    def _merge(
        self,
        ticker: str,
        market: str,
        ai_strategy: StockStrategy | None,
        tp_sl_result: TpSlEvaluationResponse | None,
        trailing_result: TrailingStopEvaluationResponse | None,
    ) -> UnifiedStrategy:
        """
        Merge AI strategy with position engine results.
        Severity hierarchy: hold < buy < partial_sell < full_exit
        SL/exit actions override AI on conflicts.
        """
        ai_action = ai_strategy.action if ai_strategy else "hold"
        engine_action = "hold"
        sell_quantity = Decimal("0.0000")
        realized_pnl = Decimal("0.0000")
        engine_rationale = ""

        # Determine position engine action (trailing takes precedence)
        if trailing_result and trailing_result.triggered:
            engine_action = "full_exit"
            engine_rationale = (
                f"Trailing stop triggered at {trailing_result.stop_price}"
            )
        elif tp_sl_result and tp_sl_result.action != "hold":
            engine_action = tp_sl_result.action
            sell_quantity = tp_sl_result.sell_quantity
            realized_pnl = tp_sl_result.realized_pnl_estimate
            triggered = tp_sl_result.triggered_by.upper()
            pct = tp_sl_result.triggered_level_pct
            engine_rationale = f"{triggered} triggered at {pct}%"

        # Merge actions by severity
        ai_severity = ACTION_SEVERITY.get(ai_action, 0)
        engine_severity = ACTION_SEVERITY.get(engine_action, 0)

        if engine_action == "full_exit":
            final_action = "full_exit"
            source = "position_engine"
        elif ai_action == "full_exit":
            final_action = "full_exit"
            source = "ai"
        elif engine_severity > ai_severity:
            final_action = engine_action
            source = "position_engine"
        elif ai_severity > engine_severity:
            final_action = ai_action
            source = "ai"
        else:
            final_action = ai_action
            source = "merged"

        # Determine sell_quantity for final action
        if final_action in ("partial_sell", "full_exit"):
            if tp_sl_result and tp_sl_result.action != "hold":
                sell_quantity = tp_sl_result.sell_quantity
                realized_pnl = tp_sl_result.realized_pnl_estimate

        # Build rationale
        ai_rationale = ai_strategy.rationale if ai_strategy else ""
        if ai_rationale and engine_rationale:
            rationale = f"AI: {ai_rationale} | Engine: {engine_rationale}"[:200]
        elif ai_rationale:
            rationale = ai_rationale[:200]
        elif engine_rationale:
            rationale = engine_rationale[:200]
        else:
            rationale = "No specific signal"

        # Confidence
        if ai_strategy:
            confidence = Decimal(str(ai_strategy.confidence))
            if source == "merged" and engine_severity > 0:
                # Lower confidence when merging conflicting signals
                confidence = min(confidence, Decimal("0.9"))
        else:
            confidence = Decimal("1.0")  # Deterministic rule = 100% confidence

        return UnifiedStrategy(
            ticker=ticker,
            market=market,
            final_action=final_action,
            action_source=source,
            ai_strategy=ai_strategy,
            tp_sl_result=tp_sl_result,
            trailing_result=trailing_result,
            confidence=confidence,
            rationale=rationale,
            sell_quantity=sell_quantity,
            realized_pnl_estimate=realized_pnl,
        )
