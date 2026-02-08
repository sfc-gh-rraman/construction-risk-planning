// VIGIL Risk Planning - API Service

const API_BASE = '/api';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'API request failed');
  }

  return response.json();
}

// Fire Season
export const getFireSeason = () => fetchAPI('/fire-season');

// Dashboard
import type { DashboardMetrics, MapData } from '../types';
export const getDashboardMetrics = (): Promise<DashboardMetrics> => fetchAPI<DashboardMetrics>('/dashboard/metrics');
export const getMapData = (): Promise<MapData> => fetchAPI<MapData>('/dashboard/map');

// Assets
export const getAssets = (region?: string, assetType?: string) => {
  const params = new URLSearchParams();
  if (region) params.append('region', region);
  if (assetType) params.append('asset_type', assetType);
  return fetchAPI(`/assets?${params}`);
};

export const getAssetSummary = () => fetchAPI('/assets/summary');
export const getReplacementPriorities = (limit = 50) => 
  fetchAPI(`/assets/replacement-priorities?limit=${limit}`);

// Vegetation
export const getVegetation = (region?: string) => {
  const params = region ? `?region=${region}` : '';
  return fetchAPI(`/vegetation${params}`);
};

export const getComplianceSummary = () => fetchAPI('/vegetation/compliance');
export const getTrimPriorities = (limit = 50) => 
  fetchAPI(`/vegetation/trim-priorities?limit=${limit}`);

export const getClearanceRequirement = (voltageClass: string, fireDistrict: string) =>
  fetchAPI(`/vegetation/clearance-requirement?voltage_class=${voltageClass}&fire_district=${fireDistrict}`);

// Risk
export const getRiskAssessments = (region?: string) => {
  const params = region ? `?region=${region}` : '';
  return fetchAPI(`/risk${params}`);
};

export const getRiskSummary = () => fetchAPI('/risk/summary');
export const getPSPSCandidates = () => fetchAPI('/risk/psps-candidates');

// Work Orders
export const getWorkOrders = (status?: string) => {
  const params = status ? `?status=${status}` : '';
  return fetchAPI(`/work-orders${params}`);
};

export const getWorkOrderBacklog = () => fetchAPI('/work-orders/backlog');

export const createWorkOrder = (data: {
  asset_id: string;
  work_order_type: string;
  priority: string;
  description: string;
  estimated_cost: number;
  scheduled_date?: string;
}) => fetchAPI('/work-orders', {
  method: 'POST',
  body: JSON.stringify(data),
});

// Hidden Discovery
export const getWaterTreeingCandidates = () => fetchAPI('/discovery/water-treeing');
export const getAMICorrelation = () => fetchAPI('/discovery/ami-correlation');

// ML Predictions
export const getMLSummary = () => fetchAPI('/ml/summary');
export const getAssetHealthPredictions = (limit = 100) => 
  fetchAPI(`/ml/asset-health?limit=${limit}`);
export const getVegetationGrowthPredictions = (limit = 100) =>
  fetchAPI(`/ml/vegetation-growth?limit=${limit}`);
export const getIgnitionRiskPredictions = (limit = 100) =>
  fetchAPI(`/ml/ignition-risk?limit=${limit}`);
export const getCableFailurePredictions = (limit = 100) =>
  fetchAPI(`/ml/cable-failure?limit=${limit}`);

// Search
export const searchGO95 = (query: string) => 
  fetchAPI(`/search/go95?query=${encodeURIComponent(query)}`);

export const searchVegetationDocs = (query: string) =>
  fetchAPI(`/search/vegetation?query=${encodeURIComponent(query)}`);

// Chat
export const sendChatMessage = async (message: string, persona?: string) => {
  return fetchAPI('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, persona }),
  });
};

// Chat with streaming (SSE via POST)
export interface StreamEvent {
  type: 'fire_season' | 'text' | 'thinking' | 'status' | 'tool_result' | 'chart' | 'complete' | 'error';
  data: unknown;
}

export const streamChatMessage = async (
  message: string,
  callbacks: {
    onFireSeason?: (data: unknown) => void;
    onText?: (chunk: string) => void;
    onThinking?: (data: { title: string; content: string }) => void;
    onStatus?: (data: { title: string; status: string }) => void;
    onToolResult?: (data: { sql?: string; data?: unknown; error?: string }) => void;
    onChart?: (chartSpec: unknown) => void;
    onComplete?: (data: unknown) => void;
    onError?: (error: string) => void;
  },
  persona?: string
) => {
  const abortController = new AbortController();

  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ message, persona }),
      signal: abortController.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent = '';
      let currentData = '';

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          currentData = line.slice(5).trim();
          
          if (currentEvent && currentData) {
            try {
              const parsedData = JSON.parse(currentData);
              
              switch (currentEvent) {
                case 'fire_season':
                  callbacks.onFireSeason?.(parsedData);
                  break;
                case 'text':
                  callbacks.onText?.(parsedData.chunk);
                  break;
                case 'thinking':
                  callbacks.onThinking?.(parsedData);
                  break;
                case 'status':
                  callbacks.onStatus?.(parsedData);
                  break;
                case 'tool_result':
                  callbacks.onToolResult?.(parsedData);
                  break;
                case 'chart':
                  callbacks.onChart?.(parsedData.chart_spec);
                  break;
                case 'complete':
                  callbacks.onComplete?.(parsedData);
                  break;
                case 'error':
                  callbacks.onError?.(parsedData.error);
                  break;
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', currentData);
            }
            currentEvent = '';
            currentData = '';
          }
        }
      }
    }
  } catch (error) {
    if ((error as Error).name !== 'AbortError') {
      callbacks.onError?.((error as Error).message);
    }
  }

  return () => abortController.abort();
};
