import { usePositions } from '../../hooks/usePositions'

export function PositionsTable() {
  const { positions, loading, error, closePosition } = usePositions()

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR')
  }

  const formatPrice = (price: string) => {
    return Number(price).toFixed(4)
  }

  const getMarketBadge = (market: string) => {
    return market === 'KR' ? '🇰🇷 한국' : '🇺🇸 미국'
  }

  const handleClose = async (id: string, ticker: string) => {
    if (window.confirm(`${ticker} 포지션을 정말 종료하시겠습니까?`)) {
      await closePosition(id)
    }
  }

  if (loading) {
    return (
      <div className="loading-spinner">
        포지션을 불러오는 중...
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-state">
        오류: {error}
      </div>
    )
  }

  if (positions.length === 0) {
    return (
      <div className="empty-state">
        <h3>활성 포지션이 없습니다</h3>
        <p>새로운 포지션을 생성해보세요.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="card-title">활성 포지션 ({positions.length})</h3>
      
      {/* Desktop table */}
      <div className="hide-mobile" style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>종목</th>
              <th>시장</th>
              <th>평균단가</th>
              <th>진입 횟수</th>
              <th>생성일</th>
              <th>액션</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position) => (
              <tr key={position.id}>
                <td style={{ fontWeight: '600' }}>{position.ticker}</td>
                <td>{getMarketBadge(position.market)}</td>
                <td style={{ fontFamily: 'monospace' }}>
                  ${formatPrice(position.avg_price)}
                </td>
                <td style={{ textAlign: 'center' }}>
                  {position.entries.length}
                </td>
                <td>{formatDate(position.created_at)}</td>
                <td>
                  <button
                    onClick={() => handleClose(position.id, position.ticker)}
                    className="btn btn-danger text-sm"
                  >
                    종료
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div style={{ display: 'none' }} className="show-mobile">
        {positions.map((position) => (
          <div key={position.id} className="position-card">
            <div className="position-card-header">
              <div>
                <div className="position-card-ticker">{position.ticker}</div>
                <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  평균단가: ${formatPrice(position.avg_price)}
                </div>
              </div>
              <div className="position-card-market">
                {getMarketBadge(position.market)}
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                진입 {position.entries.length}회 • {formatDate(position.created_at)}
              </div>
              <button
                onClick={() => handleClose(position.id, position.ticker)}
                className="btn btn-danger text-sm"
              >
                종료
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}