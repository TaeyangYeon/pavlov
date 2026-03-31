/**
 * API client for behavioral analysis and cooling-off checks
 */

export interface BehaviorReportResponse {
  total_trades: number;
  ai_alignment_rate: number;
  ai_alignment_pct: string;
  alignment_label: string;
  alignment_color: string;
  impulse_trade_count: number;
  contradiction_count: number;
  overtrading_tickers: string[];
  avg_holding_days: number;
  most_traded_ticker: string | null;
  cooling_off_warnings_received: number;
  patterns: Array<{
    type: string;
    ticker: string;
    description: string;
    detected_at: string;
  }>;
  analysis_period_days: number;
  generated_at: string;
}

export interface CoolingOffStatus {
  ticker: string;
  is_within_cooling_off: boolean;
  minutes_elapsed: number;
  minutes_remaining: number;
  cooling_off_minutes: number;
  last_ai_recommendation: string | null;
}

const API_BASE = '/api/v1';

export async function getBehaviorReport(days?: number): Promise<BehaviorReportResponse> {
  const params = new URLSearchParams();
  if (days) params.append('days', days.toString());
  
  const response = await fetch(`${API_BASE}/behavior/report?${params}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch behavior report: ${response.statusText}`);
  }
  
  return response.json();
}

export async function checkCoolingOff(ticker: string): Promise<CoolingOffStatus> {
  const response = await fetch(`${API_BASE}/behavior/cooling-off/${ticker}`);
  
  if (!response.ok) {
    throw new Error(`Failed to check cooling-off: ${response.statusText}`);
  }
  
  return response.json();
}