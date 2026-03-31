import { MainContent } from '../layout'
import { PositionForm } from './PositionForm'
import { PositionsTable } from './PositionsTable'

export function PositionsPage() {
  return (
    <MainContent title="포지션 관리">
      <div style={{ display: 'grid', gap: '24px', gridTemplateColumns: '1fr 2fr' }}>
        <div className="hide-mobile">
          <PositionForm />
        </div>
        
        <div>
          <PositionsTable />
        </div>
      </div>
      
      {/* Mobile layout - stacked */}
      <div style={{ display: 'none' }} className="show-mobile">
        <div className="mb-4">
          <PositionForm />
        </div>
        <PositionsTable />
      </div>
    </MainContent>
  )
}