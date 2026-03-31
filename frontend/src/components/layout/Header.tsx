import { useNotifications } from '../../hooks/useNotifications'

export function Header() {
  const { unreadCount } = useNotifications()

  return (
    <header className="header">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold">파블로프 대시보드</h1>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span>🔔</span>
          {unreadCount > 0 && (
            <span className="badge" style={{ background: 'var(--color-danger)', color: 'white' }}>
              {unreadCount}
            </span>
          )}
        </div>
        
        <button className="btn btn-ghost text-sm">설정</button>
      </div>
    </header>
  )
}