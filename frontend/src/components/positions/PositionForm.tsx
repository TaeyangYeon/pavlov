import React, { useState } from 'react'
import type { PositionEntry } from '../../types'
import { usePositions } from '../../hooks/usePositions'
import { checkCoolingOff } from '../../api/behavior'
import { recordDecision } from '../../api/decisions'
import { CoolingOffWarning } from '../behavior/CoolingOffWarning'
import type { CoolingOffStatus } from '../../api/behavior'

export function PositionForm() {
  const { createPosition } = usePositions()
  const [ticker, setTicker] = useState('')
  const [market, setMarket] = useState<'KR' | 'US'>('US')
  const [entries, setEntries] = useState<PositionEntry[]>([
    {
      price: '',
      quantity: '',
      entered_at: new Date().toISOString().slice(0, 16)
    }
  ])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [coolingOffStatus, setCoolingOffStatus] = useState<CoolingOffStatus | null>(null)
  const [showCoolingOffWarning, setShowCoolingOffWarning] = useState(false)

  const calculateAvgPrice = (): number | null => {
    const validEntries = entries.filter(
      e => e.price && e.quantity && Number(e.price) > 0 && Number(e.quantity) > 0
    )
    
    if (validEntries.length === 0) return null
    
    const totalValue = validEntries.reduce(
      (sum, e) => sum + Number(e.price) * Number(e.quantity), 
      0
    )
    const totalQuantity = validEntries.reduce(
      (sum, e) => sum + Number(e.quantity), 
      0
    )
    
    return totalQuantity > 0 ? totalValue / totalQuantity : null
  }

  const addEntry = () => {
    setEntries([
      ...entries,
      {
        price: '',
        quantity: '',
        entered_at: new Date().toISOString().slice(0, 16)
      }
    ])
  }

  const removeEntry = (index: number) => {
    if (entries.length > 1) {
      setEntries(entries.filter((_, i) => i !== index))
    }
  }

  const updateEntry = (index: number, field: keyof PositionEntry, value: string) => {
    const newEntries = [...entries]
    newEntries[index] = { ...newEntries[index], [field]: value }
    setEntries(newEntries)
  }

  const checkCoolingOffAndSubmit = async () => {
    setError(null)
    setIsSubmitting(true)

    try {
      // Step 1: Check cooling-off period
      const coolingOffCheck = await checkCoolingOff(ticker.trim().toUpperCase())
      
      if (coolingOffCheck.is_within_cooling_off) {
        setCoolingOffStatus(coolingOffCheck)
        setShowCoolingOffWarning(true)
        setIsSubmitting(false)
        return
      }

      // No cooling-off warning, proceed directly
      await submitPosition(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : '냉각 기간 확인에 실패했습니다')
      setIsSubmitting(false)
    }
  }

  const submitPosition = async (overrideCoolingOff: boolean = false) => {
    try {
      const validEntries = entries.filter(
        e => e.price && e.quantity && Number(e.price) > 0 && Number(e.quantity) > 0
      )

      if (validEntries.length === 0) {
        throw new Error('최소 하나 이상의 유효한 진입이 필요합니다')
      }

      if (!ticker.trim()) {
        throw new Error('종목 코드는 필수입니다')
      }

      const formattedEntries = validEntries.map(e => ({
        ...e,
        entered_at: new Date(e.entered_at).toISOString()
      }))

      // Step 2: Record decision for behavioral analysis
      const totalQuantity = validEntries.reduce((sum, e) => sum + Number(e.quantity), 0)
      const avgPrice = calculateAvgPrice()
      
      if (avgPrice) {
        await recordDecision({
          ticker: ticker.trim().toUpperCase(),
          market,
          action: 'buy',
          price: avgPrice,
          quantity: totalQuantity,
          notes: `Position creation with ${validEntries.length} entries`,
          override_cooling_off: overrideCoolingOff
        })
      }

      // Step 3: Create position
      await createPosition({
        ticker: ticker.trim().toUpperCase(),
        market,
        entries: formattedEntries
      })

      // Reset form
      setTicker('')
      setMarket('US')
      setEntries([{
        price: '',
        quantity: '',
        entered_at: new Date().toISOString().slice(0, 16)
      }])
      setShowCoolingOffWarning(false)
      setCoolingOffStatus(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : '포지션 생성에 실패했습니다')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await checkCoolingOffAndSubmit()
  }

  const handleCoolingOffOverride = () => {
    setShowCoolingOffWarning(false)
    submitPosition(true)
  }

  const handleCoolingOffCancel = () => {
    setShowCoolingOffWarning(false)
    setCoolingOffStatus(null)
    setIsSubmitting(false)
  }

  const avgPrice = calculateAvgPrice()

  return (
    <>
      {showCoolingOffWarning && coolingOffStatus && (
        <CoolingOffWarning
          coolingOffStatus={coolingOffStatus}
          onCancel={handleCoolingOffCancel}
          onOverride={handleCoolingOffOverride}
        />
      )}
      
      <div className="card">
        <h3 className="card-title">새 포지션 생성</h3>
        
        <form onSubmit={handleSubmit}>
        <div className="flex gap-4 mb-4">
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              종목 코드
            </label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="AAPL"
              style={{ textTransform: 'uppercase' }}
              required
            />
          </div>
          
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              시장
            </label>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value as 'KR' | 'US')}
            >
              <option value="US">🇺🇸 미국 시장</option>
              <option value="KR">🇰🇷 한국 시장</option>
            </select>
          </div>
        </div>

        <div className="mb-4">
          <h4 style={{ marginBottom: '16px', fontSize: '16px' }}>포지션 진입</h4>
          
          {entries.map((entry, index) => (
            <div key={index} className="mb-4" style={{ 
              padding: '16px', 
              border: '1px solid var(--color-border)', 
              borderRadius: 'var(--radius)',
              background: 'var(--color-bg)'
            }}>
              <div className="flex gap-2 mb-2">
                <div style={{ flex: 1 }}>
                  <label className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                    가격
                  </label>
                  <input
                    type="number"
                    value={entry.price}
                    onChange={(e) => updateEntry(index, 'price', e.target.value)}
                    placeholder="0.00"
                    step="0.01"
                    min="0"
                  />
                </div>
                
                <div style={{ flex: 1 }}>
                  <label className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                    수량
                  </label>
                  <input
                    type="number"
                    value={entry.quantity}
                    onChange={(e) => updateEntry(index, 'quantity', e.target.value)}
                    placeholder="0"
                    step="0.01"
                    min="0"
                  />
                </div>
                
                <div style={{ flex: 1 }}>
                  <label className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                    진입시간
                  </label>
                  <input
                    type="datetime-local"
                    value={entry.entered_at}
                    onChange={(e) => updateEntry(index, 'entered_at', e.target.value)}
                  />
                </div>
                
                {entries.length > 1 && (
                  <div style={{ alignSelf: 'end' }}>
                    <button
                      type="button"
                      onClick={() => removeEntry(index)}
                      className="btn btn-danger text-sm"
                    >
                      삭제
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          <button
            type="button"
            onClick={addEntry}
            className="btn btn-secondary"
          >
            + 진입 추가
          </button>
        </div>

        {avgPrice !== null && (
          <div className="mb-4" style={{ 
            padding: '16px',
            background: 'var(--color-success)',
            color: 'white',
            borderRadius: 'var(--radius)'
          }}>
            <strong>계산된 평균 단가: ${avgPrice.toFixed(4)}</strong>
          </div>
        )}

        {error && (
          <div className="error-state mb-4">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting || !ticker.trim() || entries.every(e => !e.price || !e.quantity)}
          className="btn btn-primary"
        >
          {isSubmitting ? '생성 중...' : '포지션 생성'}
        </button>
      </form>
    </div>
    </>
  )
}