"""
Slow Query Logger for Step 26: Performance Optimization.
Logs SQL queries that exceed threshold using SQLAlchemy event hooks.
Never logs query parameters for security.
"""

import time
from typing import List, Dict, Any

from sqlalchemy import event
from sqlalchemy.engine import Engine


class SlowQueryLogger:
    """
    Logs SQL queries that exceed threshold.
    Attached to SQLAlchemy engine via event hooks.
    Never logs query parameters (security).
    """

    def __init__(self, threshold_ms: int = 100):
        self._threshold_ms = threshold_ms
        self._slow_queries: List[Dict[str, Any]] = []

    def attach(self, engine: Engine) -> None:
        """Attach event listeners to engine."""

        @event.listens_for(engine, "before_cursor_execute")
        def before_execute(
            conn, cursor, statement, parameters,
            context, executemany
        ):
            """Record query start time."""
            conn.info.setdefault("query_start_time", [])
            conn.info["query_start_time"].append(
                time.time()
            )

        @event.listens_for(engine, "after_cursor_execute")
        def after_execute(
            conn, cursor, statement, parameters,
            context, executemany
        ):
            """Check query execution time and log slow queries."""
            total = time.time() - (
                conn.info["query_start_time"].pop(-1)
            )
            elapsed_ms = total * 1000

            if elapsed_ms > self._threshold_ms:
                # Truncate statement, never log params
                stmt_preview = statement[:200].replace(
                    '\n', ' '
                ).strip()
                log_entry = {
                    "elapsed_ms": round(elapsed_ms, 2),
                    "statement_preview": stmt_preview,
                    "timestamp": time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
                self._slow_queries.append(log_entry)
                print(
                    f"[SlowQuery] {elapsed_ms:.1f}ms: "
                    f"{stmt_preview[:100]}..."
                )

    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get list of slow queries."""
        return list(self._slow_queries)

    def get_count(self) -> int:
        """Get count of slow queries."""
        return len(self._slow_queries)

    def clear(self) -> None:
        """Clear slow query log."""
        self._slow_queries.clear()