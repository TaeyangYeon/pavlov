import React from 'react'
import type { SchedulerStatus, RecoveryResponse } from '../../types'
import { usePolling } from '../../hooks/usePolling'
import { fetchSchedulerStatus, triggerRecovery } from '../../api/scheduler'
import { MainContent } from '../layout'
import { POLL_INTERVALS } from '../../constants'

export function SchedulerPage() {
  const { 
    data: schedulerStatus, 
    loading, 
    error, 
    refresh 
  } = usePolling<SchedulerStatus>(fetchSchedulerStatus, POLL_INTERVALS.SCHEDULER)

  const [recoveryLoading, setRecoveryLoading] = React.useState(false)
  const [recoveryResult, setRecoveryResult] = React.useState<RecoveryResponse | null>(null)

  const handleRecovery = async (market?: string) => {
    try {
      setRecoveryLoading(true)
      setRecoveryResult(null)
      
      const result = await triggerRecovery(market)
      setRecoveryResult(result)
    } catch (err) {
      console.error('Recovery failed:', err)
    } finally {
      setRecoveryLoading(false)
    }
  }

  const formatNextRun = (isoString: string | null): string => {
    if (!isoString) return '예정 없음'
    
    try {
      const date = new Date(isoString)
      const now = new Date()
      const diffMs = date.getTime() - now.getTime()
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
      
      if (diffMs < 0) return '지연됨'
      if (diffHours === 0) return `${diffMinutes}분 후`
      if (diffHours < 24) return `${diffHours}시간 ${diffMinutes}분 후`
      
      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays}일 ${diffHours % 24}시간 후`
    } catch {
      return '잘못된 날짜'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return <span className="badge" style={{ background: 'var(--color-success)', color: 'white' }}>🟢 실행중</span>
      case 'stopped':
        return <span className="badge" style={{ background: 'var(--color-danger)', color: 'white' }}>🔴 중단됨</span>
      default:
        return <span className="badge" style={{ background: 'var(--color-neutral)', color: 'white' }}>❓ 알 수 없음</span>
    }
  }

  const getJobIcon = (jobId: string): string => {
    switch (jobId) {
      case 'kr_analysis': return '🇰🇷'
      case 'us_analysis': return '🇺🇸'
      default: return '⏰'
    }
  }

  const formatRecoveryResult = (result: { recovered: boolean; date?: string; error?: string }) => {
    if (result.recovered) {
      return (
        <div className="flex items-center gap-2 pnl-positive">
          <span>✅</span>
          <span>복구됨 {result.date}</span>
        </div>
      )
    } else if (result.error === 'stale') {
      return (
        <div className="flex items-center gap-2" style={{ color: 'var(--color-warning)' }}>
          <span>⏭️</span>
          <span>건너뜀 (너무 오래됨)</span>
        </div>
      )
    } else if (result.error) {
      return (
        <div className="flex items-center gap-2 pnl-negative">
          <span>❌</span>
          <span>실패: {result.error}</span>
        </div>
      )
    } else {
      return (
        <div className="flex items-center gap-2" style={{ color: 'var(--color-neutral)' }}>
          <span>⏭️</span>
          <span>없음</span>
        </div>
      )
    }
  }

  if (loading) {
    return (
      <MainContent title="스케줄러">
        <div className="loading-spinner">
          스케줄러 상태를 불러오는 중...
        </div>
      </MainContent>
    )
  }

  if (error) {
    return (
      <MainContent title="스케줄러">
        <div className="error-state">
          오류: {error}
        </div>
      </MainContent>
    )
  }

  if (!schedulerStatus) {
    return (
      <MainContent title="스케줄러">
        <div className="empty-state">
          <h3>스케줄러 데이터가 없습니다</h3>
        </div>
      </MainContent>
    )
  }

  return (
    <MainContent title="스케줄러">
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="card-title" style={{ marginBottom: 0 }}>시스템 상태</h3>
          <button onClick={refresh} className="btn btn-ghost text-sm">
            🔄 새로고침
          </button>
        </div>

        <div className="flex items-center gap-4 mb-4">
          <div>
            <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>상태:</span>
            {getStatusBadge(schedulerStatus.status)}
          </div>
          <div>
            <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              시간대: {schedulerStatus.timezone}
            </span>
          </div>
        </div>
      </div>

      {schedulerStatus.recovery_enabled && (
        <div className="card">
          <h3 className="card-title">🔄 누락된 실행 복구</h3>
          
          <div 
            className="mb-4 p-4" 
            style={{ 
              background: '#e3f2fd', 
              border: '1px solid var(--color-secondary)',
              borderRadius: 'var(--radius)'
            }}
          >
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm">
                최대 복구 일수: {schedulerStatus.max_recovery_days}
              </span>
              <button
                onClick={() => handleRecovery()}
                disabled={recoveryLoading}
                className="btn btn-secondary text-sm"
              >
                {recoveryLoading ? '⏳ 확인중...' : '🔍 전체 시장 확인'}
              </button>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => handleRecovery('KR')}
                disabled={recoveryLoading}
                className="btn btn-ghost text-sm"
              >
                🇰🇷 한국만 확인
              </button>
              <button
                onClick={() => handleRecovery('US')}
                disabled={recoveryLoading}
                className="btn btn-ghost text-sm"
              >
                🇺🇸 미국만 확인
              </button>
            </div>
          </div>

          {recoveryResult && (
            <div className="p-4" style={{ background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
              <h4 className="font-semibold mb-3">복구 결과:</h4>
              <div style={{ display: 'grid', gap: '8px' }}>
                {recoveryResult.kr && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-semibold">🇰🇷 한국 시장:</span>
                    {formatRecoveryResult(recoveryResult.kr)}
                  </div>
                )}
                {recoveryResult.us && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-semibold">🇺🇸 미국 시장:</span>
                    {formatRecoveryResult(recoveryResult.us)}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="card">
        <h3 className="card-title">예약된 작업</h3>
        
        {schedulerStatus.jobs.length === 0 ? (
          <div className="empty-state">
            <h3>예약된 작업이 없습니다</h3>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '16px' }}>
            {schedulerStatus.jobs.map((job) => (
              <div
                key={job.id}
                className="p-4"
                style={{
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius)',
                  background: 'var(--color-bg)'
                }}
              >
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: '20px' }}>{getJobIcon(job.id)}</span>
                    <span className="font-semibold">{job.name}</span>
                  </div>
                  <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                    ID: {job.id}
                  </span>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }} className="text-sm">
                  <div>
                    <span style={{ color: 'var(--color-text-secondary)' }}>다음 실행:</span>
                    <div className="font-semibold">
                      {job.next_run ? (
                        <>
                          <div>{new Date(job.next_run).toLocaleString('ko-KR', {
                            timeZone: 'Asia/Seoul',
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit'
                          })}</div>
                          <div className="text-sm" style={{ color: 'var(--color-secondary)' }}>
                            ({formatNextRun(job.next_run)})
                          </div>
                        </>
                      ) : (
                        <span style={{ color: 'var(--color-neutral)' }}>예정 없음</span>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <span style={{ color: 'var(--color-text-secondary)' }}>스케줄:</span>
                    <div className="font-semibold text-sm" style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                      {job.trigger}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div 
        className="text-sm flex justify-between items-center p-3"
        style={{ 
          background: 'var(--color-bg)', 
          color: 'var(--color-text-secondary)',
          borderRadius: 'var(--radius)'
        }}
      >
        <span>자동 새로고침: {POLL_INTERVALS.SCHEDULER / 1000}초</span>
        <span>마지막 업데이트: {new Date().toLocaleTimeString('ko-KR')}</span>
      </div>
    </MainContent>
  )
}