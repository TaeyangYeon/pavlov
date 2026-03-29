/**
 * PositionListWithPnL component for displaying positions with P&L calculations
 */

import { useState, useEffect } from 'react'
import type { PositionResponse, PositionWithPnL } from '../api/positions'
import { positionAPI } from '../api/positions'
import { TpSlPanel } from './TpSlPanel'

interface PositionListWithPnLProps {
  refreshTrigger: number
}

export function PositionListWithPnL({ refreshTrigger }: PositionListWithPnLProps) {
  const [positions, setPositions] = useState<PositionResponse[]>([])
  const [positionsWithPnL, setPositionsWithPnL] = useState<PositionWithPnL[]>([])
  const [currentPrice, setCurrentPrice] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [loadingPnL, setLoadingPnL] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPositionForTpSl, setSelectedPositionForTpSl] = useState<{ id: string; ticker: string } | null>(null)

  const fetchPositions = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await positionAPI.fetchPositions()
      setPositions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch positions')
    } finally {
      setLoading(false)
    }
  }

  const fetchPnLData = async () => {
    if (!currentPrice || positions.length === 0) return

    try {
      setLoadingPnL(true)
      setError(null)
      
      const pnlPromises = positions.map(position => 
        positionAPI.getPositionWithPnL(position.id, currentPrice)
      )
      
      const pnlData = await Promise.all(pnlPromises)
      setPositionsWithPnL(pnlData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch P&L data')
    } finally {
      setLoadingPnL(false)
    }
  }

  useEffect(() => {
    fetchPositions()
  }, [refreshTrigger])

  useEffect(() => {
    if (currentPrice && positions.length > 0) {
      fetchPnLData()
    }
  }, [currentPrice, positions])

  const handleClosePosition = async (id: string, ticker: string) => {
    if (!window.confirm(`Are you sure you want to close position ${ticker}?`)) {
      return
    }

    try {
      await positionAPI.closePosition(id)
      // Refresh the list
      await fetchPositions()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to close position')
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const formatPrice = (price: string) => {
    return Number(price).toFixed(4)
  }

  const formatPnL = (pnl: string) => {
    return Number(pnl).toFixed(2)
  }

  const formatPercent = (percent: string) => {
    return `${Number(percent).toFixed(2)}%`
  }

  const getPnLColor = (pnl: string) => {
    const value = Number(pnl)
    if (value > 0) return '#28a745' // green for profit
    if (value < 0) return '#dc3545' // red for loss
    return '#6c757d' // gray for neutral
  }

  if (loading) {
    return (
      <div style={{ 
        padding: '20px', 
        textAlign: 'center',
        border: '1px solid #ddd',
        borderRadius: '8px'
      }}>
        Loading positions...
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ 
        padding: '20px',
        backgroundColor: '#ffebee',
        color: '#c62828',
        borderRadius: '4px',
        border: '1px solid #e57373'
      }}>
        Error: {error}
        <button
          onClick={fetchPositions}
          style={{
            marginLeft: '10px',
            background: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '5px 10px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div style={{ 
      padding: '20px', 
      border: '1px solid #ddd', 
      borderRadius: '8px',
      backgroundColor: '#f9f9f9'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '20px' 
      }}>
        <h2 style={{ margin: '0' }}>Positions with P&L ({positions.length})</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <input
            type="number"
            value={currentPrice}
            onChange={(e) => setCurrentPrice(e.target.value)}
            placeholder="Enter current price"
            step="0.01"
            min="0"
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          />
          <button
            onClick={fetchPositions}
            disabled={loadingPnL}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              padding: '8px 12px',
              cursor: 'pointer',
              opacity: loadingPnL ? 0.6 : 1
            }}
          >
            {loadingPnL ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {!currentPrice && (
        <div style={{ 
          padding: '15px',
          backgroundColor: '#e3f2fd',
          borderRadius: '4px',
          marginBottom: '20px',
          fontSize: '14px',
          color: '#1976d2'
        }}>
          💡 Enter a current price above to see P&L calculations
        </div>
      )}

      {positions.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          color: '#666',
          padding: '40px',
          fontStyle: 'italic'
        }}>
          No open positions. Create your first position using the form on the left.
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            backgroundColor: 'white'
          }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>
                  Ticker
                </th>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>
                  Market
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #ddd' }}>
                  Avg Price
                </th>
                {currentPrice && positionsWithPnL.length > 0 && (
                  <>
                    <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #ddd' }}>
                      Current Price
                    </th>
                    <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #ddd' }}>
                      Unrealized P&L
                    </th>
                    <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #ddd' }}>
                      P&L %
                    </th>
                    <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #ddd' }}>
                      Total P&L
                    </th>
                  </>
                )}
                <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #ddd' }}>
                  Entries
                </th>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>
                  Created
                </th>
                <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #ddd' }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position) => {
                const positionPnL = positionsWithPnL.find(p => p.id === position.id)
                return (
                  <tr key={position.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '12px', fontWeight: 'bold' }}>
                      {position.ticker}
                    </td>
                    <td style={{ padding: '12px' }}>
                      {position.market}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                      ${formatPrice(position.avg_price)}
                    </td>
                    {currentPrice && positionsWithPnL.length > 0 && positionPnL && (
                      <>
                        <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                          ${formatPrice(positionPnL.current_price)}
                        </td>
                        <td style={{ 
                          padding: '12px', 
                          textAlign: 'right', 
                          fontFamily: 'monospace',
                          color: getPnLColor(positionPnL.unrealized_pnl),
                          fontWeight: 'bold'
                        }}>
                          ${formatPnL(positionPnL.unrealized_pnl)}
                        </td>
                        <td style={{ 
                          padding: '12px', 
                          textAlign: 'right', 
                          fontFamily: 'monospace',
                          color: getPnLColor(positionPnL.unrealized_pnl_percent),
                          fontWeight: 'bold'
                        }}>
                          {formatPercent(positionPnL.unrealized_pnl_percent)}
                        </td>
                        <td style={{ 
                          padding: '12px', 
                          textAlign: 'right', 
                          fontFamily: 'monospace',
                          color: getPnLColor(positionPnL.total_pnl),
                          fontWeight: 'bold'
                        }}>
                          ${formatPnL(positionPnL.total_pnl)}
                        </td>
                      </>
                    )}
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {position.entries.length}
                    </td>
                    <td style={{ padding: '12px' }}>
                      {formatDate(position.created_at)}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '5px', justifyContent: 'center' }}>
                        <button
                          onClick={() => setSelectedPositionForTpSl({ id: position.id, ticker: position.ticker })}
                          style={{
                            background: '#17a2b8',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            padding: '6px 12px',
                            cursor: 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          TP/SL
                        </button>
                        <button
                          onClick={() => handleClosePosition(position.id, position.ticker)}
                          style={{
                            background: '#dc3545',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            padding: '6px 12px',
                            cursor: 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          Close
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          
          {currentPrice && positionsWithPnL.length > 0 && (
            <div style={{
              marginTop: '20px',
              padding: '15px',
              backgroundColor: '#f8f9fa',
              borderRadius: '4px',
              border: '1px solid #dee2e6'
            }}>
              <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#495057' }}>
                Portfolio Summary
              </h4>
              <div style={{ display: 'flex', justifyContent: 'space-around', fontSize: '16px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#6c757d', marginBottom: '4px' }}>
                    Total Unrealized P&L
                  </div>
                  <div style={{ 
                    fontFamily: 'monospace', 
                    fontWeight: 'bold',
                    color: getPnLColor(positionsWithPnL.reduce((sum, p) => sum + Number(p.unrealized_pnl), 0).toString())
                  }}>
                    ${formatPnL(positionsWithPnL.reduce((sum, p) => sum + Number(p.unrealized_pnl), 0).toString())}
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#6c757d', marginBottom: '4px' }}>
                    Total P&L
                  </div>
                  <div style={{ 
                    fontFamily: 'monospace', 
                    fontWeight: 'bold',
                    color: getPnLColor(positionsWithPnL.reduce((sum, p) => sum + Number(p.total_pnl), 0).toString())
                  }}>
                    ${formatPnL(positionsWithPnL.reduce((sum, p) => sum + Number(p.total_pnl), 0).toString())}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {selectedPositionForTpSl && (
        <TpSlPanel
          positionId={selectedPositionForTpSl.id}
          ticker={selectedPositionForTpSl.ticker}
          onClose={() => setSelectedPositionForTpSl(null)}
        />
      )}
    </div>
  )
}