export const POLL_INTERVALS = {
  POSITIONS: 60_000,
  NOTIFICATIONS: 30_000,
  STRATEGY: 300_000,
  SCHEDULER: 120_000,
} as const;

export const ACTION_LABELS: Record<string, string> = {
  hold: "보유",
  buy: "매수",
  partial_sell: "일부 매도",
  full_exit: "전량 청산",
};

export const ACTION_COLORS: Record<string, string> = {
  hold: "var(--color-neutral)",
  buy: "var(--color-secondary)",
  partial_sell: "var(--color-warning)",
  full_exit: "var(--color-danger)",
};

export const MARKET_LABELS: Record<string, string> = {
  KR: "🇰🇷 한국",
  US: "🇺🇸 미국",
};

export const STUB_USER_ID = "00000000-0000-0000-0000-000000000001";

export const STRATEGY_LABELS: Record<string, string> = {
  buy: '매수',
  hold: '보유',
  partial_sell: '부분 매도',
  full_exit: '전체 청산'
};

export const NOTIFICATION_LABELS: Record<string, string> = {
  strategy_change: '전략 변경',
  tp_sl_alert: 'TP/SL 알림',
  impulse_warning: '임펄스 경고',
  system: '시스템'
};