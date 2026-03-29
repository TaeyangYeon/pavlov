import { useState } from 'react'
import { PositionForm } from './components/PositionForm'
import { PositionList } from './components/PositionList'

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0)

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
          margin: '0'
        }}>
          Track your investment positions with weighted average cost calculation
        </p>
      </header>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '30px',
        alignItems: 'start'
      }}>
        <PositionForm onPositionCreated={handlePositionCreated} />
        <PositionList refreshTrigger={refreshTrigger} />
      </div>
    </div>
  )
}

export default App
