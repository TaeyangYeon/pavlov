/**
 * API client for scheduler management
 */

import type { SchedulerStatus, Market } from '../types'

export async function fetchSchedulerStatus(): Promise<SchedulerStatus> {
  const response = await fetch('/api/v1/scheduler/status')
  if (!response.ok) {
    throw new Error(`Failed to fetch scheduler status: ${response.statusText}`)
  }
  return response.json()
}

export async function triggerJob(
  market: Market
): Promise<{ message: string }> {
  const response = await fetch(`/api/v1/scheduler/trigger/${market}`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(`Failed to trigger job: ${response.statusText}`)
  }
  return response.json()
}

export async function triggerRecovery(market?: string): Promise<Record<string, unknown>> {
  const url = market 
    ? `/api/v1/scheduler/recover?market=${market}`
    : '/api/v1/scheduler/recover'
  const response = await fetch(url, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(`Failed to trigger recovery: ${response.statusText}`)
  }
  return response.json()
}