import { useEffect, useRef, useMemo, useCallback } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { MapFeature, RISK_TIER_COLORS } from '../types'

interface RiskMap3DProps {
  features: MapFeature[]
  selectedRegion?: string
  onAssetClick?: (asset: MapFeature['properties']) => void
}

const INITIAL_VIEW = {
  center: [-119.5, 37.5] as [number, number],
  zoom: 5.5,
  pitch: 45,
  bearing: -10,
}

const REGION_CENTERS: Record<string, { center: [number, number]; zoom: number }> = {
  NorCal: { center: [-121.5, 38.5], zoom: 7 },
  SoCal: { center: [-117.5, 34.0], zoom: 7 },
  PNW: { center: [-122.5, 45.5], zoom: 7 },
  Southwest: { center: [-111.5, 33.5], zoom: 7 },
  Mountain: { center: [-105.5, 39.5], zoom: 7 },
}

export function RiskMap3D({ features, selectedRegion, onAssetClick }: RiskMap3DProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])

  const filteredFeatures = useMemo(() => {
    if (!selectedRegion || selectedRegion === 'All') return features
    return features.filter(f => f.properties.region === selectedRegion)
  }, [features, selectedRegion])

  const clearMarkers = useCallback(() => {
    markersRef.current.forEach(marker => marker.remove())
    markersRef.current = []
  }, [])

  useEffect(() => {
    if (!mapContainer.current || map.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: INITIAL_VIEW.center,
      zoom: INITIAL_VIEW.zoom,
      pitch: INITIAL_VIEW.pitch,
      bearing: INITIAL_VIEW.bearing,
    })

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right')

    return () => {
      clearMarkers()
      map.current?.remove()
      map.current = null
    }
  }, [clearMarkers])

  useEffect(() => {
    if (!map.current) return

    const targetView = selectedRegion && selectedRegion !== 'All' && REGION_CENTERS[selectedRegion]
      ? REGION_CENTERS[selectedRegion]
      : { center: INITIAL_VIEW.center, zoom: INITIAL_VIEW.zoom }

    map.current.flyTo({
      center: targetView.center,
      zoom: targetView.zoom,
      pitch: INITIAL_VIEW.pitch,
      bearing: INITIAL_VIEW.bearing,
      duration: 1000,
    })
  }, [selectedRegion])

  useEffect(() => {
    if (!map.current) return
    
    clearMarkers()

    const sampleRate = filteredFeatures.length > 1000 ? Math.ceil(filteredFeatures.length / 500) : 1
    const displayFeatures = filteredFeatures.filter((_, i) => i % sampleRate === 0)

    displayFeatures.forEach(feature => {
      const color = RISK_TIER_COLORS[feature.properties.risk_tier] || '#6b7280'
      const isCritical = feature.properties.risk_tier === 'CRITICAL'
      const isHigh = feature.properties.risk_tier === 'HIGH'
      
      const el = document.createElement('div')
      el.className = 'map-marker'
      el.style.cssText = `
        width: ${isCritical ? '16px' : isHigh ? '12px' : '8px'};
        height: ${isCritical ? '16px' : isHigh ? '12px' : '8px'};
        background-color: ${color};
        border-radius: 50%;
        border: 2px solid rgba(255,255,255,0.3);
        cursor: pointer;
        transition: transform 0.2s;
        box-shadow: 0 0 ${isCritical ? '12px' : '6px'} ${color}80;
        ${isCritical ? 'animation: pulse 2s infinite;' : ''}
      `
      
      el.addEventListener('mouseenter', () => {
        el.style.transform = 'scale(1.5)'
      })
      el.addEventListener('mouseleave', () => {
        el.style.transform = 'scale(1)'
      })
      
      if (onAssetClick) {
        el.addEventListener('click', () => {
          onAssetClick(feature.properties)
        })
      }

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(feature.geometry.coordinates)
        .addTo(map.current!)

      markersRef.current.push(marker)
    })
  }, [filteredFeatures, onAssetClick, clearMarkers])

  return (
    <div className="relative w-full h-full">
      <style>{`
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 12px var(--risk-critical); }
          50% { box-shadow: 0 0 20px var(--risk-critical); }
        }
      `}</style>
      
      <div ref={mapContainer} className="w-full h-full rounded-xl" />

      <div className="absolute bottom-4 left-4 bg-gray-800/95 backdrop-blur-sm rounded-lg p-3 shadow-xl border border-gray-700">
        <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Risk Tier</h4>
        <div className="space-y-1.5">
          {Object.entries(RISK_TIER_COLORS).map(([tier, color]) => (
            <div key={tier} className="flex items-center gap-2 text-sm">
              <span 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}80` }}
              />
              <span className="text-gray-300">{tier}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="absolute top-4 left-4 bg-gray-800/95 backdrop-blur-sm rounded-lg px-3 py-2 shadow-xl border border-gray-700">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span>{filteredFeatures.length.toLocaleString()} assets</span>
          {filteredFeatures.length > 500 && (
            <span className="text-gray-500">(sampled view)</span>
          )}
        </div>
      </div>
    </div>
  )
}
