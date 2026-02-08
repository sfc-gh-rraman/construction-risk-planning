import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Activity,
  TreePine,
  Flame,
  Zap,
  AlertTriangle,
  ChevronRight,
  Brain,
  TrendingDown,
  Clock,
  Droplets
} from 'lucide-react'
import { getMLSummary, getCombinedRiskByRegion, getUrgentMLActions } from '../services/api'

interface MLModel {
  name: string
  icon: string
  total_predictions: number
  critical_count?: number
  high_risk_count?: number
  urgent_count?: number
  at_risk_count?: number
  algorithm: string
  hidden_discovery?: boolean
  status: string
}

interface MLSummaryResponse {
  models: {
    asset_health: MLModel
    vegetation_growth: MLModel
    ignition_risk: MLModel
    cable_failure: MLModel
  }
}

interface RegionRisk {
  REGION: string
  ASSET_COUNT: number
  AVG_RISK_SCORE: number
  EMERGENCY_COUNT: number
  HIGH_PRIORITY_COUNT: number
  CRITICAL_HEALTH_COUNT: number
  HIGH_IGNITION_COUNT: number
  WATER_TREEING_COUNT: number
}

interface UrgentAsset {
  ASSET_ID: string
  ASSET_TYPE: string
  REGION: string
  FIRE_THREAT_DISTRICT: string
  HEALTH_STATUS: string
  IGNITION_RISK_LEVEL: string
  WATER_TREEING_RISK: string
  COMPOSITE_ML_RISK_SCORE: number
  MAINTENANCE_PRIORITY: string
  TOTAL_CUSTOMERS: number
}

const iconMap: Record<string, React.ReactNode> = {
  activity: <Activity size={18} />,
  'tree-pine': <TreePine size={18} />,
  flame: <Flame size={18} />,
  zap: <Zap size={18} />
}

const colorMap: Record<string, string> = {
  activity: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  'tree-pine': 'text-green-400 bg-green-500/10 border-green-500/30',
  flame: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
  zap: 'text-purple-400 bg-purple-500/10 border-purple-500/30'
}

function ModelCard({ model, iconKey }: { model: MLModel; iconKey: string }) {
  const alertCount = model.critical_count || model.high_risk_count || model.at_risk_count || 0
  const hasAlert = alertCount > 0
  
  return (
    <div className={`rounded-lg p-4 border ${colorMap[iconKey]} transition-all hover:scale-[1.02]`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-lg ${colorMap[iconKey]}`}>
          {iconMap[iconKey]}
        </div>
        {model.hidden_discovery && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-medium">
            DISCOVERY
          </span>
        )}
      </div>
      
      <h3 className="font-medium text-white text-sm mb-1">{model.name}</h3>
      <p className="text-xs text-slate-500 mb-3">{model.algorithm}</p>
      
      <div className="flex items-end justify-between">
        <div>
          <div className="text-2xl font-bold text-white">
            {model.total_predictions.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-500">predictions</div>
        </div>
        
        {hasAlert && (
          <div className="flex items-center gap-1 text-red-400">
            <AlertTriangle size={12} />
            <span className="text-sm font-semibold">{alertCount}</span>
          </div>
        )}
      </div>
    </div>
  )
}

function RegionRiskBar({ region }: { region: RegionRisk }) {
  const maxScore = 100
  const scoreWidth = Math.min((region.AVG_RISK_SCORE / maxScore) * 100, 100)
  
  return (
    <div className="mb-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-300">{region.REGION}</span>
        <div className="flex items-center gap-2 text-xs">
          {region.EMERGENCY_COUNT > 0 && (
            <span className="text-red-400 flex items-center gap-0.5">
              <AlertTriangle size={10} />
              {region.EMERGENCY_COUNT}
            </span>
          )}
          <span className="text-slate-500">{region.ASSET_COUNT.toLocaleString()}</span>
        </div>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all ${
            region.AVG_RISK_SCORE > 60 ? 'bg-red-500' :
            region.AVG_RISK_SCORE > 40 ? 'bg-orange-500' :
            'bg-green-500'
          }`}
          style={{ width: `${scoreWidth}%` }}
        />
      </div>
    </div>
  )
}

function UrgentActionCard({ asset }: { asset: UrgentAsset }) {
  const priorityColors: Record<string, string> = {
    EMERGENCY: 'border-red-500/50 bg-red-500/10',
    HIGH: 'border-orange-500/50 bg-orange-500/10'
  }
  
  const riskIcons = []
  if (asset.HEALTH_STATUS === 'CRITICAL') riskIcons.push({ icon: <TrendingDown size={12} />, color: 'text-blue-400', label: 'Health' })
  if (asset.IGNITION_RISK_LEVEL === 'HIGH') riskIcons.push({ icon: <Flame size={12} />, color: 'text-orange-400', label: 'Ignition' })
  if (asset.WATER_TREEING_RISK === 'HIGH') riskIcons.push({ icon: <Droplets size={12} />, color: 'text-purple-400', label: 'Cable' })
  
  return (
    <div className={`rounded-lg p-3 border ${priorityColors[asset.MAINTENANCE_PRIORITY] || 'border-gray-700'}`}>
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="text-xs font-medium text-white">{asset.ASSET_ID}</div>
          <div className="text-[10px] text-slate-500">{asset.ASSET_TYPE}</div>
        </div>
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
          asset.MAINTENANCE_PRIORITY === 'EMERGENCY' ? 'bg-red-500/20 text-red-300' : 'bg-orange-500/20 text-orange-300'
        }`}>
          {asset.MAINTENANCE_PRIORITY}
        </span>
      </div>
      
      <div className="flex items-center gap-3 mb-2">
        {riskIcons.map((r, i) => (
          <div key={i} className={`flex items-center gap-1 ${r.color}`}>
            {r.icon}
            <span className="text-[10px]">{r.label}</span>
          </div>
        ))}
      </div>
      
      <div className="flex items-center justify-between text-[10px] text-slate-500">
        <span>{asset.REGION}</span>
        <span>{asset.FIRE_THREAT_DISTRICT}</span>
        {asset.TOTAL_CUSTOMERS > 0 && (
          <span>{asset.TOTAL_CUSTOMERS.toLocaleString()} customers</span>
        )}
      </div>
    </div>
  )
}

export function MLInsightsPanel() {
  const [activeTab, setActiveTab] = useState<'summary' | 'regions' | 'urgent'>('summary')
  
  const { data: mlSummary, isLoading: summaryLoading } = useQuery<MLSummaryResponse>({
    queryKey: ['mlSummary'],
    queryFn: () => getMLSummary() as Promise<MLSummaryResponse>,
    refetchInterval: 60000
  })
  
  const { data: regionData } = useQuery<{ regions: RegionRisk[] }>({
    queryKey: ['mlRegions'],
    queryFn: () => getCombinedRiskByRegion() as Promise<{ regions: RegionRisk[] }>,
    refetchInterval: 60000
  })
  
  const { data: urgentData } = useQuery<{ urgent_assets: UrgentAsset[]; summary: { emergency_count: number; high_priority_count: number } }>({
    queryKey: ['mlUrgent'],
    queryFn: () => getUrgentMLActions(20) as Promise<{ urgent_assets: UrgentAsset[]; summary: { emergency_count: number; high_priority_count: number } }>,
    refetchInterval: 30000
  })
  
  if (summaryLoading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-32 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }
  
  const totalAlerts = mlSummary ? 
    (mlSummary.models.asset_health.critical_count || 0) +
    (mlSummary.models.ignition_risk.high_risk_count || 0) +
    (mlSummary.models.cable_failure.at_risk_count || 0) : 0
  
  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-700/50">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Brain size={16} className="text-purple-400" />
            <h2 className="text-sm font-semibold text-white">ML Insights</h2>
          </div>
          {totalAlerts > 0 && (
            <div className="flex items-center gap-1 text-red-400 bg-red-500/10 px-2 py-1 rounded-full">
              <AlertTriangle size={12} />
              <span className="text-xs font-medium">{totalAlerts} alerts</span>
            </div>
          )}
        </div>
        
        <div className="flex gap-1">
          {[
            { id: 'summary', label: 'Models' },
            { id: 'regions', label: 'Regions' },
            { id: 'urgent', label: 'Urgent', badge: urgentData?.summary.emergency_count }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {tab.label}
              {tab.badge && tab.badge > 0 && (
                <span className="w-4 h-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'summary' && mlSummary && (
          <div className="grid grid-cols-2 gap-3">
            <ModelCard model={mlSummary.models.asset_health} iconKey="activity" />
            <ModelCard model={mlSummary.models.vegetation_growth} iconKey="tree-pine" />
            <ModelCard model={mlSummary.models.ignition_risk} iconKey="flame" />
            <ModelCard model={mlSummary.models.cable_failure} iconKey="zap" />
          </div>
        )}
        
        {activeTab === 'regions' && regionData && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-medium text-slate-400 uppercase">Risk by Region</h3>
              <div className="flex items-center gap-3 text-[10px]">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" /> Low</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500" /> Med</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> High</span>
              </div>
            </div>
            {regionData.regions.map(region => (
              <RegionRiskBar key={region.REGION} region={region} />
            ))}
          </div>
        )}
        
        {activeTab === 'urgent' && urgentData && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-medium text-slate-400 uppercase flex items-center gap-2">
                <Clock size={12} />
                Urgent Actions
              </h3>
              <span className="text-xs text-slate-500">
                {urgentData.summary.emergency_count + urgentData.summary.high_priority_count} total
              </span>
            </div>
            <div className="space-y-2">
              {urgentData.urgent_assets.slice(0, 10).map(asset => (
                <UrgentActionCard key={asset.ASSET_ID} asset={asset} />
              ))}
            </div>
            {urgentData.urgent_assets.length > 10 && (
              <button className="mt-3 w-full text-xs text-purple-400 hover:text-purple-300 flex items-center justify-center gap-1">
                View all {urgentData.urgent_assets.length} urgent items
                <ChevronRight size={14} />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
