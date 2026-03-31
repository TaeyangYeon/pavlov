import { useState } from 'react'
import type { Market } from '../../types'
import { useStrategy } from '../../hooks/useStrategy'
import { MainContent } from '../layout'
import { StrategyCards } from './StrategyCards'

export function StrategyPage() {
  const [selectedMarket, setSelectedMarket] = useState<Market>('US')
  const { result, loading, error, refresh } = useStrategy(selectedMarket)

  return (
    <MainContent title="전략 분석">
      <div className="mb-4">
        <div className="market-selector">
          <button
            className={`market-tab ${selectedMarket === 'US' ? 'active' : ''}`}
            onClick={() => setSelectedMarket('US')}
          >
            🇺🇸 미국 시장
          </button>
          <button
            className={`market-tab ${selectedMarket === 'KR' ? 'active' : ''}`}
            onClick={() => setSelectedMarket('KR')}
          >
            🇰🇷 한국 시장
          </button>
          <button
            onClick={refresh}
            className="btn btn-secondary text-sm"
            disabled={loading}
            style={{ marginLeft: 'auto' }}
          >
            {loading ? '새로고침 중...' : '새로고침'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="loading-spinner">
          전략 데이터를 불러오는 중...
        </div>
      )}

      {error && (
        <div className="error-state">
          오류: {error}
        </div>
      )}

      {!loading && !error && !result && (
        <div className="empty-state">
          <h3>전략 데이터가 없습니다</h3>
          <p>선택한 시장에 대한 분석 결과가 없습니다.</p>
        </div>
      )}

      {result && !loading && !error && (
        <StrategyCards result={result} />
      )}
    </MainContent>
  )
}