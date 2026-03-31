import type { StrategyRunResult, UnifiedStrategy } from '../../types'
import { STRATEGY_LABELS } from '../../constants'

interface StrategyCardsProps {
  result: StrategyRunResult
}

export function StrategyCards({ result }: StrategyCardsProps) {
  const getActionColor = (action: string) => {
    switch (action) {
      case 'buy': return 'var(--color-success)'
      case 'hold': return 'var(--color-neutral)'
      case 'partial_sell': return 'var(--color-warning)'
      case 'full_exit': return 'var(--color-danger)'
      default: return 'var(--color-neutral)'
    }
  }

  const getActionSymbol = (action: string) => {
    switch (action) {
      case 'buy': return '📈'
      case 'hold': return '⏸️'
      case 'partial_sell': return '📊'
      case 'full_exit': return '📉'
      default: return '❓'
    }
  }

  const getActionLabel = (action: string) => {
    return STRATEGY_LABELS[action as keyof typeof STRATEGY_LABELS] || action
  }

  if (result.strategies.length === 0) {
    return (
      <div className="empty-state">
        <h3>전략 결과가 없습니다</h3>
        <p>포지션을 먼저 생성해주세요.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="summary-cards mb-4">
        <div className="summary-card">
          <h3>분석된 종목</h3>
          <div className="value">{result.total_tickers_analyzed}</div>
        </div>
        <div className="summary-card">
          <h3>변경된 전략</h3>
          <div className="value" style={{ color: 'var(--color-success)' }}>
            {result.changed_count}
          </div>
        </div>
        <div className="summary-card">
          <h3>시장</h3>
          <div className="value">
            {result.market === 'KR' ? '🇰🇷 한국' : '🇺🇸 미국'}
          </div>
        </div>
        <div className="summary-card">
          <h3>분석 일시</h3>
          <div className="value text-sm">
            {new Date(result.run_date).toLocaleDateString('ko-KR')}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="card-title">전략 추천</h3>
        
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {result.strategies.map((strategy: UnifiedStrategy, index) => (
            <div
              key={`${strategy.ticker}-${index}`}
              className="mb-4"
              style={{
                padding: '16px',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius)',
                background: strategy.changed_from_last ? '#e3f2fd' : 'var(--color-surface)',
                borderLeft: strategy.changed_from_last ? '4px solid var(--color-secondary)' : undefined
              }}
            >
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-lg">{strategy.ticker}</span>
                  {strategy.changed_from_last && (
                    <span 
                      className="badge text-sm" 
                      style={{ background: 'var(--color-secondary)', color: 'white' }}
                    >
                      변경됨
                    </span>
                  )}
                </div>
                
                <div className="flex items-center gap-2">
                  <span style={{ fontSize: '20px' }}>
                    {getActionSymbol(strategy.final_action)}
                  </span>
                  <span
                    className="font-semibold"
                    style={{
                      color: getActionColor(strategy.final_action),
                      textTransform: 'uppercase'
                    }}
                  >
                    {getActionLabel(strategy.final_action)}
                  </span>
                </div>
              </div>

              <div className="flex gap-4 text-sm mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                <div>
                  <strong>신뢰도:</strong> {(strategy.confidence * 100).toFixed(0)}%
                </div>
                <div>
                  <strong>출처:</strong> {strategy.action_source}
                </div>
                {strategy.sell_quantity > 0 && (
                  <div>
                    <strong>매도 수량:</strong> {strategy.sell_quantity.toFixed(4)}
                  </div>
                )}
                {strategy.realized_pnl_estimate !== 0 && (
                  <div>
                    <strong>예상 손익:</strong> 
                    <span 
                      className={strategy.realized_pnl_estimate >= 0 ? 'pnl-positive' : 'pnl-negative'}
                      style={{ marginLeft: '4px' }}
                    >
                      ${strategy.realized_pnl_estimate.toFixed(2)}
                    </span>
                  </div>
                )}
              </div>

              <div 
                className="text-sm" 
                style={{
                  color: 'var(--color-text-secondary)',
                  background: 'var(--color-bg)',
                  padding: '8px',
                  borderRadius: '4px',
                  fontStyle: 'italic'
                }}
              >
                {strategy.rationale || '근거가 제공되지 않았습니다.'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}