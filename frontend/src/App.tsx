import { useState } from 'react'
import { Header, Sidebar } from './components/layout'
import { Dashboard } from './components/dashboard'
import { PositionsPage } from './components/positions'
import { StrategyPage } from './components/strategy'
import { NotificationsPage, SchedulerPage } from './components/notifications'
import { BehaviorDashboard } from './components/behavior/BehaviorDashboard'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'positions':
        return <PositionsPage />
      case 'strategy':
        return <StrategyPage />
      case 'behavior':
        return <BehaviorDashboard />
      case 'notifications':
        return <NotificationsPage />
      case 'scheduler':
        return <SchedulerPage />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="app-layout">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <div style={{ flex: 1 }}>
        <Header />
        {renderCurrentPage()}
      </div>
    </div>
  )
}

export default App