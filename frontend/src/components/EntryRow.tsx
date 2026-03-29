/**
 * EntryRow component for individual position entry input
 */

import type { PositionEntry } from '../api/positions'

interface EntryRowProps {
  entry: PositionEntry
  onChange: (entry: PositionEntry) => void
  onRemove: () => void
  canRemove: boolean
}

export function EntryRow({ entry, onChange, onRemove, canRemove }: EntryRowProps) {
  const handleChange = (field: keyof PositionEntry, value: string) => {
    onChange({
      ...entry,
      [field]: value,
    })
  }

  return (
    <div style={{ 
      display: 'flex', 
      gap: '10px', 
      alignItems: 'center',
      marginBottom: '10px',
      padding: '10px',
      border: '1px solid #ddd',
      borderRadius: '4px'
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', flex: '1' }}>
        <label style={{ marginBottom: '5px', fontSize: '12px', fontWeight: 'bold' }}>
          Price
        </label>
        <input
          type="number"
          step="0.01"
          value={entry.price}
          onChange={(e) => handleChange('price', e.target.value)}
          placeholder="100.00"
          style={{
            padding: '8px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            width: '100px'
          }}
        />
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', flex: '1' }}>
        <label style={{ marginBottom: '5px', fontSize: '12px', fontWeight: 'bold' }}>
          Quantity
        </label>
        <input
          type="number"
          step="0.01"
          value={entry.quantity}
          onChange={(e) => handleChange('quantity', e.target.value)}
          placeholder="10"
          style={{
            padding: '8px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            width: '100px'
          }}
        />
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', flex: '2' }}>
        <label style={{ marginBottom: '5px', fontSize: '12px', fontWeight: 'bold' }}>
          Date & Time
        </label>
        <input
          type="datetime-local"
          value={entry.entered_at}
          onChange={(e) => handleChange('entered_at', e.target.value)}
          style={{
            padding: '8px',
            border: '1px solid #ccc',
            borderRadius: '4px',
          }}
        />
      </div>
      
      {canRemove && (
        <button
          onClick={onRemove}
          style={{
            background: '#ff4444',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '8px 12px',
            cursor: 'pointer',
            fontSize: '16px',
            marginTop: '20px'
          }}
          title="Remove entry"
        >
          ×
        </button>
      )}
    </div>
  )
}