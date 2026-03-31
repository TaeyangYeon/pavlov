import { SummaryCards } from './SummaryCards'
import { MainContent } from '../layout'

export function Dashboard() {
  return (
    <MainContent title="대시보드">
      <SummaryCards />
      
      <div style={{ marginTop: '32px' }}>
        <div className="card">
          <h3 className="card-title">시스템 상태</h3>
          <div style={{ display: 'grid', gap: '12px' }}>
            <div className="flex justify-between items-center">
              <span>한국 시장 분석</span>
              <span className="badge" style={{ background: 'var(--color-success)', color: 'white' }}>활성</span>
            </div>
            <div className="flex justify-between items-center">
              <span>미국 시장 분석</span>
              <span className="badge" style={{ background: 'var(--color-success)', color: 'white' }}>활성</span>
            </div>
            <div className="flex justify-between items-center">
              <span>알림 시스템</span>
              <span className="badge" style={{ background: 'var(--color-success)', color: 'white' }}>정상</span>
            </div>
            <div className="flex justify-between items-center">
              <span>스케줄러</span>
              <span className="badge" style={{ background: 'var(--color-success)', color: 'white' }}>실행중</span>
            </div>
          </div>
        </div>
      </div>
    </MainContent>
  )
}