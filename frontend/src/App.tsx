import { useState } from 'react'
import { PositionForm } from './components/PositionForm'
import { PositionList } from './components/PositionList'
import { PositionListWithPnL } from './components/PositionListWithPnL'
import { StrategyDashboard } from './components/StrategyDashboard'
import { SchedulerPanel } from './components/SchedulerPanel'

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [showPnLView, setShowPnLView] = useState(false)
  const [activeTab, setActiveTab] = useState<'positions' | 'strategy' | 'scheduler'>('positions')

  const handlePositionCreated = () => {
    setRefreshTrigger(prev => prev + 1)
  }

  return (
    <div style={{ 
      maxWidth: '1200px', 
      margin: '0 auto', 
      padding: '20px',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <header style={{ 
        textAlign: 'center', 
        marginBottom: '40px',
        borderBottom: '1px solid #eee',
        paddingBottom: '20px'
      }}>
        <h1 style={{ 
          color: '#333',
          fontSize: '2.5rem',
          margin: '0 0 10px 0'
        }}>
          Pavlov - Position Manager
        </h1>
        <p style={{ 
          color: '#666',
          fontSize: '1.1rem',
          margin: '0 0 20px 0'
        }}>
          Track your investment positions and AI-powered strategy recommendations
        </p>
        
        {/* Main tabs */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '15px' }}>
          <button
            onClick={() => setActiveTab('positions')}
            style={{
              padding: '10px 20px',
              border: activeTab !== 'positions' ? '1px solid #ddd' : 'none',
              backgroundColor: activeTab === 'positions' ? '#007bff' : 'white',
              color: activeTab === 'positions' ? 'white' : '#333',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📊 Positions
          </button>
          <button
            onClick={() => setActiveTab('strategy')}
            style={{
              padding: '10px 20px',
              border: activeTab !== 'strategy' ? '1px solid #ddd' : 'none',
              backgroundColor: activeTab === 'strategy' ? '#28a745' : 'white',
              color: activeTab === 'strategy' ? 'white' : '#333',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            🎯 Strategy
          </button>
          <button
            onClick={() => setActiveTab('scheduler')}
            style={{
              padding: '10px 20px',
              border: activeTab !== 'scheduler' ? '1px solid #ddd' : 'none',
              backgroundColor: activeTab === 'scheduler' ? '#6610f2' : 'white',
              color: activeTab === 'scheduler' ? 'white' : '#333',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📅 Scheduler
          </button>
        </div>

        {/* Position view selector (only show when positions tab is active) */}
        {activeTab === 'positions' && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
            <button
              onClick={() => setShowPnLView(false)}
              style={{
                padding: '8px 16px',
                border: showPnLView ? '1px solid #ddd' : 'none',
                backgroundColor: showPnLView ? 'white' : '#007bff',
                color: showPnLView ? '#333' : 'white',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              Basic View
            </button>
            <button
              onClick={() => setShowPnLView(true)}
              style={{
                padding: '8px 16px',
                border: !showPnLView ? '1px solid #ddd' : 'none',
                backgroundColor: !showPnLView ? 'white' : '#007bff',
                color: !showPnLView ? '#333' : 'white',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              P&L View
            </button>
          </div>
        )}
      </header>

      {activeTab === 'positions' ? (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: showPnLView ? '1fr 2fr' : '1fr 1fr', 
          gap: '30px',
          alignItems: 'start'
        }}>
          <PositionForm onPositionCreated={handlePositionCreated} />
          {showPnLView ? (
            <PositionListWithPnL refreshTrigger={refreshTrigger} />
          ) : (
            <PositionList refreshTrigger={refreshTrigger} />
          )}
        </div>
      ) : activeTab === 'strategy' ? (
        <div style={{ maxWidth: '100%' }}>
          <StrategyDashboard refreshTrigger={refreshTrigger} />
        </div>
      ) : (
        <div style={{ maxWidth: '100%' }}>
          <SchedulerPanel />
        </div>
      )}
    </div>
  )
}

export default App
