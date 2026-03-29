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

export interface PositionWithPnL extends PositionResponse {
  current_price: string
  unrealized_pnl: string
  unrealized_pnl_percent: string
  realized_pnl: string
  total_pnl: string
}

export interface TakeProfitLevel {
  pct: number
  sell_ratio: number
}

export interface StopLossLevel {
  pct: number
  sell_ratio: number
}

export interface TpSlEvaluationRequest {
  position_id: string
  current_price: string
  take_profit_levels: TakeProfitLevel[]
  stop_loss_levels: StopLossLevel[]
}

export interface TpSlEvaluationResponse {
  position_id: string
  ticker: string
  action: string
  triggered_by: string
  triggered_level_pct: number | null
  sell_quantity: string
  sell_ratio: string
  current_pnl_pct: string
  realized_pnl_estimate: string
  avg_price: string
  current_price: string
  total_quantity: string
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

  async getPositionWithPnL(id: string, currentPrice: string): Promise<PositionWithPnL> {
    const response = await fetch(`${this.baseUrl}/${id}/pnl?current_price=${currentPrice}`)
    if (!response.ok) {
      throw new Error(`Failed to get position P&L: ${response.statusText}`)
    }
    return response.json()
  }

  async evaluateTpSl(request: TpSlEvaluationRequest): Promise<TpSlEvaluationResponse> {
    const response = await fetch(`${this.baseUrl}/${request.position_id}/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      throw new Error(`Failed to evaluate TP/SL: ${response.statusText}`)
    }
    return response.json()
  }
}

export const positionAPI = new PositionAPI()