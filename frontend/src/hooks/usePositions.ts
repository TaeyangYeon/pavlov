import { useCallback } from 'react'
import { usePolling } from './usePolling'
import { positionAPI, type PositionCreate } from '../api/positions'
import { POLL_INTERVALS } from '../constants'
import type { Position, PositionEntry } from '../types'

export function usePositions() {
  const {
    data: positions,
    loading,
    error,
    refresh,
  } = usePolling<Position[]>(
    () => positionAPI.fetchPositions(),
    POLL_INTERVALS.POSITIONS
  )

  const createPosition = useCallback(async (data: PositionCreate) => {
    await positionAPI.createPosition(data)
    refresh() // Refresh the list
  }, [refresh])

  const closePosition = useCallback(async (id: string) => {
    await positionAPI.closePosition(id)
    refresh() // Refresh the list
  }, [refresh])

  const addEntry = useCallback(async (id: string, entry: PositionEntry) => {
    await positionAPI.addEntry(id, entry)
    refresh() // Refresh the list
  }, [refresh])

  return {
    positions: positions || [],
    loading,
    error,
    refresh,
    createPosition,
    closePosition,
    addEntry,
  }
}