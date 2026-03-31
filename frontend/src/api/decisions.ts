/**
 * API client for decision recording and management
 */

export interface DecisionCreate {
  ticker: string;
  market: "KR" | "US";
  action: "buy" | "sell" | "hold";
  price: number;
  quantity: number;
  notes?: string;
  override_cooling_off?: boolean;
}

export interface DecisionResponse {
  id: string;
  ticker: string;
  action: string;
  price: number;
  quantity: number;
  ai_suggested: boolean;
  cooling_off_warning: boolean;
  notes: string | null;
  created_at: string;
}

const API_BASE = '/api/v1';

export async function recordDecision(data: DecisionCreate): Promise<DecisionResponse> {
  const response = await fetch(`${API_BASE}/decisions/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to record decision: ${response.statusText}`);
  }
  
  return response.json();
}

export async function listDecisions(ticker?: string, days?: number): Promise<DecisionResponse[]> {
  const params = new URLSearchParams();
  if (ticker) params.append('ticker', ticker);
  if (days) params.append('days', days.toString());
  
  const response = await fetch(`${API_BASE}/decisions/?${params}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch decisions: ${response.statusText}`);
  }
  
  return response.json();
}