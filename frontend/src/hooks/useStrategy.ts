import { usePolling } from './usePolling'
import { fetchLatestStrategies } from '../api/strategy'
import { POLL_INTERVALS } from '../constants'
import type { StrategyRunResult, Market } from '../types'

export function useStrategy(market: Market) {
  const {
    data: result,
    loading,
    error,
    refresh,
  } = usePolling<StrategyRunResult>(
    () => fetchLatestStrategies(market),
    POLL_INTERVALS.STRATEGY
  )

  return {
    result,
    loading,
    error,
    refresh,
  }
}