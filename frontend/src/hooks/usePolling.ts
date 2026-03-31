import { useState, useEffect, useCallback, useRef } from 'react'

export function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number,
  enabled: boolean = true,
): {
  data: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
} {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined)
  const isFirstLoad = useRef(true)

  const fetch = useCallback(async () => {
    try {
      // Only show loading on first fetch
      if (isFirstLoad.current) {
        setLoading(true)
        isFirstLoad.current = false
      }
      setError(null)
      const result = await fetchFn()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [fetchFn])

  const refresh = useCallback(() => {
    fetch()
  }, [fetch])

  useEffect(() => {
    if (!enabled) return

    // Initial fetch
    fetch()

    // Set up polling
    intervalRef.current = setInterval(fetch, intervalMs)

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [fetch, intervalMs, enabled])

  return { data, loading, error, refresh }
}