import { useState, useMemo, useCallback } from 'react'
import { Map } from 'react-map-gl/maplibre'
import DeckGL from '@deck.gl/react'
import { HexagonLayer } from '@deck.gl/aggregation-layers'
import { ScatterplotLayer, TextLayer } from '@deck.gl/layers'
import { MapFeature, RISK_TIER_COLORS } from '../types'
import { Flame, Mountain, Activity, Layers, Eye, EyeOff } from 'lucide-react'
import 'maplibre-gl/dist/maplibre-gl.css'

interface RiskMap3DProps {
  features: MapFeature[]
  selectedRegion?: string
  onAssetClick?: (asset: MapFeature['properties']) => void
}

const INITIAL_VIEW_STATE = {
  longitude: -119.5,
  latitude: 37.5,
  zoom: 5.5,
  pitch: 45,
  bearing: -10,
}

const REGION_VIEWS: Record<string, { longitude: number; latitude: number; zoom: number }> = {
  NorCal: { longitude: -121.5, latitude: 38.5, zoom: 7 },
  SoCal: { longitude: -117.5, latitude: 34.0, zoom: 7 },
  PNW: { longitude: -122.5, latitude: 45.5, zoom: 7 },
  Southwest: { longitude: -111.5, latitude: 33.5, zoom: 7 },
  Mountain: { longitude: -105.5, latitude: 39.5, zoom: 7 },
}

function getRiskWeight(tier: string): number {
  switch (tier) {
    case 'CRITICAL': return 4
    case 'HIGH': return 3
    case 'MEDIUM': return 2
    case 'LOW': return 1
    default: return 1
  }
}

function getColorForWeight(weight: number): [number, number, number, number] {
  if (weight >= 3.5) return [239, 68, 68, 220]
  if (weight >= 2.5) return [249, 115, 22, 200]
  if (weight >= 1.5) return [234, 179, 8, 180]
  return [34, 197, 94, 160]
}

export function RiskMap3D({ features, selectedRegion, onAssetClick }: RiskMap3DProps) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const [show3DHexbins, setShow3DHexbins] = useState(true)
  const [showAssets, setShowAssets] = useState(true)
  const [hoveredAsset, setHoveredAsset] = useState<MapFeature['properties'] | null>(null)

  const filteredFeatures = useMemo(() => {
    if (!selectedRegion || selectedRegion === 'All') return features
    return features.filter(f => f.properties.region === selectedRegion)
  }, [features, selectedRegion])

  const handleRegionChange = useCallback((region: string | undefined) => {
    if (region && region !== 'All' && REGION_VIEWS[region]) {
      setViewState(prev => ({
        ...prev,
        ...REGION_VIEWS[region],
        pitch: 45,
        bearing: -10
      }))
    } else {
      setViewState(INITIAL_VIEW_STATE)
    }
  }, [])

  useMemo(() => {
    handleRegionChange(selectedRegion)
  }, [selectedRegion, handleRegionChange])

  const hexagonData = useMemo(() => 
    filteredFeatures.map(f => ({
      position: f.geometry.coordinates,
      weight: getRiskWeight(f.properties.risk_tier),
      properties: f.properties
    })), 
    [filteredFeatures]
  )

  const criticalAssets = useMemo(() =>
    filteredFeatures.filter(f => f.properties.risk_tier === 'CRITICAL'),
    [filteredFeatures]
  )

  const layers = useMemo(() => {
    const result = []

    if (show3DHexbins && hexagonData.length > 0) {
      result.push(
        new HexagonLayer({
          id: 'hexagon-layer',
          data: hexagonData,
          getPosition: (d: { position: [number, number] }) => d.position,
          getElevationWeight: (d: { weight: number }) => d.weight,
          getColorWeight: (d: { weight: number }) => d.weight,
          elevationScale: 3000,
          extruded: true,
          radius: 15000,
          coverage: 0.9,
          elevationRange: [0, 25000],
          colorRange: [
            [34, 197, 94],
            [234, 179, 8],
            [249, 115, 22],
            [239, 68, 68],
            [220, 38, 38],
            [185, 28, 28]
          ],
          opacity: 0.7,
          pickable: true,
          material: {
            ambient: 0.4,
            diffuse: 0.6,
            shininess: 32,
            specularColor: [60, 64, 70]
          }
        })
      )
    }

    if (showAssets) {
      result.push(
        new ScatterplotLayer({
          id: 'assets-layer',
          data: filteredFeatures.slice(0, 2000),
          getPosition: (d: MapFeature) => d.geometry.coordinates,
          getFillColor: (d: MapFeature) => {
            const color = RISK_TIER_COLORS[d.properties.risk_tier]
            const hex = color.replace('#', '')
            const r = parseInt(hex.substring(0, 2), 16)
            const g = parseInt(hex.substring(2, 4), 16)
            const b = parseInt(hex.substring(4, 6), 16)
            return [r, g, b, 200]
          },
          getRadius: (d: MapFeature) => {
            switch (d.properties.risk_tier) {
              case 'CRITICAL': return 800
              case 'HIGH': return 600
              case 'MEDIUM': return 400
              default: return 300
            }
          },
          radiusMinPixels: 3,
          radiusMaxPixels: 15,
          pickable: true,
          onClick: ({ object }: { object?: MapFeature }) => {
            if (object && onAssetClick) {
              onAssetClick(object.properties)
            }
          },
          onHover: ({ object }: { object?: MapFeature }) => {
            setHoveredAsset(object?.properties || null)
          },
          stroked: true,
          lineWidthMinPixels: 1,
          getLineColor: [255, 255, 255, 100]
        })
      )

      result.push(
        new ScatterplotLayer({
          id: 'critical-pulse-layer',
          data: criticalAssets,
          getPosition: (d: MapFeature) => d.geometry.coordinates,
          getFillColor: [239, 68, 68, 100],
          getRadius: 1500,
          radiusMinPixels: 8,
          radiusMaxPixels: 25,
          pickable: false
        })
      )
    }

    return result
  }, [show3DHexbins, showAssets, hexagonData, filteredFeatures, criticalAssets, onAssetClick])

  const riskCounts = useMemo(() => ({
    CRITICAL: filteredFeatures.filter(f => f.properties.risk_tier === 'CRITICAL').length,
    HIGH: filteredFeatures.filter(f => f.properties.risk_tier === 'HIGH').length,
    MEDIUM: filteredFeatures.filter(f => f.properties.risk_tier === 'MEDIUM').length,
    LOW: filteredFeatures.filter(f => f.properties.risk_tier === 'LOW').length,
  }), [filteredFeatures])

  return (
    <div className="relative w-full h-full">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: vs }) => setViewState(vs as typeof viewState)}
        controller={true}
        layers={layers}
        getTooltip={({ object }) => object?.properties ? {
          html: `
            <div style="background: #1f2937; padding: 12px; border-radius: 8px; border: 1px solid #374151; min-width: 200px;">
              <div style="font-weight: 600; color: white; margin-bottom: 4px;">${object.properties.asset_id}</div>
              <div style="color: #9ca3af; font-size: 12px; margin-bottom: 8px;">${object.properties.asset_type}</div>
              <div style="display: flex; gap: 8px; font-size: 11px;">
                <span style="color: ${RISK_TIER_COLORS[object.properties.risk_tier]}; font-weight: 600;">
                  ${object.properties.risk_tier}
                </span>
                <span style="color: #6b7280;">•</span>
                <span style="color: #9ca3af;">${object.properties.region}</span>
                <span style="color: #6b7280;">•</span>
                <span style="color: #f97316;">${object.properties.fire_district}</span>
              </div>
              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #374151; font-size: 11px; color: #6b7280;">
                Condition: ${(object.properties.condition_score * 100).toFixed(0)}%
              </div>
            </div>
          `,
          style: { background: 'transparent', border: 'none', boxShadow: 'none' }
        } : null}
      >
        <Map
          mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
          attributionControl={false}
        />
      </DeckGL>

      <div className="absolute top-4 left-4 bg-gray-800/95 backdrop-blur-sm rounded-xl p-4 shadow-xl border border-gray-700 space-y-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Mountain size={16} className="text-purple-400" />
          3D Risk Terrain
        </div>
        <div className="space-y-2">
          <button
            onClick={() => setShow3DHexbins(!show3DHexbins)}
            className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              show3DHexbins 
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' 
                : 'bg-gray-700/50 text-gray-400 border border-gray-600/50'
            }`}
          >
            {show3DHexbins ? <Eye size={14} /> : <EyeOff size={14} />}
            3D Hexbin Heatmap
          </button>
          <button
            onClick={() => setShowAssets(!showAssets)}
            className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              showAssets 
                ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                : 'bg-gray-700/50 text-gray-400 border border-gray-600/50'
            }`}
          >
            {showAssets ? <Eye size={14} /> : <EyeOff size={14} />}
            Asset Points
          </button>
        </div>
        <div className="pt-2 border-t border-gray-700">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Activity size={12} className="text-green-500 animate-pulse" />
            <span>{filteredFeatures.length.toLocaleString()} assets</span>
          </div>
        </div>
      </div>

      <div className="absolute bottom-4 left-4 bg-gray-800/95 backdrop-blur-sm rounded-xl p-4 shadow-xl border border-gray-700">
        <h4 className="text-xs font-semibold text-gray-400 uppercase mb-3 flex items-center gap-2">
          <Layers size={12} />
          Risk Tier
        </h4>
        <div className="space-y-2">
          {Object.entries(RISK_TIER_COLORS).map(([tier, color]) => (
            <div key={tier} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}80` }}
                />
                <span className="text-gray-300 text-sm">{tier}</span>
              </div>
              <span className="text-gray-500 text-xs font-mono">
                {riskCounts[tier as keyof typeof riskCounts]?.toLocaleString() || 0}
              </span>
            </div>
          ))}
        </div>
        {show3DHexbins && (
          <div className="mt-4 pt-3 border-t border-gray-700">
            <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Elevation = Risk Density</h4>
            <div className="h-2 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 via-orange-500 to-red-600" />
            <div className="flex justify-between text-[10px] text-gray-500 mt-1">
              <span>Low</span>
              <span>High</span>
            </div>
          </div>
        )}
      </div>

      {hoveredAsset && (
        <div className="absolute top-4 right-4 bg-gray-800/95 backdrop-blur-sm rounded-xl p-4 shadow-xl border border-gray-700 w-64">
          <div className="flex items-center gap-2 mb-2">
            <div 
              className="w-3 h-3 rounded-full animate-pulse"
              style={{ backgroundColor: RISK_TIER_COLORS[hoveredAsset.risk_tier] }}
            />
            <span className="font-semibold text-white truncate">{hoveredAsset.asset_id}</span>
          </div>
          <div className="text-sm text-gray-400 mb-3">{hoveredAsset.asset_type}</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-700/50 rounded px-2 py-1">
              <span className="text-gray-500">Region</span>
              <div className="text-white">{hoveredAsset.region}</div>
            </div>
            <div className="bg-gray-700/50 rounded px-2 py-1">
              <span className="text-gray-500">Fire Zone</span>
              <div className="text-orange-400">{hoveredAsset.fire_district}</div>
            </div>
            <div className="bg-gray-700/50 rounded px-2 py-1 col-span-2">
              <span className="text-gray-500">Condition Score</span>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 h-1.5 bg-gray-600 rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full"
                    style={{ 
                      width: `${hoveredAsset.condition_score * 100}%`,
                      backgroundColor: RISK_TIER_COLORS[hoveredAsset.risk_tier]
                    }}
                  />
                </div>
                <span className="text-white">{(hoveredAsset.condition_score * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="absolute bottom-4 right-4 bg-gray-800/95 backdrop-blur-sm rounded-lg px-3 py-2 shadow-xl border border-gray-700 flex items-center gap-2">
        <Flame size={14} className="text-orange-500" />
        <span className="text-xs text-gray-400">
          <span className="text-red-400 font-bold">{riskCounts.CRITICAL}</span> critical in view
        </span>
      </div>
    </div>
  )
}
