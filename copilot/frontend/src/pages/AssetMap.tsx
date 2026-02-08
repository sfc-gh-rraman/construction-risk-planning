import { useEffect, useState, useMemo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import { useQuery } from '@tanstack/react-query'
import { 
  Zap, 
  AlertTriangle, 
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  Clock,
  Filter,
  TreePine,
  Droplets,
  Flame,
  Activity,
  Brain,
  Loader2
} from 'lucide-react'
import { getMapData, getAssetMLPredictions } from '../services/api'
import type { MapData, MapFeature } from '../types'
import { REGIONS, RISK_TIER_COLORS } from '../types'
import 'leaflet/dist/leaflet.css'

interface MLPrediction {
  health: {
    PREDICTED_HEALTH_SCORE: number
    PREDICTED_CONDITION: string
    HEALTH_DELTA: number
    MODEL_CONFIDENCE: number
  } | null
  vegetation: {
    PREDICTED_DAYS_TO_CONTACT: number
    GROWTH_RISK: string
    PREDICTED_GROWTH_RATE: number
    SPECIES: string
  } | null
  ignition: {
    RISK_LEVEL: string
    CONDITION_SCORE: number
    AVG_CLEARANCE_DEFICIT: number
  } | null
  cable: {
    PREDICTED_WATER_TREEING: number
    RAIN_VOLTAGE_CORRELATION: number
    RISK_LEVEL: string
    RAIN_CORRELATED_DIPS: number
    MOISTURE_EXPOSURE: string
  } | null
  combined: {
    COMPOSITE_ML_RISK_SCORE: number
    MAINTENANCE_PRIORITY: string
    HEALTH_STATUS: string
    IGNITION_RISK_LEVEL: string
    WATER_TREEING_RISK: string
  } | null
}

interface EnrichedAsset extends MapFeature {
  mlPrediction?: MLPrediction
}

function generateRealAIInsight(ml: MLPrediction | undefined, asset: MapFeature['properties']): { text: string; icon: 'water' | 'fire' | 'health' | 'veg' | 'default'; confidence: number } {
  if (!ml) {
    return { text: 'Loading ML predictions...', icon: 'default', confidence: 0 }
  }

  if (ml.cable?.PREDICTED_WATER_TREEING === 1) {
    const correlation = (ml.cable.RAIN_VOLTAGE_CORRELATION * 100).toFixed(0)
    const dips = ml.cable.RAIN_CORRELATED_DIPS
    return {
      text: `🔍 WATER TREEING DETECTED: ${correlation}% rain-voltage correlation with ${dips} voltage dips. Moisture intrusion likely.`,
      icon: 'water',
      confidence: ml.cable.RAIN_VOLTAGE_CORRELATION
    }
  }

  if (ml.ignition?.RISK_LEVEL === 'HIGH') {
    const deficit = ml.ignition.AVG_CLEARANCE_DEFICIT?.toFixed(1) || '0'
    return {
      text: `🔥 HIGH IGNITION RISK: Condition score ${(ml.ignition.CONDITION_SCORE * 100).toFixed(0)}%, clearance deficit ${deficit}ft in ${asset.fire_district} zone.`,
      icon: 'fire',
      confidence: 0.85
    }
  }

  if (ml.vegetation?.GROWTH_RISK === 'HIGH') {
    const days = ml.vegetation.PREDICTED_DAYS_TO_CONTACT
    const species = ml.vegetation.SPECIES || 'vegetation'
    return {
      text: `🌳 URGENT: ${species} contact in ${days} days at ${(ml.vegetation.PREDICTED_GROWTH_RATE * 12).toFixed(1)}ft/year growth rate.`,
      icon: 'veg',
      confidence: 0.78
    }
  }

  if (ml.health?.PREDICTED_CONDITION === 'CRITICAL') {
    const score = (ml.health.PREDICTED_HEALTH_SCORE * 100).toFixed(0)
    const delta = ml.health.HEALTH_DELTA > 0 ? 'improving' : 'declining'
    return {
      text: `⚠️ CRITICAL HEALTH: ${score}% predicted score (${delta}). Model confidence: ${(ml.health.MODEL_CONFIDENCE * 100).toFixed(0)}%`,
      icon: 'health',
      confidence: ml.health.MODEL_CONFIDENCE
    }
  }

  if (ml.combined?.MAINTENANCE_PRIORITY === 'EMERGENCY') {
    const score = (ml.combined.COMPOSITE_ML_RISK_SCORE * 100).toFixed(0)
    return {
      text: `🚨 EMERGENCY: Composite ML risk score ${score}%. Multiple risk factors converging.`,
      icon: 'default',
      confidence: ml.combined.COMPOSITE_ML_RISK_SCORE
    }
  }

  if (ml.health) {
    const score = (ml.health.PREDICTED_HEALTH_SCORE * 100).toFixed(0)
    const condition = ml.health.PREDICTED_CONDITION
    return {
      text: `✅ Health Score: ${score}% (${condition}). Model confidence: ${(ml.health.MODEL_CONFIDENCE * 100).toFixed(0)}%`,
      icon: 'health',
      confidence: ml.health.MODEL_CONFIDENCE
    }
  }

  return { text: 'No ML predictions available for this asset.', icon: 'default', confidence: 0 }
}

function generateNextAction(ml: MLPrediction | undefined, asset: MapFeature['properties']): { action: string; days: number; source: string } {
  if (!ml) {
    return { action: 'Pending ML analysis', days: 30, source: 'default' }
  }

  if (ml.cable?.PREDICTED_WATER_TREEING === 1) {
    return { action: 'Cable replacement assessment', days: 14, source: 'Water Treeing Model' }
  }

  if (ml.ignition?.RISK_LEVEL === 'HIGH') {
    return { action: 'Fire mitigation inspection', days: 7, source: 'Ignition Risk Model' }
  }

  if (ml.vegetation?.PREDICTED_DAYS_TO_CONTACT && ml.vegetation.PREDICTED_DAYS_TO_CONTACT < 60) {
    return { 
      action: 'Vegetation trimming', 
      days: Math.max(1, Math.floor(ml.vegetation.PREDICTED_DAYS_TO_CONTACT * 0.75)),
      source: 'Vegetation Growth Model'
    }
  }

  if (ml.health?.PREDICTED_CONDITION === 'CRITICAL') {
    return { action: 'Emergency inspection', days: 3, source: 'Health Prediction Model' }
  }

  if (ml.combined?.MAINTENANCE_PRIORITY === 'EMERGENCY') {
    return { action: 'Priority maintenance', days: 5, source: 'Combined Risk Model' }
  }

  if (ml.combined?.MAINTENANCE_PRIORITY === 'HIGH') {
    return { action: 'Scheduled maintenance', days: 21, source: 'Combined Risk Model' }
  }

  return { action: 'Routine inspection', days: 90, source: 'Standard Schedule' }
}

function FitBounds({ features }: { features: MapFeature[] }) {
  const map = useMap()
  
  useEffect(() => {
    if (features.length > 0) {
      const bounds = features.slice(0, 100).map(f => [
        f.geometry.coordinates[1], 
        f.geometry.coordinates[0]
      ] as [number, number])
      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 10 })
      }
    }
  }, [features, map])
  
  return null
}

export function AssetMap() {
  const [selectedRegion, setSelectedRegion] = useState('All')
  const [selectedRiskTier, setSelectedRiskTier] = useState('All')
  const [selectedAsset, setSelectedAsset] = useState<EnrichedAsset | null>(null)

  const { data: mapData, isLoading } = useQuery<MapData>({
    queryKey: ['mapData'],
    queryFn: getMapData,
    refetchInterval: 60000,
  })

  const assetIds = useMemo(() => {
    return mapData?.features?.map(f => f.properties.asset_id) || []
  }, [mapData])

  const { data: mlData, isLoading: mlLoading } = useQuery({
    queryKey: ['assetMLPredictions', assetIds.slice(0, 500)],
    queryFn: () => getAssetMLPredictions(assetIds.slice(0, 500)),
    enabled: assetIds.length > 0,
    staleTime: 5 * 60 * 1000,
  })

  const enrichedFeatures: EnrichedAsset[] = useMemo(() => {
    if (!mapData?.features) return []
    
    return mapData.features.map(f => ({
      ...f,
      mlPrediction: mlData?.predictions?.[f.properties.asset_id] as MLPrediction | undefined
    }))
  }, [mapData, mlData])

  const filteredFeatures = enrichedFeatures.filter(f => {
    if (selectedRegion !== 'All' && f.properties.region !== selectedRegion) return false
    if (selectedRiskTier !== 'All' && f.properties.risk_tier !== selectedRiskTier) return false
    return true
  })

  const displayFeatures = filteredFeatures.slice(0, 500)

  const riskCounts = {
    CRITICAL: enrichedFeatures.filter(f => f.properties.risk_tier === 'CRITICAL').length,
    HIGH: enrichedFeatures.filter(f => f.properties.risk_tier === 'HIGH').length,
    MEDIUM: enrichedFeatures.filter(f => f.properties.risk_tier === 'MEDIUM').length,
    LOW: enrichedFeatures.filter(f => f.properties.risk_tier === 'LOW').length,
  }

  const mlCoverage = mlData?.coverage || { health: 0, vegetation: 0, ignition: 0, cable: 0 }

  const totalAssets = enrichedFeatures.length
  const criticalCount = riskCounts.CRITICAL

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-12 h-12 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="h-full flex" style={{ minHeight: 'calc(100vh - 120px)' }}>
      <div className="flex-1 relative" style={{ minHeight: '500px' }}>
        <div className="absolute top-4 left-4 right-80 flex gap-4 z-[1000] flex-wrap">
          <div className="bg-gray-800/95 backdrop-blur-sm rounded-lg p-3 flex items-center gap-3 border border-gray-700">
            <Zap size={20} className="text-purple-500" />
            <div>
              <div className="text-lg font-bold text-white">{totalAssets.toLocaleString()}</div>
              <div className="text-xs text-slate-500">Assets</div>
            </div>
          </div>
          <div className="bg-gray-800/95 backdrop-blur-sm rounded-lg p-3 flex items-center gap-3 border border-gray-700">
            <AlertTriangle size={20} className="text-red-500" />
            <div>
              <div className="text-lg font-bold text-white">{criticalCount}</div>
              <div className="text-xs text-slate-500">Critical</div>
            </div>
          </div>
          <div className="bg-gray-800/95 backdrop-blur-sm rounded-lg p-3 flex items-center gap-3 border border-purple-500/50">
            <Brain size={20} className="text-purple-400" />
            <div>
              <div className="text-lg font-bold text-purple-400">{mlCoverage.health}</div>
              <div className="text-xs text-purple-400/70">ML Predictions</div>
            </div>
            {mlLoading && <Loader2 size={14} className="text-purple-400 animate-spin" />}
          </div>
          <div className="bg-gray-800/95 backdrop-blur-sm rounded-lg p-3 flex items-center gap-2 border border-gray-700">
            <Filter size={16} className="text-slate-400" />
            <select 
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="bg-transparent text-white text-sm border-none outline-none cursor-pointer"
            >
              <option value="All" className="bg-gray-800">All Regions</option>
              {REGIONS.map(r => (
                <option key={r} value={r} className="bg-gray-800">{r}</option>
              ))}
            </select>
          </div>
          <div className="bg-gray-800/95 backdrop-blur-sm rounded-lg p-3 flex items-center gap-2 border border-gray-700">
            <select 
              value={selectedRiskTier}
              onChange={(e) => setSelectedRiskTier(e.target.value)}
              className="bg-transparent text-white text-sm border-none outline-none cursor-pointer"
            >
              <option value="All" className="bg-gray-800">All Risk</option>
              <option value="CRITICAL" className="bg-gray-800">Critical</option>
              <option value="HIGH" className="bg-gray-800">High</option>
              <option value="MEDIUM" className="bg-gray-800">Medium</option>
              <option value="LOW" className="bg-gray-800">Low</option>
            </select>
          </div>
        </div>

        <MapContainer
          center={[37.5, -119.5]}
          zoom={6}
          className="absolute inset-0"
          style={{ background: '#0d1117', height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            subdomains="abcd"
            maxZoom={19}
          />
          <FitBounds features={displayFeatures} />
          
          {displayFeatures.map((asset) => {
            const insight = generateRealAIInsight(asset.mlPrediction, asset.properties)
            const nextAction = generateNextAction(asset.mlPrediction, asset.properties)
            const hasWaterTreeing = asset.mlPrediction?.cable?.PREDICTED_WATER_TREEING === 1
            const hasHighIgnition = asset.mlPrediction?.ignition?.RISK_LEVEL === 'HIGH'
            
            return (
              <CircleMarker
                key={asset.properties.asset_id}
                center={[asset.geometry.coordinates[1], asset.geometry.coordinates[0]]}
                radius={asset.properties.risk_tier === 'CRITICAL' ? 10 : 
                        asset.properties.risk_tier === 'HIGH' ? 8 : 6}
                pathOptions={{
                  color: hasWaterTreeing ? '#3b82f6' : 
                         hasHighIgnition ? '#f97316' :
                         RISK_TIER_COLORS[asset.properties.risk_tier] || '#6b7280',
                  fillColor: hasWaterTreeing ? '#3b82f6' :
                             hasHighIgnition ? '#f97316' :
                             RISK_TIER_COLORS[asset.properties.risk_tier] || '#6b7280',
                  fillOpacity: 0.7,
                  weight: selectedAsset?.properties.asset_id === asset.properties.asset_id ? 3 : 1
                }}
                eventHandlers={{
                  click: () => setSelectedAsset(asset)
                }}
              >
                <Popup className="vigil-popup" minWidth={360} maxWidth={400}>
                  <div className="bg-gray-900 text-white rounded-lg overflow-hidden" style={{ margin: '-14px -20px' }}>
                    <div className="px-4 py-3 border-b border-gray-700/50 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-2.5 h-2.5 rounded-full animate-pulse"
                          style={{ backgroundColor: hasWaterTreeing ? '#3b82f6' : hasHighIgnition ? '#f97316' : RISK_TIER_COLORS[asset.properties.risk_tier] }}
                        />
                        <span className="font-semibold text-white truncate max-w-[180px]">
                          {asset.properties.asset_id}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {hasWaterTreeing && (
                          <span className="text-xs font-medium px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 flex items-center gap-1">
                            <Droplets size={10} />
                            WATER TREE
                          </span>
                        )}
                        <span 
                          className="text-xs font-medium px-2 py-0.5 rounded uppercase"
                          style={{ 
                            backgroundColor: `${RISK_TIER_COLORS[asset.properties.risk_tier]}20`,
                            color: RISK_TIER_COLORS[asset.properties.risk_tier]
                          }}
                        >
                          {asset.properties.risk_tier}
                        </span>
                      </div>
                    </div>

                    <div className="px-4 py-2 border-b border-gray-700/30 flex items-center justify-between text-sm">
                      <span className="text-slate-400">{asset.properties.asset_type}</span>
                      <span className="font-medium text-purple-400">{asset.properties.region}</span>
                    </div>

                    <div className="px-4 py-3 grid grid-cols-2 gap-3 border-b border-gray-700/30">
                      <div className="flex items-center justify-between bg-gray-800/50 rounded px-2.5 py-1.5">
                        <span className="text-xs text-slate-500">Condition</span>
                        <div className="flex items-center gap-1">
                          <span className={`font-bold ${
                            asset.properties.condition_score >= 0.7 ? 'text-green-500' :
                            asset.properties.condition_score >= 0.4 ? 'text-yellow-500' :
                            'text-red-500'
                          }`}>
                            {(asset.properties.condition_score * 100).toFixed(0)}%
                          </span>
                          {asset.mlPrediction?.health?.HEALTH_DELTA !== undefined && (
                            asset.mlPrediction.health.HEALTH_DELTA > 0 
                              ? <TrendingUp size={12} className="text-green-500" />
                              : asset.mlPrediction.health.HEALTH_DELTA < 0 
                                ? <TrendingDown size={12} className="text-red-500" />
                                : <Minus size={12} className="text-slate-500" />
                          )}
                        </div>
                      </div>
                      <div className="flex items-center justify-between bg-gray-800/50 rounded px-2.5 py-1.5">
                        <span className="text-xs text-slate-500">Fire Zone</span>
                        <span className="font-bold text-orange-400">{asset.properties.fire_district}</span>
                      </div>
                    </div>

                    {asset.mlPrediction?.combined && (
                      <div className="px-4 py-2 border-b border-gray-700/30 grid grid-cols-4 gap-2">
                        <div className="text-center">
                          <Activity size={14} className="mx-auto text-green-400 mb-1" />
                          <div className="text-xs text-slate-500">Health</div>
                          <div className={`text-xs font-bold ${
                            asset.mlPrediction.combined.HEALTH_STATUS === 'CRITICAL' ? 'text-red-400' :
                            asset.mlPrediction.combined.HEALTH_STATUS === 'POOR' ? 'text-orange-400' :
                            'text-green-400'
                          }`}>
                            {asset.mlPrediction.combined.HEALTH_STATUS || 'N/A'}
                          </div>
                        </div>
                        <div className="text-center">
                          <Flame size={14} className="mx-auto text-orange-400 mb-1" />
                          <div className="text-xs text-slate-500">Ignition</div>
                          <div className={`text-xs font-bold ${
                            asset.mlPrediction.combined.IGNITION_RISK_LEVEL === 'HIGH' ? 'text-red-400' :
                            asset.mlPrediction.combined.IGNITION_RISK_LEVEL === 'MEDIUM' ? 'text-yellow-400' :
                            'text-green-400'
                          }`}>
                            {asset.mlPrediction.combined.IGNITION_RISK_LEVEL || 'N/A'}
                          </div>
                        </div>
                        <div className="text-center">
                          <Droplets size={14} className="mx-auto text-blue-400 mb-1" />
                          <div className="text-xs text-slate-500">Water Tree</div>
                          <div className={`text-xs font-bold ${
                            asset.mlPrediction.combined.WATER_TREEING_RISK === 'HIGH' ? 'text-blue-400' : 'text-slate-400'
                          }`}>
                            {asset.mlPrediction.combined.WATER_TREEING_RISK || 'N/A'}
                          </div>
                        </div>
                        <div className="text-center">
                          <TreePine size={14} className="mx-auto text-green-500 mb-1" />
                          <div className="text-xs text-slate-500">Veg Days</div>
                          <div className={`text-xs font-bold ${
                            (asset.mlPrediction.vegetation?.PREDICTED_DAYS_TO_CONTACT || 999) < 30 ? 'text-red-400' :
                            (asset.mlPrediction.vegetation?.PREDICTED_DAYS_TO_CONTACT || 999) < 60 ? 'text-yellow-400' :
                            'text-green-400'
                          }`}>
                            {asset.mlPrediction.vegetation?.PREDICTED_DAYS_TO_CONTACT || '—'}
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="px-4 py-3 border-b border-gray-700/30 bg-gradient-to-r from-purple-900/30 to-transparent">
                      <div className="flex items-start gap-2">
                        <Brain size={14} className="text-purple-500 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-purple-400 font-medium">VIGIL AI Insight</span>
                            {insight.confidence > 0 && (
                              <span className="text-xs text-purple-400/70">
                                {(insight.confidence * 100).toFixed(0)}% conf
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed">
                            {mlLoading ? (
                              <span className="flex items-center gap-2">
                                <Loader2 size={12} className="animate-spin" />
                                Loading ML predictions...
                              </span>
                            ) : insight.text}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="px-4 py-2 border-b border-gray-700/30 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Target size={14} className="text-purple-400" />
                        <span className="text-xs text-slate-400">Next:</span>
                        <span className="text-xs text-white font-medium">{nextAction.action}</span>
                      </div>
                      <div className="flex items-center gap-1 text-xs">
                        <Clock size={12} className="text-slate-500" />
                        <span className={`font-medium ${nextAction.days <= 7 ? 'text-red-400' : nextAction.days <= 21 ? 'text-yellow-400' : 'text-green-400'}`}>
                          {nextAction.days}d
                        </span>
                      </div>
                    </div>

                    <div className="px-4 py-2 text-xs text-slate-500 border-b border-gray-700/30">
                      Source: {nextAction.source}
                    </div>

                    <div className="px-4 py-3">
                      <button
                        onClick={(e) => e.stopPropagation()}
                        className="w-full py-2 bg-gradient-to-r from-purple-600 to-purple-500 rounded-lg text-white text-sm font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
                      >
                        Create Work Order
                        <ExternalLink size={14} />
                      </button>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>

        <div className="absolute bottom-4 left-4 bg-gray-800/95 backdrop-blur-sm rounded-lg p-4 z-[1000] border border-gray-700">
          <h4 className="text-xs font-semibold text-slate-400 mb-3">Risk Level</h4>
          <div className="space-y-2">
            {Object.entries(RISK_TIER_COLORS).map(([level, color]) => (
              <div key={level} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: color }} />
                <span className="text-xs text-slate-300">{level}</span>
                <span className="text-xs text-slate-500">
                  ({riskCounts[level as keyof typeof riskCounts] || 0})
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-gray-700">
            <h4 className="text-xs font-semibold text-purple-400 mb-2">ML Overlays</h4>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <span className="text-xs text-slate-300">Water Treeing</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-orange-500" />
                <span className="text-xs text-slate-300">High Ignition</span>
              </div>
            </div>
          </div>
        </div>

        {filteredFeatures.length > 500 && (
          <div className="absolute top-4 right-4 bg-yellow-500/20 border border-yellow-500/50 rounded-lg px-3 py-2 z-[1000]">
            <span className="text-xs text-yellow-400">
              Showing 500 of {filteredFeatures.length.toLocaleString()} assets
            </span>
          </div>
        )}
      </div>

      <div className="w-80 border-l border-gray-700/50 bg-gray-900/50 overflow-y-auto">
        {selectedAsset ? (
          <div className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="font-semibold text-white text-lg">{selectedAsset.properties.asset_id}</h2>
                <p className="text-sm text-slate-500">{selectedAsset.properties.asset_type}</p>
              </div>
              <span 
                className="px-2 py-1 rounded text-xs font-medium"
                style={{ 
                  backgroundColor: `${RISK_TIER_COLORS[selectedAsset.properties.risk_tier]}20`,
                  color: RISK_TIER_COLORS[selectedAsset.properties.risk_tier]
                }}
              >
                {selectedAsset.properties.risk_tier}
              </span>
            </div>

            <div className="space-y-4">
              <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700">
                <div className="text-xs text-slate-500 mb-1">Region</div>
                <div className="font-medium text-white">{selectedAsset.properties.region}</div>
              </div>

              {selectedAsset.mlPrediction?.combined && (
                <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Brain size={16} className="text-purple-400" />
                    <span className="text-sm font-medium text-purple-400">ML Risk Score</span>
                  </div>
                  <div className="text-3xl font-bold text-white mb-2">
                    {((selectedAsset.mlPrediction.combined.COMPOSITE_ML_RISK_SCORE || 0) * 100).toFixed(0)}%
                  </div>
                  <div className={`text-sm font-medium ${
                    selectedAsset.mlPrediction.combined.MAINTENANCE_PRIORITY === 'EMERGENCY' ? 'text-red-400' :
                    selectedAsset.mlPrediction.combined.MAINTENANCE_PRIORITY === 'HIGH' ? 'text-orange-400' :
                    'text-green-400'
                  }`}>
                    {selectedAsset.mlPrediction.combined.MAINTENANCE_PRIORITY} Priority
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700 text-center">
                  <div className="text-xs text-slate-500 mb-1">Fire District</div>
                  <div className="text-lg font-bold text-orange-400">
                    {selectedAsset.properties.fire_district}
                  </div>
                </div>
                <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700 text-center">
                  <div className="text-xs text-slate-500 mb-1">ML Coverage</div>
                  <div className="text-lg font-bold text-purple-400">
                    {selectedAsset.mlPrediction ? '4 Models' : 'None'}
                  </div>
                </div>
              </div>

              {selectedAsset.mlPrediction?.cable?.PREDICTED_WATER_TREEING === 1 && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Droplets size={14} className="text-blue-400" />
                    <span className="text-xs font-medium text-blue-400">WATER TREEING DETECTED</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-slate-500">Correlation:</span>
                      <span className="text-blue-300 ml-1 font-medium">
                        {((selectedAsset.mlPrediction.cable.RAIN_VOLTAGE_CORRELATION || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Voltage Dips:</span>
                      <span className="text-blue-300 ml-1 font-medium">
                        {selectedAsset.mlPrediction.cable.RAIN_CORRELATED_DIPS}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Zap size={14} className="text-purple-400" />
                  <span className="text-xs font-medium text-purple-400">VIGIL AI Insight</span>
                </div>
                <p className="text-sm text-slate-300">
                  {mlLoading ? 'Loading...' : generateRealAIInsight(selectedAsset.mlPrediction, selectedAsset.properties).text}
                </p>
              </div>

              <button className="w-full py-3 bg-purple-600 hover:bg-purple-700 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2">
                <ExternalLink size={16} />
                Create Work Order
              </button>
              
              <button 
                onClick={() => setSelectedAsset(null)}
                className="w-full py-2 text-sm text-slate-400 hover:text-white transition-colors"
              >
                ← Back to List
              </button>
            </div>
          </div>
        ) : (
          <div className="p-6">
            <div className="text-center py-8">
              <Brain size={48} className="mx-auto text-purple-500/50 mb-4" />
              <h3 className="font-medium text-slate-300 mb-2">ML-Powered Asset Map</h3>
              <p className="text-sm text-slate-500">
                Click on a marker to view real ML predictions
              </p>
            </div>

            <div className="space-y-2 mt-4">
              <h4 className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-3">
                ML-Flagged Critical Assets
              </h4>
              {enrichedFeatures
                .filter(f => f.mlPrediction?.combined?.MAINTENANCE_PRIORITY === 'EMERGENCY' || 
                             f.mlPrediction?.cable?.PREDICTED_WATER_TREEING === 1 ||
                             f.properties.risk_tier === 'CRITICAL')
                .slice(0, 10)
                .map((asset) => {
                  const hasWaterTreeing = asset.mlPrediction?.cable?.PREDICTED_WATER_TREEING === 1
                  return (
                    <div
                      key={asset.properties.asset_id}
                      onClick={() => setSelectedAsset(asset)}
                      className="bg-gray-800/50 hover:bg-gray-700/50 rounded-lg p-3 cursor-pointer transition-colors border border-gray-700/50"
                    >
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-3 h-3 rounded-full flex-shrink-0 animate-pulse"
                          style={{ background: hasWaterTreeing ? '#3b82f6' : RISK_TIER_COLORS[asset.properties.risk_tier] }}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-white truncate flex items-center gap-2">
                            {asset.properties.asset_id}
                            {hasWaterTreeing && <Droplets size={12} className="text-blue-400" />}
                          </div>
                          <div className="text-xs text-slate-500">
                            {asset.properties.asset_type} • {asset.properties.region}
                          </div>
                        </div>
                        <div className="text-sm text-slate-400">
                          {asset.mlPrediction?.combined 
                            ? `${((asset.mlPrediction.combined.COMPOSITE_ML_RISK_SCORE || 0) * 100).toFixed(0)}%`
                            : `${(asset.properties.condition_score * 100).toFixed(0)}%`
                          }
                        </div>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
