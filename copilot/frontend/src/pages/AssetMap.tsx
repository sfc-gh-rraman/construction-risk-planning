import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import { useQuery } from '@tanstack/react-query'
import { 
  Zap, 
  AlertTriangle, 
  ArrowLeft, 
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  Bell,
  Clock,
  Filter,
  TreePine,
  Thermometer
} from 'lucide-react'
import { getMapData } from '../services/api'
import type { MapData, MapFeature } from '../types'
import { REGIONS, RISK_TIER_COLORS } from '../types'
import 'leaflet/dist/leaflet.css'

interface EnrichedAsset extends MapFeature {
  aiInsight: string
  nextAction: string
  daysToAction: number
  conditionTrend: 'up' | 'down' | 'stable'
  alertCount: number
}

const generateAIInsight = (asset: MapFeature['properties']): string => {
  if (asset.risk_tier === 'CRITICAL') {
    const insights = [
      `⚠️ Water treeing detected - ${Math.floor(Math.random() * 15 + 10)}% degradation`,
      `🔴 Fire risk elevated - ${asset.fire_district} zone`,
      `⚠️ Condition declining rapidly - recommend replacement`
    ]
    return insights[Math.floor(Math.random() * insights.length)]
  } else if (asset.risk_tier === 'HIGH') {
    const insights = [
      `📊 Vegetation encroachment detected nearby`,
      `⚡ Partial discharge activity increasing`,
      `🔍 Inspection recommended within 30 days`
    ]
    return insights[Math.floor(Math.random() * insights.length)]
  } else {
    const insights = [
      `✅ Operating within normal parameters`,
      `🌟 Good condition - routine maintenance only`,
      `✅ No anomalies detected`
    ]
    return insights[Math.floor(Math.random() * insights.length)]
  }
}

const generateNextAction = (asset: MapFeature['properties']): { action: string; days: number } => {
  const actions: Record<string, string[]> = {
    CRITICAL: ['Emergency Inspection', 'Replace Asset', 'De-energize for Safety'],
    HIGH: ['Priority Inspection', 'Schedule Maintenance', 'Vegetation Clearing'],
    MEDIUM: ['Routine Inspection', 'Monitor Condition', 'Schedule Review'],
    LOW: ['Annual Inspection', 'Standard Maintenance', 'Update Records']
  }
  const tierActions = actions[asset.risk_tier] || actions.LOW
  const action = tierActions[Math.floor(Math.random() * tierActions.length)]
  const days = asset.risk_tier === 'CRITICAL' ? Math.floor(Math.random() * 7 + 1) :
               asset.risk_tier === 'HIGH' ? Math.floor(Math.random() * 21 + 7) :
               Math.floor(Math.random() * 60 + 30)
  return { action, days }
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

  const [enrichedFeatures, setEnrichedFeatures] = useState<EnrichedAsset[]>([])

  useEffect(() => {
    if (mapData?.features) {
      const enriched = mapData.features.map(f => {
        const nextAction = generateNextAction(f.properties)
        return {
          ...f,
          aiInsight: generateAIInsight(f.properties),
          nextAction: nextAction.action,
          daysToAction: nextAction.days,
          conditionTrend: f.properties.condition_score >= 0.7 ? 'up' as const : 
                          f.properties.condition_score >= 0.4 ? 'stable' as const : 'down' as const,
          alertCount: f.properties.risk_tier === 'CRITICAL' ? Math.floor(Math.random() * 3 + 1) :
                      f.properties.risk_tier === 'HIGH' ? Math.floor(Math.random() * 2) : 0
        }
      })
      setEnrichedFeatures(enriched)
    }
  }, [mapData])

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
        <div className="absolute top-4 left-4 right-80 flex gap-4 z-[1000]">
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
          
          {displayFeatures.map((asset) => (
            <CircleMarker
              key={asset.properties.asset_id}
              center={[asset.geometry.coordinates[1], asset.geometry.coordinates[0]]}
              radius={asset.properties.risk_tier === 'CRITICAL' ? 10 : 
                      asset.properties.risk_tier === 'HIGH' ? 8 : 6}
              pathOptions={{
                color: RISK_TIER_COLORS[asset.properties.risk_tier] || '#6b7280',
                fillColor: RISK_TIER_COLORS[asset.properties.risk_tier] || '#6b7280',
                fillOpacity: 0.7,
                weight: selectedAsset?.properties.asset_id === asset.properties.asset_id ? 3 : 1
              }}
              eventHandlers={{
                click: () => setSelectedAsset(asset)
              }}
            >
              <Popup className="vigil-popup" minWidth={320} maxWidth={360}>
                <div className="bg-gray-900 text-white rounded-lg overflow-hidden" style={{ margin: '-14px -20px' }}>
                  <div className="px-4 py-3 border-b border-gray-700/50 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-2.5 h-2.5 rounded-full animate-pulse"
                        style={{ backgroundColor: RISK_TIER_COLORS[asset.properties.risk_tier] }}
                      />
                      <span className="font-semibold text-white truncate max-w-[180px]">
                        {asset.properties.asset_id}
                      </span>
                    </div>
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
                        {asset.conditionTrend === 'up' && <TrendingUp size={12} className="text-green-500" />}
                        {asset.conditionTrend === 'down' && <TrendingDown size={12} className="text-red-500" />}
                        {asset.conditionTrend === 'stable' && <Minus size={12} className="text-slate-500" />}
                      </div>
                    </div>
                    <div className="flex items-center justify-between bg-gray-800/50 rounded px-2.5 py-1.5">
                      <span className="text-xs text-slate-500">Fire Zone</span>
                      <span className="font-bold text-orange-400">{asset.properties.fire_district}</span>
                    </div>
                  </div>

                  <div className="px-4 py-2 border-b border-gray-700/30">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-500">Condition</span>
                      <span className="text-xs font-medium text-white">{(asset.properties.condition_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full rounded-full transition-all"
                        style={{ 
                          width: `${asset.properties.condition_score * 100}%`,
                          background: `linear-gradient(90deg, ${RISK_TIER_COLORS[asset.properties.risk_tier]}, #a855f7)`
                        }}
                      />
                    </div>
                  </div>

                  <div className="px-4 py-2.5 border-b border-gray-700/30 bg-gray-800/30">
                    <div className="flex items-start gap-2">
                      <Zap size={14} className="text-purple-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="text-xs text-purple-400 font-medium">VIGIL AI</span>
                        <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">
                          {asset.aiInsight}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="px-4 py-2 border-b border-gray-700/30 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Target size={14} className="text-purple-400" />
                      <span className="text-xs text-slate-400">Next:</span>
                      <span className="text-xs text-white font-medium">{asset.nextAction}</span>
                    </div>
                    <div className="flex items-center gap-1 text-xs">
                      <Clock size={12} className="text-slate-500" />
                      <span className="text-yellow-400 font-medium">{asset.daysToAction}d</span>
                    </div>
                  </div>

                  <div className="px-4 py-2 flex items-center gap-3 text-xs border-b border-gray-700/30">
                    <div className="flex items-center gap-1.5">
                      <TreePine size={12} className="text-green-500" />
                      <span className="text-slate-400">Veg. Clear</span>
                    </div>
                    {asset.alertCount > 0 && (
                      <div className="flex items-center gap-1.5">
                        <Bell size={12} className="text-yellow-400" />
                        <span className="text-yellow-400">{asset.alertCount} Alert{asset.alertCount !== 1 ? 's' : ''}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1.5 ml-auto">
                      <Thermometer size={12} className="text-slate-500" />
                      <span className="text-slate-400">{asset.properties.fire_district}</span>
                    </div>
                  </div>

                  <div className="px-4 py-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                      }}
                      className="w-full py-2 bg-gradient-to-r from-purple-600 to-purple-500 rounded-lg text-white text-sm font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
                    >
                      Create Work Order
                      <ExternalLink size={14} />
                    </button>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          ))}
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

              <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700">
                <div className="text-xs text-slate-500 mb-1">Condition Score</div>
                <div className="text-2xl font-bold text-white">
                  {(selectedAsset.properties.condition_score * 100).toFixed(0)}%
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700 text-center">
                  <div className="text-xs text-slate-500 mb-1">Fire District</div>
                  <div className="text-lg font-bold text-orange-400">
                    {selectedAsset.properties.fire_district}
                  </div>
                </div>
                <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700 text-center">
                  <div className="text-xs text-slate-500 mb-1">Alerts</div>
                  <div className={`text-lg font-bold ${selectedAsset.alertCount > 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {selectedAsset.alertCount}
                  </div>
                </div>
              </div>

              <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Zap size={14} className="text-purple-400" />
                  <span className="text-xs font-medium text-purple-400">VIGIL AI Insight</span>
                </div>
                <p className="text-sm text-slate-300">{selectedAsset.aiInsight}</p>
              </div>

              <button className="w-full py-3 bg-purple-600 hover:bg-purple-700 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2">
                <ExternalLink size={16} />
                Create Work Order
              </button>
              
              <button 
                onClick={() => setSelectedAsset(null)}
                className="w-full py-2 text-sm text-slate-400 hover:text-white flex items-center justify-center gap-2 transition-colors"
              >
                <ArrowLeft size={14} />
                Back to List
              </button>
            </div>
          </div>
        ) : (
          <div className="p-6">
            <div className="text-center py-8">
              <Zap size={48} className="mx-auto text-slate-600 mb-4" />
              <h3 className="font-medium text-slate-300 mb-2">Select an Asset</h3>
              <p className="text-sm text-slate-500">
                Click on a marker to view asset details
              </p>
            </div>

            <div className="space-y-2 mt-4">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Critical Assets
              </h4>
              {enrichedFeatures
                .filter(f => f.properties.risk_tier === 'CRITICAL')
                .slice(0, 10)
                .map((asset) => (
                <div
                  key={asset.properties.asset_id}
                  onClick={() => setSelectedAsset(asset)}
                  className="bg-gray-800/50 hover:bg-gray-700/50 rounded-lg p-3 cursor-pointer transition-colors border border-gray-700/50"
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-3 h-3 rounded-full flex-shrink-0 animate-pulse"
                      style={{ background: RISK_TIER_COLORS[asset.properties.risk_tier] }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-white truncate">
                        {asset.properties.asset_id}
                      </div>
                      <div className="text-xs text-slate-500">
                        {asset.properties.asset_type} • {asset.properties.region}
                      </div>
                    </div>
                    <div className="text-sm text-slate-400">
                      {(asset.properties.condition_score * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
