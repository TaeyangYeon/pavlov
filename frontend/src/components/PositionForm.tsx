/**
 * PositionForm component for creating positions with multiple entries
 */

import { useState } from 'react'
import type { PositionEntry, PositionCreate } from '../api/positions'
import { positionAPI } from '../api/positions'
import { EntryRow } from './EntryRow'

interface PositionFormProps {
  onPositionCreated: () => void
}

export function PositionForm({ onPositionCreated }: PositionFormProps) {
  const [ticker, setTicker] = useState('')
  const [market, setMarket] = useState<'KR' | 'US'>('US')
  const [entries, setEntries] = useState<PositionEntry[]>([
    {
      price: '',
      quantity: '',
      entered_at: new Date().toISOString().slice(0, 16) // YYYY-MM-DDTHH:MM format
    }
  ])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const calculateAvgPrice = (): number | null => {
    const validEntries = entries.filter(
      e => e.price && e.quantity && Number(e.price) > 0 && Number(e.quantity) > 0
    )
    
    if (validEntries.length === 0) return null
    
    const totalValue = validEntries.reduce(
      (sum, e) => sum + Number(e.price) * Number(e.quantity), 
      0
    )
    const totalQuantity = validEntries.reduce(
      (sum, e) => sum + Number(e.quantity), 
      0
    )
    
    return totalQuantity > 0 ? totalValue / totalQuantity : null
  }

  const addEntry = () => {
    setEntries([
      ...entries,
      {
        price: '',
        quantity: '',
        entered_at: new Date().toISOString().slice(0, 16)
      }
    ])
  }

  const removeEntry = (index: number) => {
    if (entries.length > 1) {
      setEntries(entries.filter((_, i) => i !== index))
    }
  }

  const updateEntry = (index: number, entry: PositionEntry) => {
    const newEntries = [...entries]
    newEntries[index] = entry
    setEntries(newEntries)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      // Validate entries
      const validEntries = entries.filter(
        e => e.price && e.quantity && Number(e.price) > 0 && Number(e.quantity) > 0
      )

      if (validEntries.length === 0) {
        throw new Error('At least one valid entry is required')
      }

      if (!ticker.trim()) {
        throw new Error('Ticker is required')
      }

      // Convert datetime-local format to ISO string
      const formattedEntries = validEntries.map(e => ({
        ...e,
        entered_at: new Date(e.entered_at).toISOString()
      }))

      const positionData: PositionCreate = {
        ticker: ticker.trim().toUpperCase(),
        market,
        entries: formattedEntries
      }

      await positionAPI.createPosition(positionData)

      // Reset form
      setTicker('')
      setMarket('US')
      setEntries([{
        price: '',
        quantity: '',
        entered_at: new Date().toISOString().slice(0, 16)
      }])

      onPositionCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create position')
    } finally {
      setIsSubmitting(false)
    }
  }

  const avgPrice = calculateAvgPrice()

  return (
    <div style={{ 
      padding: '20px', 
      border: '1px solid #ddd', 
      borderRadius: '8px',
      backgroundColor: '#f9f9f9'
    }}>
      <h2 style={{ marginTop: '0', marginBottom: '20px' }}>Create New Position</h2>
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
            <div style={{ flex: '1' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Ticker Symbol
              </label>
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                placeholder="AAPL"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  textTransform: 'uppercase'
                }}
                required
              />
            </div>
            
            <div style={{ flex: '1' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Market
              </label>
              <select
                value={market}
                onChange={(e) => setMarket(e.target.value as 'KR' | 'US')}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ccc',
                  borderRadius: '4px'
                }}
              >
                <option value="US">US Market</option>
                <option value="KR">Korean Market</option>
              </select>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ marginBottom: '15px' }}>Position Entries</h3>
          
          {entries.map((entry, index) => (
            <EntryRow
              key={index}
              entry={entry}
              onChange={(updatedEntry) => updateEntry(index, updatedEntry)}
              onRemove={() => removeEntry(index)}
              canRemove={entries.length > 1}
            />
          ))}
          
          <button
            type="button"
            onClick={addEntry}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              padding: '10px 15px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
          >
            + Add Entry
          </button>
        </div>

        {avgPrice !== null && (
          <div style={{ 
            marginBottom: '20px', 
            padding: '15px',
            backgroundColor: '#e8f5e8',
            borderRadius: '4px',
            border: '1px solid #4caf50'
          }}>
            <strong>Calculated Average Price: ${avgPrice.toFixed(4)}</strong>
          </div>
        )}

        {error && (
          <div style={{
            marginBottom: '20px',
            padding: '10px',
            backgroundColor: '#ffebee',
            color: '#c62828',
            borderRadius: '4px',
            border: '1px solid #e57373'
          }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting || !ticker.trim() || entries.every(e => !e.price || !e.quantity)}
          style={{
            background: isSubmitting ? '#ccc' : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '12px 24px',
            cursor: isSubmitting ? 'not-allowed' : 'pointer',
            fontSize: '16px',
            fontWeight: 'bold'
          }}
        >
          {isSubmitting ? 'Creating...' : 'Create Position'}
        </button>
      </form>
    </div>
  )
}