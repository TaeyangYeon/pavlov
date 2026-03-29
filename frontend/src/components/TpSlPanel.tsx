/**
 * TpSlPanel component for TP/SL evaluation
 */

import { useState } from 'react'
import type { TakeProfitLevel, StopLossLevel, TpSlEvaluationResponse } from '../api/positions'
import { positionAPI } from '../api/positions'

interface TpSlPanelProps {
  positionId: string
  ticker: string
  onClose: () => void
}

export function TpSlPanel({ positionId, ticker, onClose }: TpSlPanelProps) {
  const [currentPrice, setCurrentPrice] = useState<string>('')
  const [tpLevels, setTpLevels] = useState<TakeProfitLevel[]>([
    { pct: 10, sell_ratio: 0.5 }
  ])
  const [slLevels, setSlLevels] = useState<StopLossLevel[]>([
    { pct: -5, sell_ratio: 1.0 }
  ])
  const [evaluation, setEvaluation] = useState<TpSlEvaluationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addTpLevel = () => {
    setTpLevels([...tpLevels, { pct: 15, sell_ratio: 0.3 }])
  }

  const addSlLevel = () => {
    setSlLevels([...slLevels, { pct: -10, sell_ratio: 1.0 }])
  }

  const removeTpLevel = (index: number) => {
    setTpLevels(tpLevels.filter((_, i) => i !== index))
  }

  const removeSlLevel = (index: number) => {
    setSlLevels(slLevels.filter((_, i) => i !== index))
  }

  const updateTpLevel = (index: number, field: 'pct' | 'sell_ratio', value: number) => {
    const updated = [...tpLevels]
    updated[index] = { ...updated[index], [field]: value }
    setTpLevels(updated)
  }

  const updateSlLevel = (index: number, field: 'pct' | 'sell_ratio', value: number) => {
    const updated = [...slLevels]
    updated[index] = { ...updated[index], [field]: value }
    setSlLevels(updated)
  }

  const evaluate = async () => {
    if (!currentPrice) {
      setError('Please enter current price')
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      const result = await positionAPI.evaluateTpSl({
        position_id: positionId,
        current_price: currentPrice,
        take_profit_levels: tpLevels,
        stop_loss_levels: slLevels
      })
      
      setEvaluation(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to evaluate')
    } finally {
      setLoading(false)
    }
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case 'hold': return '#6c757d'  // gray
      case 'partial_sell': return '#fd7e14'  // orange
      case 'full_exit': return '#dc3545'  // red
      default: return '#6c757d'
    }
  }

  const getActionEmoji = (action: string) => {
    switch (action) {
      case 'hold': return '🟢'
      case 'partial_sell': return '🟡' 
      case 'full_exit': return '🔴'
      default: return '⚪'
    }
  }

  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      background: 'white',
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '20px',
      width: '600px',
      maxHeight: '80vh',
      overflow: 'auto',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
      zIndex: 1000
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0 }}>TP/SL Evaluation - {ticker}</h3>
        <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer' }}>
          ✕
        </button>
      </div>

      {/* Current Price Input */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
          Current Price:
        </label>
        <input
          type="number"
          step="0.01"
          value={currentPrice}
          onChange={(e) => setCurrentPrice(e.target.value)}
          style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
          placeholder="Enter current market price"
        />
      </div>

      {/* Take Profit Levels */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <label style={{ fontWeight: 'bold' }}>Take Profit Levels:</label>
          <button onClick={addTpLevel} style={{ background: '#28a745', color: 'white', border: 'none', borderRadius: '4px', padding: '4px 8px' }}>
            + Add TP
          </button>
        </div>
        {tpLevels.map((level, index) => (
          <div key={index} style={{ display: 'flex', gap: '10px', marginBottom: '5px', alignItems: 'center' }}>
            <span style={{ width: '60px' }}>TP {index + 1}:</span>
            <input
              type="number"
              value={level.pct}
              onChange={(e) => updateTpLevel(index, 'pct', parseFloat(e.target.value) || 0)}
              style={{ width: '80px', padding: '4px' }}
              placeholder="% gain"
            />
            <span>%</span>
            <input
              type="number"
              step="0.1"
              value={level.sell_ratio}
              onChange={(e) => updateTpLevel(index, 'sell_ratio', parseFloat(e.target.value) || 0)}
              style={{ width: '80px', padding: '4px' }}
              placeholder="Sell ratio"
              min="0"
              max="1"
            />
            <span>ratio</span>
            <button onClick={() => removeTpLevel(index)} style={{ background: '#dc3545', color: 'white', border: 'none', borderRadius: '3px', padding: '2px 6px' }}>
              ✕
            </button>
          </div>
        ))}
      </div>

      {/* Stop Loss Levels */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <label style={{ fontWeight: 'bold' }}>Stop Loss Levels:</label>
          <button onClick={addSlLevel} style={{ background: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', padding: '4px 8px' }}>
            + Add SL
          </button>
        </div>
        {slLevels.map((level, index) => (
          <div key={index} style={{ display: 'flex', gap: '10px', marginBottom: '5px', alignItems: 'center' }}>
            <span style={{ width: '60px' }}>SL {index + 1}:</span>
            <input
              type="number"
              value={level.pct}
              onChange={(e) => updateSlLevel(index, 'pct', parseFloat(e.target.value) || 0)}
              style={{ width: '80px', padding: '4px' }}
              placeholder="% loss"
            />
            <span>%</span>
            <input
              type="number"
              step="0.1"
              value={level.sell_ratio}
              onChange={(e) => updateSlLevel(index, 'sell_ratio', parseFloat(e.target.value) || 0)}
              style={{ width: '80px', padding: '4px' }}
              placeholder="Sell ratio"
              min="0"
              max="1"
            />
            <span>ratio</span>
            <button onClick={() => removeSlLevel(index)} style={{ background: '#dc3545', color: 'white', border: 'none', borderRadius: '3px', padding: '2px 6px' }}>
              ✕
            </button>
          </div>
        ))}
      </div>

      {/* Evaluate Button */}
      <button
        onClick={evaluate}
        disabled={loading || !currentPrice}
        style={{
          width: '100%',
          padding: '12px',
          background: loading ? '#6c757d' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
          marginBottom: '20px'
        }}
      >
        {loading ? 'Evaluating...' : 'Evaluate TP/SL'}
      </button>

      {/* Error Display */}
      {error && (
        <div style={{ 
          padding: '10px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {/* Evaluation Result */}
      {evaluation && (
        <div style={{
          border: '1px solid #dee2e6',
          borderRadius: '4px',
          padding: '15px',
          backgroundColor: '#f8f9fa'
        }}>
          <h4 style={{ margin: '0 0 10px 0' }}>Evaluation Result:</h4>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>Action:</strong> 
            <span style={{ 
              marginLeft: '10px',
              color: getActionColor(evaluation.action),
              fontWeight: 'bold'
            }}>
              {getActionEmoji(evaluation.action)} {evaluation.action.toUpperCase()}
            </span>
          </div>

          <div style={{ marginBottom: '10px' }}>
            <strong>Triggered By:</strong> {evaluation.triggered_by}
          </div>

          {evaluation.triggered_level_pct && (
            <div style={{ marginBottom: '10px' }}>
              <strong>Triggered Level:</strong> {evaluation.triggered_level_pct}%
            </div>
          )}

          <div style={{ marginBottom: '10px' }}>
            <strong>Current P&L:</strong> {Number(evaluation.current_pnl_pct).toFixed(2)}%
          </div>

          <div style={{ marginBottom: '10px' }}>
            <strong>Sell Quantity:</strong> {evaluation.sell_quantity} shares
          </div>

          <div style={{ marginBottom: '10px' }}>
            <strong>Sell Ratio:</strong> {Number(evaluation.sell_ratio).toFixed(2)}
          </div>

          <div>
            <strong>Realized P&L Estimate:</strong> 
            <span style={{ 
              color: Number(evaluation.realized_pnl_estimate) >= 0 ? '#28a745' : '#dc3545',
              fontWeight: 'bold',
              marginLeft: '5px'
            }}>
              ${Number(evaluation.realized_pnl_estimate).toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}