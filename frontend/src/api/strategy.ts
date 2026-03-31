/**
 * API client for strategy management
 */

import type { StrategyRunResult, Market } from '../types'

export async function fetchLatestStrategies(
  market: Market
): Promise<StrategyRunResult> {
  const response = await fetch(`/api/v1/strategy/latest/${market}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch latest strategies: ${response.statusText}`)
  }
  return response.json()
}