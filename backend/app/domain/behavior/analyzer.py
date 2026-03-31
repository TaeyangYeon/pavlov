"""
Behavioral pattern analysis engine for emotional suppression system.
Pure calculation class with no I/O dependencies.
"""

from collections import Counter
from datetime import datetime, timedelta
from app.domain.behavior.schemas import BehaviorReport, ImpulsePattern


class BehaviorAnalyzer:
    """
    Pure behavioral pattern analysis engine.
    No I/O, no async, no side effects.
    Input: decision_log rows + strategy history
    Output: BehaviorReport dataclass
    """

    RAPID_REVERSAL_HOURS = 24
    OVERTRADING_THRESHOLD = 3
    OVERTRADING_PERIOD_DAYS = 7

    def analyze(
        self,
        user_id: str,
        decisions: list[dict],
        analysis_period_days: int = 30,
    ) -> BehaviorReport:
        """
        Full behavioral analysis for a user.
        decisions: list of decision_log dicts with fields:
          ticker, action, price, quantity,
          ai_suggested, notes, created_at
        """
        total = len(decisions)

        # AI alignment
        alignment = self._calculate_alignment(decisions)

        # Impulse patterns
        patterns = self._detect_patterns(decisions)
        impulse_count = sum(
            1 for p in patterns
            if p.pattern_type == "rapid_reversal"
        )
        contradiction_count = sum(
            1 for p in patterns
            if p.pattern_type == "ai_contradiction"
        )

        # Overtrading
        overtrading = self._detect_overtrading(decisions)

        # Holding period (approximate from buy/sell pairs)
        avg_holding = self._calculate_avg_holding(decisions)

        # Most traded
        most_traded = self._most_traded_ticker(decisions)

        # Cooling-off warnings
        warnings = sum(
            1 for d in decisions
            if d.get("notes") and
            "cooling" in str(d.get("notes", "")).lower()
        )

        return BehaviorReport(
            user_id=user_id,
            analysis_period_days=analysis_period_days,
            total_trades=total,
            ai_alignment_rate=alignment["rate"],
            ai_aligned_count=alignment["aligned"],
            ai_contradicted_count=alignment["contradicted"],
            no_ai_data_count=alignment["no_data"],
            impulse_trade_count=impulse_count,
            contradiction_count=contradiction_count,
            overtrading_tickers=overtrading,
            avg_holding_days=avg_holding,
            most_traded_ticker=most_traded,
            cooling_off_warnings_received=warnings,
            patterns=patterns,
            generated_at=datetime.now(),
        )

    def _calculate_alignment(
        self, decisions: list[dict]
    ) -> dict:
        aligned = sum(
            1 for d in decisions
            if d.get("ai_suggested") is True
        )
        contradicted = sum(
            1 for d in decisions
            if d.get("ai_suggested") is False
            and not str(d.get("notes", ""))
                .lower()
                .startswith("no ai")
        )
        no_data = len(decisions) - aligned - contradicted
        denominator = aligned + contradicted
        rate = (
            round(aligned / denominator, 4)
            if denominator > 0 else 0.0
        )
        return {
            "rate": rate,
            "aligned": aligned,
            "contradicted": contradicted,
            "no_data": no_data,
        }

    def _detect_patterns(
        self, decisions: list[dict]
    ) -> list[ImpulsePattern]:
        patterns = []

        # Group by ticker
        by_ticker: dict[str, list[dict]] = {}
        for d in decisions:
            ticker = d["ticker"]
            if ticker not in by_ticker:
                by_ticker[ticker] = []
            by_ticker[ticker].append(d)

        for ticker, trades in by_ticker.items():
            # Sort by time
            sorted_trades = sorted(
                trades,
                key=lambda x: x["created_at"]
            )

            # Rapid reversal detection
            for i in range(len(sorted_trades) - 1):
                t1 = sorted_trades[i]
                t2 = sorted_trades[i + 1]
                t1_time = t1["created_at"]
                t2_time = t2["created_at"]
                if isinstance(t1_time, str):
                    t1_time = datetime.fromisoformat(t1_time)
                if isinstance(t2_time, str):
                    t2_time = datetime.fromisoformat(t2_time)

                hours_between = (
                    t2_time - t1_time
                ).total_seconds() / 3600

                is_reversal = (
                    t1["action"] == "buy"
                    and t2["action"] == "sell"
                    or t1["action"] == "sell"
                    and t2["action"] == "buy"
                )

                if (
                    hours_between < self.RAPID_REVERSAL_HOURS
                    and is_reversal
                ):
                    patterns.append(ImpulsePattern(
                        pattern_type="rapid_reversal",
                        ticker=ticker,
                        detected_at=t2_time,
                        description=(
                            f"{ticker}: {t1['action']} → "
                            f"{t2['action']} within "
                            f"{hours_between:.1f}h"
                        ),
                    ))

        return patterns

    def _detect_overtrading(
        self, decisions: list[dict]
    ) -> list[str]:
        cutoff = (
            datetime.now()
            - timedelta(days=self.OVERTRADING_PERIOD_DAYS)
        )
        recent = []
        for d in decisions:
            created = d["created_at"]
            if isinstance(created, str):
                created = datetime.fromisoformat(created)
            if created >= cutoff:
                recent.append(d["ticker"])

        counts = Counter(recent)
        return [
            ticker for ticker, count in counts.items()
            if count >= self.OVERTRADING_THRESHOLD
        ]

    def _calculate_avg_holding(
        self, decisions: list[dict]
    ) -> float:
        holding_days = []
        by_ticker: dict[str, list[dict]] = {}
        for d in decisions:
            ticker = d["ticker"]
            if ticker not in by_ticker:
                by_ticker[ticker] = []
            by_ticker[ticker].append(d)

        for ticker, trades in by_ticker.items():
            buys = [
                t for t in trades if t["action"] == "buy"
            ]
            sells = [
                t for t in trades if t["action"] == "sell"
            ]
            for buy in buys:
                for sell in sells:
                    buy_time = buy["created_at"]
                    sell_time = sell["created_at"]
                    if isinstance(buy_time, str):
                        buy_time = datetime.fromisoformat(
                            buy_time
                        )
                    if isinstance(sell_time, str):
                        sell_time = datetime.fromisoformat(
                            sell_time
                        )
                    if sell_time > buy_time:
                        days = (
                            sell_time - buy_time
                        ).total_seconds() / 86400
                        holding_days.append(days)
                        break

        if not holding_days:
            return 0.0
        return round(
            sum(holding_days) / len(holding_days), 2
        )

    def _most_traded_ticker(
        self, decisions: list[dict]
    ) -> str | None:
        if not decisions:
            return None
        counts = Counter(d["ticker"] for d in decisions)
        return counts.most_common(1)[0][0]