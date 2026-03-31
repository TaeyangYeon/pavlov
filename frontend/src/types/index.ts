// Position types
export interface PositionEntry {
  price: string;
  quantity: string;
  entered_at: string;
}

export interface Position {
  id: string;
  ticker: string;
  market: "KR" | "US";
  entries: PositionEntry[];
  avg_price: string;
  status: "open" | "closed";
  created_at: string;
}

export interface PositionWithPnL extends Position {
  current_price: string;
  unrealized_pnl: string;
  unrealized_pnl_pct: string;
  current_value: string;
  invested_value: string;
}

// Strategy types
export interface UnifiedStrategy {
  ticker: string;
  market: string;
  final_action: "hold" | "buy" | "partial_sell" | "full_exit";
  action_source: "ai" | "position_engine" | "merged";
  confidence: number;
  rationale: string;
  sell_quantity: number;
  realized_pnl_estimate: number;
  changed_from_last: boolean;
}

export interface StrategyRunResult {
  market: string;
  run_date: string;
  strategies: UnifiedStrategy[];
  total_tickers_analyzed: number;
  changed_count: number;
}

// Notification types
export interface AppNotification {
  id: string;
  type: "strategy_change" | "tp_sl_alert" | "impulse_warning" | "system";
  title: string;
  body: string;
  ticker: string | null;
  action: string | null;
  is_read: boolean;
  created_at: string;
}

// Scheduler types
export interface SchedulerJob {
  id: string;
  name: string;
  next_run: string;
  trigger: string;
}

export interface SchedulerStatus {
  status: string;
  timezone: string;
  jobs: SchedulerJob[];
  recovery_enabled?: boolean;
  max_recovery_days?: number;
}

export interface RecoveryResult {
  recovered: boolean;
  date?: string;
  error?: string;
}

export interface RecoveryResponse {
  kr?: RecoveryResult;
  us?: RecoveryResult;
}

// API key types
export interface APIKeyStatus {
  has_api_key: boolean;
  key_preview: string | null;
}

// Common
export type Market = "KR" | "US";
export type Action = "hold" | "buy" | "partial_sell" | "full_exit";