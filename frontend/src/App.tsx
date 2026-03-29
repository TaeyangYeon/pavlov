import { useState } from 'react'
import { PositionForm } from './components/PositionForm'
import { PositionList } from './components/PositionList'
import { PositionListWithPnL } from './components/PositionListWithPnL'

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [showPnLView, setShowPnLView] = useState(false)

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
          Track your investment positions with P&L calculations
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
          <button
            onClick={() => setShowPnLView(false)}
            style={{
              padding: '10px 20px',
              border: showPnLView ? '1px solid #ddd' : 'none',
              backgroundColor: showPnLView ? 'white' : '#007bff',
              color: showPnLView ? '#333' : 'white',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Basic View
          </button>
          <button
            onClick={() => setShowPnLView(true)}
            style={{
              padding: '10px 20px',
              border: !showPnLView ? '1px solid #ddd' : 'none',
              backgroundColor: !showPnLView ? 'white' : '#007bff',
              color: !showPnLView ? '#333' : 'white',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            P&L View
          </button>
        </div>
      </header>

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
    </div>
  )
}

export default App
