import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import { 
  AlertTriangle,
  Activity,
  Zap,
  TreePine,
  Flame,
  Building2,
  Brain
} from 'lucide-react'
import { Copilot } from '../components/Copilot'
import { FireSeasonBanner } from '../components/FireSeasonBanner'
import { MLInsightsPanel } from '../components/MLInsightsPanel'
import { getDashboardMetrics } from '../services/api'
import type { DashboardMetrics } from '../types'
import { REGIONS, RISK_TIER_COLORS } from '../types'

interface MetricGaugeProps {
  label: string
  value: number
  target?: number
  showTrend?: boolean
  trend?: 'up' | 'down'
}

function MetricGauge({ label, value, target = 1.0, showTrend, trend }: MetricGaugeProps) {
  const percentage = Math.min((value / target) * 100, 100)
  const isGood = value >= target * 0.95
  const isBad = value < target * 0.9
  
  return (
    <div className="text-center">
      <div className="relative w-24 h-24 mx-auto">
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="48"
            cy="48"
            r="40"
            fill="none"
            stroke="#374151"
            strokeWidth="8"
          />
          <circle
            cx="48"
            cy="48"
            r="40"
            fill="none"
            stroke={isGood ? '#10b981' : isBad ? '#ef4444' : '#f59e0b'}
            strokeWidth="8"
            strokeDasharray={`${percentage * 2.51} 251`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-2xl font-bold ${isGood ? 'text-green-500' : isBad ? 'text-red-500' : 'text-yellow-500'}`}>
            {value.toFixed(2)}
          </span>
          {showTrend && trend && (
            <span className={`text-xs ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
              {trend === 'up' ? '↑' : '↓'}
            </span>
          )}
        </div>
      </div>
      <div className="text-xs text-slate-400 mt-2">{label}</div>
    </div>
  )
}

interface AlertCardProps {
  alert: {
    level: 'critical' | 'warning' | 'info'
    type: string
    project: string
    message: string
  }
}

function AlertCard({ alert }: AlertCardProps) {
  const colors = {
    critical: 'border-red-500/50 bg-red-500/10',
    warning: 'border-orange-500/50 bg-orange-500/10',
    info: 'border-purple-500/50 bg-purple-500/10'
  }
  const dotColors = {
    critical: 'bg-red-500',
    warning: 'bg-orange-500',
    info: 'bg-purple-500'
  }
  
  return (
    <div className={`rounded-lg p-3 border ${colors[alert.level]}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className={`w-2 h-2 rounded-full ${dotColors[alert.level]} ${alert.level === 'critical' ? 'animate-pulse' : ''}`} />
        <span className="text-xs font-medium text-slate-300">{alert.project}</span>
      </div>
      <p className="text-xs text-slate-400">{alert.message}</p>
    </div>
  )
}

export function RiskDashboard() {
  const [selectedRegion, setSelectedRegion] = useState('All')
  const [showMLPanel, setShowMLPanel] = useState(true)

  const { data: metrics, isLoading } = useQuery<DashboardMetrics>({
    queryKey: ['dashboardMetrics'],
    queryFn: getDashboardMetrics,
    refetchInterval: 60000,
  })

  const summaryStats = useMemo(() => {
    if (!metrics) return null

    const assetSummary = metrics.asset_summary
    const riskSummary = metrics.risk_summary
    const complianceSummary = metrics.compliance_summary

    const filterByRegion = <T extends { REGION: string }>(data: T[]) => {
      if (selectedRegion === 'All') return data
      return data.filter(d => d.REGION === selectedRegion)
    }

    const filteredAssets = filterByRegion(assetSummary)
    const filteredRisk = filterByRegion(riskSummary)
    const filteredCompliance = filterByRegion(complianceSummary)

    return {
      totalAssets: filteredAssets.reduce((sum, a) => sum + a.ASSET_COUNT, 0),
      poorConditionAssets: filteredAssets.reduce((sum, a) => sum + a.POOR_CONDITION_COUNT, 0),
      criticalRiskAssets: filteredRisk
        .filter(r => r.RISK_TIER === 'CRITICAL')
        .reduce((sum, r) => sum + r.ASSET_COUNT, 0),
      highRiskAssets: filteredRisk
        .filter(r => r.RISK_TIER === 'HIGH')
        .reduce((sum, r) => sum + r.ASSET_COUNT, 0),
      outOfCompliance: filteredCompliance.reduce((sum, c) => sum + c.OUT_OF_COMPLIANCE, 0),
      totalTrimCost: filteredCompliance.reduce((sum, c) => sum + (c.TOTAL_TRIM_COST || 0), 0),
    }
  }, [metrics, selectedRegion])

  const alerts = useMemo(() => {
    const result: AlertCardProps['alert'][] = []
    if (summaryStats && summaryStats.criticalRiskAssets > 0) {
      result.push({
        level: 'critical',
        type: 'risk',
        project: 'Critical Risk Assets',
        message: `${summaryStats.criticalRiskAssets} assets need immediate inspection`
      })
    }
    if (summaryStats && summaryStats.outOfCompliance > 0) {
      result.push({
        level: 'warning',
        type: 'vegetation',
        project: 'Vegetation Non-Compliance',
        message: `${summaryStats.outOfCompliance} spans need trimming`
      })
    }
    result.push({
      level: 'critical',
      type: 'discovery',
      project: 'Hidden Pattern Detected',
      message: 'Water treeing degradation in underground cables - ask VIGIL!'
    })
    return result
  }, [summaryStats])

  const riskHealthScore = useMemo(() => {
    if (!summaryStats || summaryStats.totalAssets === 0) return 0.95
    const criticalPct = summaryStats.criticalRiskAssets / summaryStats.totalAssets
    const highPct = summaryStats.highRiskAssets / summaryStats.totalAssets
    return Math.max(0.7, 1 - (criticalPct * 2) - (highPct * 0.5))
  }, [summaryStats])

  const complianceScore = useMemo(() => {
    if (!summaryStats || summaryStats.totalAssets === 0) return 0.92
    return Math.max(0.7, 1 - (summaryStats.outOfCompliance / summaryStats.totalAssets) * 2)
  }, [summaryStats])

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading Risk Dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <FireSeasonBanner 
        fireStatus={metrics?.fire_season || null}
        loading={isLoading}
      />

      <div className="flex-1 flex min-h-0">
        <div className="w-[400px] flex-shrink-0 border-r border-gray-700/50 flex flex-col overflow-hidden bg-gray-900/50">
          <div className="p-6 border-b border-gray-700/50">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-4 flex items-center gap-2">
              <Activity size={14} />
              Portfolio Health
            </h2>
            
            <div className="grid grid-cols-2 gap-6">
              <MetricGauge 
                label="Risk Score" 
                value={riskHealthScore} 
                target={1.0}
                showTrend
                trend={riskHealthScore >= 0.9 ? 'up' : 'down'}
              />
              <MetricGauge 
                label="Compliance" 
                value={complianceScore} 
                target={1.0}
                showTrend
                trend={complianceScore >= 0.9 ? 'up' : 'down'}
              />
            </div>
          </div>

          <div className="p-6 border-b border-gray-700/50">
            <div className="flex flex-wrap gap-1.5 mb-4">
              <button
                onClick={() => setSelectedRegion('All')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  selectedRegion === 'All'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                All
              </button>
              {REGIONS.map(region => (
                <button
                  key={region}
                  onClick={() => setSelectedRegion(region)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                    selectedRegion === region
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {region}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <Building2 size={16} className="text-blue-400" />
                  <span className="text-xs text-slate-500">Assets</span>
                </div>
                <div className="text-2xl font-bold text-white">
                  {summaryStats?.totalAssets.toLocaleString() || 0}
                </div>
                <div className="text-xs text-slate-500">Active</div>
              </div>
              
              <div className="bg-gray-800/80 rounded-xl p-4 border border-red-500/50">
                <div className="flex items-center gap-2 mb-2">
                  <Flame size={16} className="text-red-500" />
                  <span className="text-xs text-slate-500">Critical</span>
                </div>
                <div className="text-2xl font-bold text-red-400">
                  {summaryStats?.criticalRiskAssets.toLocaleString() || 0}
                </div>
                <div className="text-xs text-slate-500">Need Action</div>
              </div>
              
              <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle size={16} className="text-orange-500" />
                  <span className="text-xs text-slate-500">High Risk</span>
                </div>
                <div className="text-2xl font-bold text-white">
                  {summaryStats?.highRiskAssets.toLocaleString() || 0}
                </div>
                <div className="text-xs text-slate-500">Monitor</div>
              </div>
              
              <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <TreePine size={16} className="text-green-500" />
                  <span className="text-xs text-slate-500">Veg. Issues</span>
                </div>
                <div className="text-2xl font-bold text-white">
                  {summaryStats?.outOfCompliance.toLocaleString() || 0}
                </div>
                <div className="text-xs text-slate-500">Non-Compliant</div>
              </div>
            </div>
          </div>

          {metrics && selectedRegion === 'All' && (
            <div className="p-6 border-b border-gray-700/50">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                <Zap size={14} />
                Risk by Region
              </h2>
              <div className="space-y-2">
                {REGIONS.map(region => {
                  const regionRisk = metrics.risk_summary.filter(r => r.REGION === region)
                  const total = regionRisk.reduce((sum, r) => sum + r.ASSET_COUNT, 0)
                  if (total === 0) return null

                  return (
                    <div key={region}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-300">{region}</span>
                        <span className="text-xs text-gray-500">{total.toLocaleString()}</span>
                      </div>
                      <div className="h-2 bg-gray-700 rounded-full overflow-hidden flex">
                        {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(tier => {
                          const tierData = regionRisk.find(r => r.RISK_TIER === tier)
                          const pct = tierData ? (tierData.ASSET_COUNT / total) * 100 : 0
                          return (
                            <div
                              key={tier}
                              style={{ 
                                width: `${pct}%`,
                                backgroundColor: RISK_TIER_COLORS[tier]
                              }}
                              className="h-full"
                              title={`${tier}: ${tierData?.ASSET_COUNT || 0}`}
                            />
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="flex flex-wrap gap-3 mt-3 text-xs">
                {Object.entries(RISK_TIER_COLORS).map(([tier, color]) => (
                  <div key={tier} className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-gray-400">{tier}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-4 flex items-center gap-2">
              <AlertTriangle size={14} />
              Active Alerts ({alerts.length})
            </h2>
            
            <div className="space-y-3">
              {alerts.map((alert, i) => (
                <AlertCard key={i} alert={alert} />
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <div className="p-4 border-b border-gray-700/50 flex items-center justify-between bg-gray-800/30">
            <div>
              <h2 className="font-semibold text-white">VIGIL Co-Pilot</h2>
              <p className="text-xs text-slate-500">Ask about risk, vegetation, assets, and hidden patterns</p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowMLPanel(!showMLPanel)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  showMLPanel 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <Brain size={14} />
                ML Insights
              </button>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-slate-500">4 Agents Ready</span>
              </div>
            </div>
          </div>
          <div className="flex-1 flex min-h-0">
            <div className={`${showMLPanel ? 'flex-1' : 'w-full'} flex flex-col`}>
              <Copilot onWorkOrderCreated={() => {}} />
            </div>
            {showMLPanel && (
              <div className="w-[340px] flex-shrink-0 border-l border-gray-700/50 bg-gray-900/50">
                <MLInsightsPanel />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
