"""
Performance index definitions for Step 26: Performance Optimization.
These are the indexes added for query optimization.
Reference this file when adding new indexes.
"""

PERFORMANCE_INDEXES = [
    # analysis_log: most common query pattern
    # exists(market, date, executed=True)
    {
        "table": "analysis_log",
        "name": "ix_analysis_log_market_date_executed",
        "columns": ["market", "date", "executed"],
    },
    # positions: open positions by user
    # get_open_positions(user_id, status='open')
    {
        "table": "positions",
        "name": "ix_positions_user_id_status",
        "columns": ["user_id", "status"],
    },
    # notifications: unread by user
    # get_unread(user_id, is_read=False)
    {
        "table": "notifications",
        "name": "ix_notifications_is_read_created_at",
        "columns": ["is_read", "created_at"],
    },
    # decision_log: by user + ticker for behavior analysis
    {
        "table": "decision_log",
        "name": "ix_decision_log_user_ticker_created",
        "columns": ["user_id", "ticker", "created_at"],
    },
    # strategy_output: latest by ticker
    {
        "table": "strategy_output",
        "name": "ix_strategy_output_ticker_created",
        "columns": ["ticker", "created_at"],
    },
]