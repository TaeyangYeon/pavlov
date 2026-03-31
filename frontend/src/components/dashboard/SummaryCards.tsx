import { usePositions } from '../../hooks/usePositions'
import { useNotifications } from '../../hooks/useNotifications'

export function SummaryCards() {
  const { positions, loading: positionsLoading } = usePositions()
  const { unreadCount, loading: notificationsLoading } = useNotifications()

  const openPositions = positions.filter(p => p.status === 'open')
  const closedPositions = positions.filter(p => p.status === 'closed')
  
  const totalPnL = positions.reduce((sum, position) => {
    const avgPrice = parseFloat(position.avg_price)
    const totalQty = position.entries.reduce((qty, entry) => qty + Number(entry.quantity), 0)
    const totalValue = avgPrice * totalQty
    return sum + totalValue
  }, 0)

  const formatKRW = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0
    }).format(amount)
  }

  const formatUSD = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const isLoading = positionsLoading || notificationsLoading

  return (
    <div className="summary-cards">
      <div className="summary-card">
        <h3>활성 포지션</h3>
        {isLoading ? (
          <div className="skeleton skeleton-value"></div>
        ) : (
          <div className="value">{openPositions.length}</div>
        )}
      </div>

      <div className="summary-card">
        <h3>종료된 포지션</h3>
        {isLoading ? (
          <div className="skeleton skeleton-value"></div>
        ) : (
          <div className="value">{closedPositions.length}</div>
        )}
      </div>

      <div className="summary-card">
        <h3>총 포지션 가치</h3>
        {isLoading ? (
          <div className="skeleton skeleton-value"></div>
        ) : (
          <div className="value" style={{ fontSize: '18px' }}>
            {totalPnL >= 1000000 ? formatKRW(totalPnL) : formatUSD(totalPnL)}
          </div>
        )}
      </div>

      <div className="summary-card">
        <h3>읽지 않은 알림</h3>
        {isLoading ? (
          <div className="skeleton skeleton-value"></div>
        ) : (
          <div className="value" style={{ color: unreadCount > 0 ? 'var(--color-danger)' : 'var(--color-text)' }}>
            {unreadCount}
          </div>
        )}
      </div>
    </div>
  )
}