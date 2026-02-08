// VIGIL Risk Planning - TypeScript Types

export interface FireSeasonStatus {
  status: 'PRE_SEASON' | 'ACTIVE' | 'POST_SEASON';
  days_until_fire_season?: number;
  days_remaining?: number;
  fire_season_start?: string;
  fire_season_end?: string;
  message: string;
}

export interface Asset {
  ASSET_ID: string;
  ASSET_TYPE: string;
  MATERIAL: string;
  VOLTAGE_CLASS: string;
  INSTALLATION_DATE: string;
  ASSET_AGE_YEARS: number;
  CONDITION_SCORE: number;
  LAST_INSPECTION_DATE: string;
  NEXT_INSPECTION_DUE: string;
  REPLACEMENT_COST: number;
  CIRCUIT_NAME: string;
  FIRE_THREAT_DISTRICT: string;
  REGION: string;
  LATITUDE: number;
  LONGITUDE: number;
}

export interface VegetationEncroachment {
  ENCROACHMENT_ID: string;
  ASSET_ID: string;
  SPECIES: string;
  CURRENT_CLEARANCE_FT: number;
  REQUIRED_CLEARANCE_FT: number;
  CLEARANCE_DEFICIT_FT: number;
  GROWTH_RATE_FT_YEAR: number;
  DAYS_TO_CONTACT: number;
  TRIM_PRIORITY: string;
  LAST_TRIM_DATE: string;
  ESTIMATED_TRIM_COST: number;
  CIRCUIT_NAME: string;
  FIRE_THREAT_DISTRICT: string;
  REGION: string;
  LATITUDE: number;
  LONGITUDE: number;
}

export interface RiskAssessment {
  ASSESSMENT_ID: string;
  ASSET_ID: string;
  FIRE_RISK_SCORE: number;
  IGNITION_PROBABILITY: number;
  CONSEQUENCE_SCORE: number;
  WIND_EXPOSURE_FACTOR: number;
  FUEL_LOAD_FACTOR: number;
  COMPOSITE_RISK_SCORE: number;
  RISK_TIER: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  ASSET_TYPE: string;
  CIRCUIT_NAME: string;
  FIRE_THREAT_DISTRICT: string;
  REGION: string;
  LATITUDE: number;
  LONGITUDE: number;
}

export interface WorkOrder {
  WORK_ORDER_ID: string;
  WORK_ORDER_TYPE: string;
  PRIORITY: string;
  STATUS: string;
  DESCRIPTION: string;
  ESTIMATED_COST: number;
  SCHEDULED_DATE: string;
  COMPLETED_DATE: string | null;
  ASSIGNED_CREW: string;
  ASSET_ID: string;
  ASSET_TYPE: string;
  REGION: string;
  CIRCUIT_NAME: string;
}

export interface MapFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number];
  };
  properties: {
    asset_id: string;
    asset_type: string;
    condition_score: number;
    risk_score: number;
    risk_tier: string;
    fire_district: string;
    region: string;
  };
}

export interface MapData {
  type: 'FeatureCollection';
  features: MapFeature[];
  fire_season: FireSeasonStatus;
}

export interface AgentPersona {
  name: string;
  emoji: string;
  catchphrase: string;
  style: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  persona?: AgentPersona;
  data?: Record<string, unknown>;
  sources?: string[];
  timestamp: string;
}

export interface ChatResponse {
  message: string;
  agent: string;
  persona: AgentPersona;
  data?: Record<string, unknown>;
  sources?: string[];
  fire_season: FireSeasonStatus;
  timestamp: string;
}

export interface WaterTreeingCandidate {
  ASSET_ID: string;
  CABLE_AGE_YEARS: number;
  MATERIAL: string;
  MOISTURE_EXPOSURE: string;
  VOLTAGE_DIP_COUNT: number;
  RAIN_CORRELATION_SCORE: number;
  FAILURE_PROBABILITY: number;
  RISK_TIER: string;
  CUSTOMER_IMPACT_COUNT: number;
  ESTIMATED_REPLACEMENT_COST: number;
  CIRCUIT_NAME: string;
  REGION: string;
}

export interface DashboardMetrics {
  fire_season: FireSeasonStatus;
  asset_summary: Array<{
    REGION: string;
    ASSET_TYPE: string;
    ASSET_COUNT: number;
    AVG_CONDITION: number;
    AVG_AGE: number;
    TOTAL_REPLACEMENT_COST: number;
    POOR_CONDITION_COUNT: number;
  }>;
  risk_summary: Array<{
    REGION: string;
    RISK_TIER: string;
    ASSET_COUNT: number;
    AVG_FIRE_RISK: number;
    AVG_IGNITION_PROB: number;
    AVG_COMPOSITE_RISK: number;
  }>;
  compliance_summary: Array<{
    REGION: string;
    FIRE_THREAT_DISTRICT: string;
    TOTAL_SPANS: number;
    OUT_OF_COMPLIANCE: number;
    AVG_DEFICIT_FT: number;
    TOTAL_TRIM_COST: number;
    CRITICAL_DAYS_TO_CONTACT: number;
  }>;
  work_order_backlog: Array<{
    REGION: string;
    WORK_ORDER_TYPE: string;
    STATUS: string;
    ORDER_COUNT: number;
    TOTAL_COST: number;
    AVG_AGE_DAYS: number;
  }>;
}

export type Region = 'NorCal' | 'SoCal' | 'PNW' | 'Southwest' | 'Mountain';

export const REGIONS: Region[] = ['NorCal', 'SoCal', 'PNW', 'Southwest', 'Mountain'];

export const RISK_TIER_COLORS: Record<string, string> = {
  CRITICAL: '#dc2626',
  HIGH: '#f97316',
  MEDIUM: '#facc15',
  LOW: '#22c55e',
};

export const FIRE_DISTRICT_COLORS: Record<string, string> = {
  TIER_3: '#b91c1c',
  TIER_2: '#ea580c',
  TIER_1: '#ca8a04',
  NON_HFTD: '#4b5563',
};
