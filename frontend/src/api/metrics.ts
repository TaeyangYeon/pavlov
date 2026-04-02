/**
 * API client for performance metrics (Step 26: Performance Optimization)
 */

export interface PerformanceMetrics {
  session_start: string;
  cache: {
    [market: string]: {
      hit_rate: number;
      session_hit_rate: number;
      total_requests: number;
      hits: number;
      misses: number;
    };
  };
  ai: {
    total_calls: number;
    total_cost_usd: number;
    avg_cost_per_call: number;
    calls: Array<{
      market: string;
      input_tokens: number;
      output_tokens: number;
      cost_usd: number;
      timestamp: string;
    }>;
  };
  alerts: {
    ai_cost_exceeded: boolean;
    ai_cost_threshold_usd: number;
    total_ai_cost_usd: number;
  };
  targets: {
    cache_hit_rate_target: number;
    ai_cost_per_run_target_usd: number;
    slow_query_threshold_ms: number;
  };
}

export async function getPerformanceMetrics(): Promise<PerformanceMetrics> {
  const response = await fetch('/api/v1/metrics/performance');
  if (!response.ok) {
    throw new Error('Failed to fetch performance metrics');
  }
  return response.json();
}

export async function resetMetrics(): Promise<void> {
  const response = await fetch('/api/v1/metrics/reset', {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to reset metrics');
  }
}