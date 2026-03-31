/**
 * API client for notifications management
 */

import type { AppNotification } from '../types'

export async function fetchUnreadNotifications(
  limit?: number
): Promise<AppNotification[]> {
  const url = limit 
    ? `/api/v1/notifications/unread?limit=${limit}`
    : '/api/v1/notifications/unread'
  
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Failed to fetch unread notifications: ${response.statusText}`)
  }
  return response.json()
}

export async function markNotificationRead(
  id: string
): Promise<void> {
  const response = await fetch(`/api/v1/notifications/${id}/read`, {
    method: 'PATCH',
  })
  if (!response.ok) {
    throw new Error(`Failed to mark notification as read: ${response.statusText}`)
  }
}

export async function markAllRead(): Promise<void> {
  const response = await fetch('/api/v1/notifications/read-all', {
    method: 'PATCH',
  })
  if (!response.ok) {
    throw new Error(`Failed to mark all notifications as read: ${response.statusText}`)
  }
}