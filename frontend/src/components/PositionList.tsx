/**
 * PositionList component for displaying open positions
 */

import { useState, useEffect } from 'react'
import type { PositionResponse } from '../api/positions'
import { positionAPI } from '../api/positions'

interface PositionListProps {
  refreshTrigger: number
}

export function PositionList({ refreshTrigger }: PositionListProps) {
  const [positions, setPositions] = useState<PositionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

  useEffect(() => {
    fetchPositions()
  }, [refreshTrigger])

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
        <h2 style={{ margin: '0' }}>Open Positions ({positions.length})</h2>
        <button
          onClick={fetchPositions}
          style={{
            background: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '8px 12px',
            cursor: 'pointer'
          }}
        >
          Refresh
        </button>
      </div>

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
              {positions.map((position) => (
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
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    {position.entries.length}
                  </td>
                  <td style={{ padding: '12px' }}>
                    {formatDate(position.created_at)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}