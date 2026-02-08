import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  TreePine,
  Flame,
  Zap,
  ChevronDown,
  ChevronUp,
  Info,
  TrendingUp,
  TrendingDown,
  Minus,
  Brain,
  BarChart3,
  Target
} from 'lucide-react'
import { getFeatureImportance } from '../services/api'

interface Feature {
  name: string
  importance: number
  direction: 'positive' | 'negative' | 'mixed'
  description: string
}

interface ModelExplainability {
  model_name: string
  algorithm: string
  features: Feature[]
  baseline_prediction: number | string
  model_accuracy: number
  discovery_note?: string
}

const MODEL_CONFIGS = [
  { 
    id: 'asset_health', 
    name: 'Asset Health', 
    icon: Activity, 
    color: 'green',
    bgClass: 'from-green-500/20 to-green-600/10 border-green-500/30',
    textClass: 'text-green-400'
  },
  { 
    id: 'vegetation_growth', 
    name: 'Vegetation Growth', 
    icon: TreePine, 
    color: 'emerald',
    bgClass: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30',
    textClass: 'text-emerald-400'
  },
  { 
    id: 'ignition_risk', 
    name: 'Ignition Risk', 
    icon: Flame, 
    color: 'orange',
    bgClass: 'from-orange-500/20 to-orange-600/10 border-orange-500/30',
    textClass: 'text-orange-400'
  },
  { 
    id: 'cable_failure', 
    name: 'Water Treeing', 
    icon: Zap, 
    color: 'blue',
    bgClass: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
    textClass: 'text-blue-400'
  }
]

function FeatureBar({ feature, maxImportance }: { feature: Feature; maxImportance: number }) {
  const widthPercent = (feature.importance / maxImportance) * 100
  
  const barColor = feature.direction === 'positive' 
    ? 'bg-gradient-to-r from-red-500 to-orange-500'
    : feature.direction === 'negative'
    ? 'bg-gradient-to-r from-green-500 to-emerald-500'
    : 'bg-gradient-to-r from-purple-500 to-blue-500'
  
  return (
    <div className="group">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-300">{feature.name}</span>
          {feature.direction === 'positive' && <TrendingUp size={12} className="text-red-400" />}
          {feature.direction === 'negative' && <TrendingDown size={12} className="text-green-400" />}
          {feature.direction === 'mixed' && <Minus size={12} className="text-purple-400" />}
        </div>
        <span className="text-sm font-mono text-slate-400">{(feature.importance * 100).toFixed(0)}%</span>
      </div>
      <div className="relative h-6 bg-gray-800 rounded overflow-hidden">
        <div 
          className={`absolute inset-y-0 left-0 ${barColor} rounded transition-all duration-500`}
          style={{ width: `${widthPercent}%` }}
        />
        <div className="absolute inset-0 flex items-center px-2">
          <span className="text-xs text-white/80 truncate">{feature.description}</span>
        </div>
      </div>
    </div>
  )
}

function ModelCard({ modelId, config }: { modelId: string; config: typeof MODEL_CONFIGS[0] }) {
  const [expanded, setExpanded] = useState(false)
  const Icon = config.icon
  
  const { data, isLoading } = useQuery<ModelExplainability>({
    queryKey: ['featureImportance', modelId],
    queryFn: () => getFeatureImportance(modelId),
    enabled: expanded
  })
  
  const maxImportance = data?.features?.reduce((max, f) => Math.max(max, f.importance), 0) || 1
  
  return (
    <div className={`bg-gradient-to-br ${config.bgClass} border rounded-xl overflow-hidden transition-all`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gray-800/80 flex items-center justify-center">
            <Icon size={20} className={config.textClass} />
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-slate-200">{config.name}</h3>
            <p className="text-xs text-slate-500">Feature importance analysis</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-slate-500">Model Accuracy</div>
            <div className={`text-sm font-bold ${config.textClass}`}>
              {data?.model_accuracy ? `${(data.model_accuracy * 100).toFixed(0)}%` : '--'}
            </div>
          </div>
          {expanded ? <ChevronUp size={20} className="text-slate-400" /> : <ChevronDown size={20} className="text-slate-400" />}
        </div>
      </button>
      
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-700/50">
          {isLoading ? (
            <div className="py-8 text-center text-slate-500">Loading feature importance...</div>
          ) : data ? (
            <div className="space-y-4 mt-4">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <Brain size={14} />
                <span>Algorithm: <strong className="text-slate-300">{data.algorithm}</strong></span>
              </div>
              
              {data.discovery_note && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 flex items-start gap-2">
                  <Info size={14} className="text-blue-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-blue-300">{data.discovery_note}</p>
                </div>
              )}
              
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <BarChart3 size={14} />
                  <span>Feature Importance (SHAP-style)</span>
                </div>
                {data.features.map((feature, i) => (
                  <FeatureBar key={i} feature={feature} maxImportance={maxImportance} />
                ))}
              </div>
              
              <div className="grid grid-cols-3 gap-3 pt-3 border-t border-gray-700/50">
                <div className="text-center">
                  <div className="text-xs text-slate-500">Baseline</div>
                  <div className="text-sm font-bold text-slate-300">
                    {typeof data.baseline_prediction === 'number' 
                      ? data.baseline_prediction.toFixed(2) 
                      : data.baseline_prediction}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-slate-500">Features</div>
                  <div className="text-sm font-bold text-slate-300">{data.features.length}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-slate-500">Accuracy</div>
                  <div className={`text-sm font-bold ${config.textClass}`}>
                    {(data.model_accuracy * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500">Failed to load</div>
          )}
        </div>
      )}
    </div>
  )
}

export function MLExplainability() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
          <Target size={20} className="text-purple-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-200">ML Model Explainability</h2>
          <p className="text-sm text-slate-500">Understand what drives each model's predictions</p>
        </div>
      </div>
      
      <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <Brain size={20} className="text-purple-400 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-purple-300 mb-1">SHAP-Style Feature Importance</h3>
            <p className="text-xs text-slate-400">
              Each bar shows how much a feature contributes to the model's predictions. 
              <span className="text-red-400"> Red bars</span> indicate features that increase risk, 
              <span className="text-green-400"> green bars</span> indicate features that decrease risk.
            </p>
          </div>
        </div>
      </div>
      
      <div className="grid gap-4">
        {MODEL_CONFIGS.map(config => (
          <ModelCard key={config.id} modelId={config.id} config={config} />
        ))}
      </div>
    </div>
  )
}
