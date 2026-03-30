import { useState, useEffect } from 'react'

interface UnifiedStrategy {
  ticker: string
  market: string
  final_action: string
  action_source: string
  confidence: number
  rationale: string
  sell_quantity: number
  realized_pnl_estimate: number
  changed_from_last: boolean
}

interface StrategyRunResult {
  market: string
  run_date: string
  strategies: UnifiedStrategy[]
  total_tickers_analyzed: number
  changed_count: number
  analysis_log_id: string | null
}

interface StrategyDashboardProps {
  refreshTrigger: number
}

export const StrategyDashboard = ({ refreshTrigger }: StrategyDashboardProps) => {
  const [result, setResult] = useState<StrategyRunResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runStrategyAnalysis = async (market: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch('/api/v1/strategy/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          market,
          run_date: new Date().toISOString().split('T')[0],
          ai_output: null,
          analysis_log_id: null,
          trailing_configs: null,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data: StrategyRunResult = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
      console.error('Strategy analysis failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case 'buy': return '#28a745'
      case 'hold': return '#6c757d'
      case 'partial_sell': return '#ffc107'
      case 'full_exit': return '#dc3545'
      default: return '#6c757d'
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

  return (
    <div style={{
      padding: '20px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      border: '1px solid #dee2e6'
    }}>
      <h2 style={{
        margin: '0 0 20px 0',
        color: '#333',
        fontSize: '1.5rem',
        borderBottom: '1px solid #dee2e6',
        paddingBottom: '10px'
      }}>
        🎯 Strategy Dashboard
      </h2>

      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <button
          onClick={() => runStrategyAnalysis('KR')}
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1,
            fontSize: '14px'
          }}
        >
          {loading ? '🔄 Running...' : '🇰🇷 Analyze KR Market'}
        </button>

        <button
          onClick={() => runStrategyAnalysis('US')}
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1,
            fontSize: '14px'
          }}
        >
          {loading ? '🔄 Running...' : '🇺🇸 Analyze US Market'}
        </button>
      </div>

      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '15px',
            marginBottom: '20px'
          }}>
            <div style={{
              padding: '15px',
              backgroundColor: 'white',
              borderRadius: '6px',
              border: '1px solid #dee2e6',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007bff' }}>
                {result.total_tickers_analyzed}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Total Analyzed</div>
            </div>

            <div style={{
              padding: '15px',
              backgroundColor: 'white',
              borderRadius: '6px',
              border: '1px solid #dee2e6',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
                {result.changed_count}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Changed Strategies</div>
            </div>

            <div style={{
              padding: '15px',
              backgroundColor: 'white',
              borderRadius: '6px',
              border: '1px solid #dee2e6',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc3545' }}>
                {result.market}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Market</div>
            </div>
          </div>

          {result.strategies.length > 0 && (
            <div>
              <h3 style={{ margin: '20px 0 15px 0', color: '#333' }}>
                Strategy Recommendations
              </h3>
              
              <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {result.strategies.map((strategy, index) => (
                  <div
                    key={`${strategy.ticker}-${index}`}
                    style={{
                      padding: '15px',
                      backgroundColor: 'white',
                      border: '1px solid #dee2e6',
                      borderRadius: '6px',
                      marginBottom: '10px',
                      boxShadow: strategy.changed_from_last ? '0 2px 4px rgba(0,123,255,0.1)' : 'none'
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '10px'
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px'
                      }}>
                        <span style={{
                          fontSize: '18px',
                          fontWeight: 'bold',
                          color: '#333'
                        }}>
                          {strategy.ticker}
                        </span>
                        {strategy.changed_from_last && (
                          <span style={{
                            fontSize: '12px',
                            color: '#007bff',
                            backgroundColor: '#e3f2fd',
                            padding: '2px 8px',
                            borderRadius: '12px'
                          }}>
                            CHANGED
                          </span>
                        )}
                      </div>
                      
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        <span style={{ fontSize: '20px' }}>
                          {getActionSymbol(strategy.final_action)}
                        </span>
                        <span style={{
                          color: getActionColor(strategy.final_action),
                          fontWeight: 'bold',
                          textTransform: 'uppercase',
                          fontSize: '14px'
                        }}>
                          {strategy.final_action.replace('_', ' ')}
                        </span>
                      </div>
                    </div>

                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                      gap: '10px',
                      fontSize: '13px',
                      color: '#666',
                      marginBottom: '10px'
                    }}>
                      <div>
                        <strong>Source:</strong> {strategy.action_source}
                      </div>
                      <div>
                        <strong>Confidence:</strong> {(strategy.confidence * 100).toFixed(0)}%
                      </div>
                      {strategy.sell_quantity > 0 && (
                        <div>
                          <strong>Sell Qty:</strong> {strategy.sell_quantity.toFixed(4)}
                        </div>
                      )}
                      {strategy.realized_pnl_estimate !== 0 && (
                        <div>
                          <strong>Est. PnL:</strong> 
                          <span style={{
                            color: strategy.realized_pnl_estimate >= 0 ? '#28a745' : '#dc3545',
                            marginLeft: '4px'
                          }}>
                            ${strategy.realized_pnl_estimate.toFixed(2)}
                          </span>
                        </div>
                      )}
                    </div>

                    <div style={{
                      fontSize: '13px',
                      color: '#495057',
                      backgroundColor: '#f8f9fa',
                      padding: '8px',
                      borderRadius: '4px',
                      fontStyle: 'italic'
                    }}>
                      {strategy.rationale || 'No rationale provided'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.strategies.length === 0 && (
            <div style={{
              textAlign: 'center',
              padding: '40px',
              color: '#666',
              fontSize: '16px'
            }}>
              No strategies found. Try creating some positions first.
            </div>
          )}
        </div>
      )}

      {!result && !loading && !error && (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: '#666',
          fontSize: '16px'
        }}>
          Click a button above to run strategy analysis
        </div>
      )}
    </div>
  )
}