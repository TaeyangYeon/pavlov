/**
 * NotificationBell Component
 * 
 * Features:
 * - Bell icon (🔔) in top-right of header
 * - Red badge showing unread count
 * - Click → dropdown showing last 10 notifications
 * - Each notification: title (bold) + body + time ago
 * - Color by type: strategy_change → blue, tp_sl_alert → red, impulse_warning → orange, system → gray
 * - "Mark all read" button
 * - "×" to mark individual as read
 * - Polls GET /api/v1/notifications/unread every 30s
 * - Badge disappears when all read
 */

import React, { useState, useEffect } from 'react';
import './NotificationBell.css';

interface Notification {
  id: string;
  type: string;
  title: string;
  body: string;
  ticker?: string;
  action?: string;
  is_read: boolean;
  created_at: string;
}

const NotificationBell: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Polling for new notifications every 30 seconds
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/v1/notifications/unread');
        if (response.ok) {
          const data = await response.json();
          setNotifications(data);
        }
      } catch (error) {
        console.error('Failed to fetch notifications:', error);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchNotifications();

    // Set up polling every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);

    return () => clearInterval(interval);
  }, []);

  const markAsRead = async (notificationId: string) => {
    try {
      const response = await fetch(`/api/v1/notifications/${notificationId}/read`, {
        method: 'PATCH',
      });
      
      if (response.ok) {
        setNotifications(prev => 
          prev.filter(n => n.id !== notificationId)
        );
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      const response = await fetch('/api/v1/notifications/read-all', {
        method: 'PATCH',
      });
      
      if (response.ok) {
        setNotifications([]);
      }
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  const getNotificationTypeColor = (type: string): string => {
    switch (type) {
      case 'strategy_change':
        return 'blue';
      case 'tp_sl_alert':
        return 'red';
      case 'impulse_warning':
        return 'orange';
      case 'system':
      default:
        return 'gray';
    }
  };

  const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
  };

  const unreadCount = notifications.length;

  return (
    <div className="notification-bell">
      <button 
        className="bell-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Notifications (${unreadCount} unread)`}
      >
        🔔
        {unreadCount > 0 && (
          <span className="notification-badge">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="dropdown-header">
            <h3>Notifications</h3>
            {unreadCount > 0 && (
              <button 
                className="mark-all-read"
                onClick={markAllAsRead}
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="notification-list">
            {loading ? (
              <div className="notification-loading">Loading...</div>
            ) : unreadCount === 0 ? (
              <div className="no-notifications">
                No unread notifications
              </div>
            ) : (
              notifications.slice(0, 10).map((notification) => (
                <div
                  key={notification.id}
                  className={`notification-item notification-${getNotificationTypeColor(notification.type)}`}
                >
                  <div className="notification-content">
                    <div className="notification-title">
                      {notification.title}
                    </div>
                    <div className="notification-body">
                      {notification.body}
                    </div>
                    <div className="notification-meta">
                      {formatTimeAgo(notification.created_at)}
                      {notification.ticker && (
                        <span className="notification-ticker">
                          • {notification.ticker}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    className="mark-read-button"
                    onClick={() => markAsRead(notification.id)}
                    aria-label="Mark as read"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;