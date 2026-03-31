import { useNotifications } from '../../hooks/useNotifications'
import { MainContent } from '../layout'
import { NOTIFICATION_LABELS } from '../../constants'

export function NotificationsPage() {
  const { notifications, unreadCount, loading, error, markRead, markAllRead } = useNotifications()

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'strategy_change':
        return 'var(--color-secondary)'
      case 'tp_sl_alert':
        return 'var(--color-danger)'
      case 'impulse_warning':
        return 'var(--color-warning)'
      case 'system':
      default:
        return 'var(--color-neutral)'
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'strategy_change':
        return '🎯'
      case 'tp_sl_alert':
        return '🚨'
      case 'impulse_warning':
        return '⚠️'
      case 'system':
      default:
        return 'ℹ️'
    }
  }

  const getTypeLabel = (type: string) => {
    return NOTIFICATION_LABELS[type as keyof typeof NOTIFICATION_LABELS] || type
  }

  const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return '방금 전'
    if (diffInMinutes < 60) return `${diffInMinutes}분 전`
    
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours}시간 전`
    
    const diffInDays = Math.floor(diffInHours / 24)
    return `${diffInDays}일 전`
  }

  if (loading) {
    return (
      <MainContent title="알림">
        <div className="loading-spinner">
          알림을 불러오는 중...
        </div>
      </MainContent>
    )
  }

  if (error) {
    return (
      <MainContent title="알림">
        <div className="error-state">
          오류: {error}
        </div>
      </MainContent>
    )
  }

  return (
    <MainContent title="알림">
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="card-title" style={{ marginBottom: 0 }}>
            읽지 않은 알림 ({unreadCount})
          </h3>
          {unreadCount > 0 && (
            <button
              onClick={markAllRead}
              className="btn btn-secondary text-sm"
            >
              모두 읽음으로 표시
            </button>
          )}
        </div>

        {notifications.length === 0 ? (
          <div className="empty-state">
            <h3>새 알림이 없습니다</h3>
            <p>모든 알림을 확인하셨습니다.</p>
          </div>
        ) : (
          <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className="mb-3"
                style={{
                  padding: '16px',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius)',
                  background: notification.is_read ? 'var(--color-bg)' : 'var(--color-surface)',
                  borderLeft: `4px solid ${getNotificationColor(notification.type)}`
                }}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: '20px' }}>
                      {getNotificationIcon(notification.type)}
                    </span>
                    <span className="font-semibold">{notification.title}</span>
                    <span
                      className="badge text-sm"
                      style={{
                        background: getNotificationColor(notification.type),
                        color: 'white'
                      }}
                    >
                      {getTypeLabel(notification.type)}
                    </span>
                    {notification.ticker && (
                      <span className="badge" style={{ background: 'var(--color-bg)' }}>
                        {notification.ticker}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                      {formatTimeAgo(notification.created_at)}
                    </span>
                    {!notification.is_read && (
                      <button
                        onClick={() => markRead(notification.id)}
                        className="btn btn-ghost text-sm"
                        style={{ padding: '4px 8px' }}
                      >
                        ✓
                      </button>
                    )}
                  </div>
                </div>

                <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  {notification.body}
                </div>

                {notification.action && (
                  <div className="mt-2">
                    <span
                      className="badge text-sm"
                      style={{ background: 'var(--color-warning)', color: 'white' }}
                    >
                      액션: {notification.action}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </MainContent>
  )
}