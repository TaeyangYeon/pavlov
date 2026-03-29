/**
 * API client for position management
 */

export interface PositionEntry {
  price: string
  quantity: string
  entered_at: string
}

export interface PositionCreate {
  ticker: string
  market: string
  entries: PositionEntry[]
}

export interface PositionResponse {
  id: string
  ticker: string
  market: string
  entries: PositionEntry[]
  avg_price: string
  status: string
  created_at: string
  updated_at: string
}

class PositionAPI {
  private baseUrl = '/api/v1/positions'

  async fetchPositions(): Promise<PositionResponse[]> {
    const response = await fetch(this.baseUrl)
    if (!response.ok) {
      throw new Error(`Failed to fetch positions: ${response.statusText}`)
    }
    return response.json()
  }

  async createPosition(data: PositionCreate): Promise<PositionResponse> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to create position: ${response.statusText}`)
    }
    return response.json()
  }

  async addEntry(id: string, entry: PositionEntry): Promise<PositionResponse> {
    const response = await fetch(`${this.baseUrl}/${id}/entries`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(entry),
    })
    if (!response.ok) {
      throw new Error(`Failed to add entry: ${response.statusText}`)
    }
    return response.json()
  }

  async closePosition(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to close position: ${response.statusText}`)
    }
  }
}

export const positionAPI = new PositionAPI()