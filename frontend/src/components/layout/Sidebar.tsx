
interface SidebarProps {
  currentPage: string
  onNavigate: (page: string) => void
}

export function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  const navItems = [
    { id: 'dashboard', label: '대시보드', icon: '📊' },
    { id: 'positions', label: '포지션', icon: '💼' },
    { id: 'strategy', label: '전략', icon: '🎯' },
    { id: 'notifications', label: '알림', icon: '🔔' },
    { id: 'scheduler', label: '스케줄러', icon: '⏰' },
  ]

  return (
    <nav className="sidebar">
      <div style={{ padding: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600', color: 'white', margin: 0 }}>파블로프</h2>
        <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', margin: '4px 0 0 0' }}>AI 투자 지원</p>
      </div>
      
      {navItems.map(item => (
        <a
          key={item.id}
          href="#"
          className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
          onClick={(e) => {
            e.preventDefault()
            onNavigate(item.id)
          }}
        >
          <span style={{ marginRight: '8px' }}>{item.icon}</span>
          {item.label}
        </a>
      ))}
    </nav>
  )
}