import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Activity,
  TreePine,
  Flame,
  Zap,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Clock,
  Droplets,
  Filter,
  Download,
  RefreshCw,
  ChevronDown,
  Search,
  Brain
} from 'lucide-react'
import {
  getMLSummary,
  getAssetHealthPredictions,
  getVegetationGrowthPredictions,
  getIgnitionRiskPredictions,
  getCableFailurePredictions,
  getCombinedRiskByRegion
} from '../services/api'
import { MLExplainability } from '../components/MLExplainability'

type TabType = 'overview' | 'health' | 'vegetation' | 'ignition' | 'cable' | 'explainability'

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

interface HealthPrediction {
  PREDICTION_ID: string
  ASSET_ID: string
  ASSET_TYPE: string
  ACTUAL_HEALTH_SCORE: number
  PREDICTED_HEALTH_SCORE: number
  HEALTH_DELTA: number
  MODEL_CONFIDENCE: number
  PREDICTED_CONDITION: string
  PREDICTION_DATE: string
}

interface VegPrediction {
  PREDICTION_ID: string
  ENCROACHMENT_ID: string
  ASSET_ID: string
  SPECIES: string
  ACTUAL_GROWTH_RATE: number
  PREDICTED_GROWTH_RATE: number
  CURRENT_CLEARANCE_FT: number
  PREDICTED_DAYS_TO_CONTACT: number
  GROWTH_RISK: string
}

interface IgnitionPrediction {
  PREDICTION_ID: string
  ASSET_ID: string
  ASSET_TYPE: string
  PREDICTED_IGNITION_RISK: number
  CONDITION_SCORE: number
  AVG_CLEARANCE_DEFICIT: number
  RISK_LEVEL: string
}

interface CablePrediction {
  PREDICTION_ID: string
  ASSET_ID: string
  MATERIAL: string
  ASSET_AGE_YEARS: number
  MOISTURE_EXPOSURE: string
  RAIN_CORRELATED_DIPS: number
  RAIN_VOLTAGE_CORRELATION: number
  RISK_LEVEL: string
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

const tabs: { id: TabType; label: string; icon: React.ReactNode; color: string }[] = [
  { id: 'overview', label: 'Overview', icon: <Activity size={16} />, color: 'purple' },
  { id: 'health', label: 'Asset Health', icon: <TrendingDown size={16} />, color: 'blue' },
  { id: 'vegetation', label: 'Vegetation', icon: <TreePine size={16} />, color: 'green' },
  { id: 'ignition', label: 'Ignition Risk', icon: <Flame size={16} />, color: 'orange' },
  { id: 'cable', label: 'Water Treeing', icon: <Zap size={16} />, color: 'purple' },
  { id: 'explainability', label: 'Explainability', icon: <Brain size={16} />, color: 'purple' }
]

function StatusBadge({ status, size = 'md' }: { status: string; size?: 'sm' | 'md' }) {
  const colors: Record<string, string> = {
    CRITICAL: 'bg-red-500/20 text-red-300 border-red-500/30',
    HIGH: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    MEDIUM: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    LOW: 'bg-green-500/20 text-green-300 border-green-500/30',
    POOR: 'bg-red-500/20 text-red-300 border-red-500/30',
    FAIR: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    GOOD: 'bg-green-500/20 text-green-300 border-green-500/30'
  }
  
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-medium ${colors[status] || 'bg-gray-500/20 text-gray-300'} ${size === 'sm' ? 'text-[10px]' : ''}`}>
      {status}
    </span>
  )
}

function ModelSummaryCard({ model, icon, color, onClick }: { model: MLModel; icon: React.ReactNode; color: string; onClick: () => void }) {
  const alertCount = model.critical_count || model.high_risk_count || model.at_risk_count || 0
  const colorClasses: Record<string, string> = {
    blue: 'border-blue-500/30 hover:border-blue-500/50',
    green: 'border-green-500/30 hover:border-green-500/50',
    orange: 'border-orange-500/30 hover:border-orange-500/50',
    purple: 'border-purple-500/30 hover:border-purple-500/50'
  }
  const iconColors: Record<string, string> = {
    blue: 'text-blue-400 bg-blue-500/10',
    green: 'text-green-400 bg-green-500/10',
    orange: 'text-orange-400 bg-orange-500/10',
    purple: 'text-purple-400 bg-purple-500/10'
  }
  
  return (
    <div 
      onClick={onClick}
      className={`bg-gray-800/50 rounded-xl p-5 border ${colorClasses[color]} cursor-pointer transition-all hover:scale-[1.02]`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg ${iconColors[color]}`}>
          {icon}
        </div>
        {model.hidden_discovery && (
          <span className="text-[10px] px-2 py-1 rounded-full bg-purple-500/20 text-purple-300 font-medium">
            HIDDEN DISCOVERY
          </span>
        )}
      </div>
      
      <h3 className="font-semibold text-white text-lg mb-1">{model.name}</h3>
      <p className="text-sm text-slate-500 mb-4">{model.algorithm}</p>
      
      <div className="flex items-end justify-between">
        <div>
          <div className="text-3xl font-bold text-white">
            {model.total_predictions.toLocaleString()}
          </div>
          <div className="text-xs text-slate-500">total predictions</div>
        </div>
        
        {alertCount > 0 && (
          <div className="flex items-center gap-2 bg-red-500/10 px-3 py-1.5 rounded-lg">
            <AlertTriangle size={16} className="text-red-400" />
            <span className="text-lg font-bold text-red-400">{alertCount}</span>
            <span className="text-xs text-red-400/70">alerts</span>
          </div>
        )}
      </div>
    </div>
  )
}

function HealthTable({ predictions }: { predictions: HealthPrediction[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Asset ID</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Type</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Actual</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Predicted</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Delta</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Confidence</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Condition</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map((p) => (
            <tr key={p.PREDICTION_ID} className="border-b border-gray-800 hover:bg-gray-800/50">
              <td className="py-3 px-4 font-mono text-xs text-white">{p.ASSET_ID}</td>
              <td className="py-3 px-4 text-slate-300">{p.ASSET_TYPE}</td>
              <td className="py-3 px-4 text-slate-300">{(p.ACTUAL_HEALTH_SCORE || 0).toFixed(2)}</td>
              <td className="py-3 px-4 text-slate-300">{(p.PREDICTED_HEALTH_SCORE || 0).toFixed(2)}</td>
              <td className="py-3 px-4">
                <span className={`flex items-center gap-1 ${(p.HEALTH_DELTA || 0) < 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {(p.HEALTH_DELTA || 0) < 0 ? <TrendingDown size={14} /> : <TrendingUp size={14} />}
                  {Math.abs(p.HEALTH_DELTA || 0).toFixed(3)}
                </span>
              </td>
              <td className="py-3 px-4 text-slate-300">{((p.MODEL_CONFIDENCE || 0) * 100).toFixed(0)}%</td>
              <td className="py-3 px-4"><StatusBadge status={p.PREDICTED_CONDITION} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function VegetationTable({ predictions }: { predictions: VegPrediction[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Asset ID</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Species</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Growth Rate</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Clearance</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Days to Contact</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Risk</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map((p) => (
            <tr key={p.PREDICTION_ID} className="border-b border-gray-800 hover:bg-gray-800/50">
              <td className="py-3 px-4 font-mono text-xs text-white">{p.ASSET_ID}</td>
              <td className="py-3 px-4 text-slate-300">{p.SPECIES}</td>
              <td className="py-3 px-4 text-slate-300">{p.PREDICTED_GROWTH_RATE} ft/yr</td>
              <td className="py-3 px-4 text-slate-300">{(p.CURRENT_CLEARANCE_FT || 0).toFixed(1)} ft</td>
              <td className="py-3 px-4">
                <span className={`flex items-center gap-1 ${(p.PREDICTED_DAYS_TO_CONTACT || 999) < 30 ? 'text-red-400' : 'text-slate-300'}`}>
                  <Clock size={14} />
                  {(p.PREDICTED_DAYS_TO_CONTACT || 0).toFixed(0)} days
                </span>
              </td>
              <td className="py-3 px-4"><StatusBadge status={p.GROWTH_RISK} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function IgnitionTable({ predictions }: { predictions: IgnitionPrediction[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Asset ID</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Type</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Condition Score</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Clearance Deficit</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Risk Level</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map((p) => (
            <tr key={p.PREDICTION_ID} className="border-b border-gray-800 hover:bg-gray-800/50">
              <td className="py-3 px-4 font-mono text-xs text-white">{p.ASSET_ID}</td>
              <td className="py-3 px-4 text-slate-300">{p.ASSET_TYPE}</td>
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${(p.CONDITION_SCORE || 0) < 0.4 ? 'bg-red-500' : (p.CONDITION_SCORE || 0) < 0.7 ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${(p.CONDITION_SCORE || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-slate-300 text-xs">{((p.CONDITION_SCORE || 0) * 100).toFixed(0)}%</span>
                </div>
              </td>
              <td className="py-3 px-4 text-slate-300">{(p.AVG_CLEARANCE_DEFICIT || 0).toFixed(1)} ft</td>
              <td className="py-3 px-4"><StatusBadge status={p.RISK_LEVEL} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function CableTable({ predictions }: { predictions: CablePrediction[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Asset ID</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Material</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Age</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Moisture</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Rain Dips</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Correlation</th>
            <th className="text-left py-3 px-4 text-slate-400 font-medium">Risk</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map((p) => (
            <tr key={p.PREDICTION_ID} className="border-b border-gray-800 hover:bg-gray-800/50">
              <td className="py-3 px-4 font-mono text-xs text-white">{p.ASSET_ID}</td>
              <td className="py-3 px-4">
                <span className={`px-2 py-0.5 rounded text-xs ${p.MATERIAL === 'XLPE' ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-500/20 text-gray-300'}`}>
                  {p.MATERIAL}
                </span>
              </td>
              <td className="py-3 px-4 text-slate-300">{p.ASSET_AGE_YEARS} yrs</td>
              <td className="py-3 px-4">
                <span className={`flex items-center gap-1 ${p.MOISTURE_EXPOSURE === 'HIGH' ? 'text-blue-400' : 'text-slate-400'}`}>
                  <Droplets size={14} />
                  {p.MOISTURE_EXPOSURE}
                </span>
              </td>
              <td className="py-3 px-4 text-slate-300">{p.RAIN_CORRELATED_DIPS}</td>
              <td className="py-3 px-4">
                <span className={`${(p.RAIN_VOLTAGE_CORRELATION || 0) < -0.5 ? 'text-red-400' : 'text-slate-300'}`}>
                  {(p.RAIN_VOLTAGE_CORRELATION || 0).toFixed(3)}
                </span>
              </td>
              <td className="py-3 px-4"><StatusBadge status={p.RISK_LEVEL} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function MLPredictions() {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [searchTerm, setSearchTerm] = useState('')
  
  const { data: mlSummary, isLoading: summaryLoading, refetch: refetchSummary } = useQuery({
    queryKey: ['mlSummary'],
    queryFn: getMLSummary
  })
  
  const { data: healthData } = useQuery({
    queryKey: ['healthPredictions'],
    queryFn: () => getAssetHealthPredictions(200),
    enabled: activeTab === 'health' || activeTab === 'overview'
  })
  
  const { data: vegData } = useQuery({
    queryKey: ['vegPredictions'],
    queryFn: () => getVegetationGrowthPredictions(200),
    enabled: activeTab === 'vegetation' || activeTab === 'overview'
  })
  
  const { data: ignitionData } = useQuery({
    queryKey: ['ignitionPredictions'],
    queryFn: () => getIgnitionRiskPredictions(200),
    enabled: activeTab === 'ignition' || activeTab === 'overview'
  })
  
  const { data: cableData } = useQuery({
    queryKey: ['cablePredictions'],
    queryFn: () => getCableFailurePredictions(200),
    enabled: activeTab === 'cable' || activeTab === 'overview'
  })
  
  const { data: regionData } = useQuery({
    queryKey: ['regionRisk'],
    queryFn: getCombinedRiskByRegion,
    enabled: activeTab === 'overview'
  })
  
  if (summaryLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading ML Predictions...</p>
        </div>
      </div>
    )
  }
  
  const models = (mlSummary as { models: Record<string, MLModel> })?.models
  
  return (
    <div className="h-full flex flex-col bg-gray-900">
      <div className="p-6 border-b border-gray-700/50">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <Activity className="text-purple-400" />
              ML Predictions
            </h1>
            <p className="text-slate-400 mt-1">Machine learning insights for proactive risk management</p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => refetchSummary()}
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm text-white transition-colors"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm text-white transition-colors">
              <Download size={16} />
              Export
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && models && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <ModelSummaryCard 
                model={models.asset_health} 
                icon={<TrendingDown size={24} />} 
                color="blue"
                onClick={() => setActiveTab('health')}
              />
              <ModelSummaryCard 
                model={models.vegetation_growth} 
                icon={<TreePine size={24} />} 
                color="green"
                onClick={() => setActiveTab('vegetation')}
              />
              <ModelSummaryCard 
                model={models.ignition_risk} 
                icon={<Flame size={24} />} 
                color="orange"
                onClick={() => setActiveTab('ignition')}
              />
              <ModelSummaryCard 
                model={models.cable_failure} 
                icon={<Zap size={24} />} 
                color="purple"
                onClick={() => setActiveTab('cable')}
              />
            </div>
            
            {regionData && (
              <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                <h2 className="text-lg font-semibold text-white mb-4">Risk by Region</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  {(regionData as { regions: RegionRisk[] }).regions?.map((region: RegionRisk) => (
                    <div key={region.REGION} className="bg-gray-900/50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-white">{region.REGION}</span>
                        {region.EMERGENCY_COUNT > 0 && (
                          <span className="flex items-center gap-1 text-red-400 text-xs">
                            <AlertTriangle size={12} />
                            {region.EMERGENCY_COUNT}
                          </span>
                        )}
                      </div>
                      <div className="text-2xl font-bold text-white mb-1">{region.ASSET_COUNT.toLocaleString()}</div>
                      <div className="text-xs text-slate-500">assets</div>
                      <div className="mt-3 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${
                            Number(region.AVG_RISK_SCORE || 0) > 60 ? 'bg-red-500' :
                            Number(region.AVG_RISK_SCORE || 0) > 40 ? 'bg-orange-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(Number(region.AVG_RISK_SCORE || 0), 100)}%` }}
                        />
                      </div>
                      <div className="text-xs text-slate-500 mt-1">Risk: {Number(region.AVG_RISK_SCORE || 0).toFixed(0)}/100</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'health' && healthData && (
          <div className="bg-gray-800/50 rounded-xl border border-gray-700">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <TrendingDown className="text-blue-400" />
                Asset Health Predictions
              </h2>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search assets..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9 pr-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>
            </div>
            <HealthTable 
              predictions={((healthData as { predictions: HealthPrediction[] }).predictions || [])
                .filter(p => !searchTerm || p.ASSET_ID.toLowerCase().includes(searchTerm.toLowerCase()))} 
            />
          </div>
        )}
        
        {activeTab === 'vegetation' && vegData && (
          <div className="bg-gray-800/50 rounded-xl border border-gray-700">
            <div className="p-4 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <TreePine className="text-green-400" />
                Vegetation Growth Predictions
              </h2>
            </div>
            <VegetationTable predictions={(vegData as { predictions: VegPrediction[] }).predictions || []} />
          </div>
        )}
        
        {activeTab === 'ignition' && ignitionData && (
          <div className="bg-gray-800/50 rounded-xl border border-gray-700">
            <div className="p-4 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Flame className="text-orange-400" />
                Ignition Risk Predictions
              </h2>
            </div>
            <IgnitionTable predictions={(ignitionData as { predictions: IgnitionPrediction[] }).predictions || []} />
          </div>
        )}
        
        {activeTab === 'cable' && cableData && (
          <div className="bg-gray-800/50 rounded-xl border border-gray-700">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Zap className="text-purple-400" />
                  Water Treeing Detection
                  <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 ml-2">
                    HIDDEN DISCOVERY
                  </span>
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  Detecting invisible underground cable degradation via AMI voltage-rain correlation
                </p>
              </div>
            </div>
            <CableTable predictions={(cableData as { predictions: CablePrediction[] }).predictions || []} />
          </div>
        )}
        
        {activeTab === 'explainability' && (
          <MLExplainability />
        )}
      </div>
    </div>
  )
}
