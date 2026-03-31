import { useCallback, useMemo } from 'react'
import { usePolling } from './usePolling'
import { fetchUnreadNotifications, markNotificationRead, markAllRead } from '../api/notifications'
import { POLL_INTERVALS } from '../constants'
import type { AppNotification } from '../types'

export function useNotifications() {
  const {
    data: notifications,
    loading,
    error,
    refresh,
  } = usePolling<AppNotification[]>(
    () => fetchUnreadNotifications(),
    POLL_INTERVALS.NOTIFICATIONS
  )

  const unreadCount = useMemo(() => {
    return notifications?.filter(n => !n.is_read).length || 0
  }, [notifications])

  const markRead = useCallback(async (id: string) => {
    await markNotificationRead(id)
    refresh() // Refresh the list
  }, [refresh])

  const markAllReadHandler = useCallback(async () => {
    await markAllRead()
    refresh() // Refresh the list
  }, [refresh])

  return {
    notifications: notifications || [],
    unreadCount,
    loading,
    error,
    markRead,
    markAllRead: markAllReadHandler,
    refresh,
  }
}