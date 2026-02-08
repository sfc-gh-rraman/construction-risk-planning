import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Zap, Search, Filter, ChevronRight, AlertTriangle, CheckCircle } from 'lucide-react'


interface AssetData {
  items: AssetItem[]
  total: number
}

interface AssetItem {
  ASSET_ID: string
  ASSET_TYPE: string
  CONDITION_SCORE: number
  ASSET_AGE_YEARS: number
  REGION: string
  CIRCUIT_NAME: string
  FIRE_THREAT_DISTRICT: string
  LAST_INSPECTION_DATE: string
  risk_tier?: string
}

async function getAssets(): Promise<AssetData> {
  const res = await fetch('/api/assets')
  if (!res.ok) throw new Error('Failed to fetch assets')
  return res.json()
}

export function AssetRegistry() {
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState('All')
  const [riskFilter, setRiskFilter] = useState('All')
  const [regionFilter, setRegionFilter] = useState('All')

  const { data, isLoading } = useQuery<AssetData>({
    queryKey: ['assets'],
    queryFn: getAssets,
    refetchInterval: 60000,
  })

  const getConditionRisk = (score: number) => {
    if (score < 0.3) return 'CRITICAL'
    if (score < 0.5) return 'HIGH'
    if (score < 0.7) return 'MEDIUM'
    return 'LOW'
  }

  const filteredItems = data?.items?.filter(item => {
    if (typeFilter !== 'All' && item.ASSET_TYPE !== typeFilter) return false
    if (riskFilter !== 'All' && getConditionRisk(item.CONDITION_SCORE) !== riskFilter) return false
    if (regionFilter !== 'All' && item.REGION !== regionFilter) return false
    if (searchTerm && !item.ASSET_ID.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  }) || []

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'CRITICAL': return 'text-red-500 bg-red-500/10'
      case 'HIGH': return 'text-orange-500 bg-orange-500/10'
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10'
      default: return 'text-green-500 bg-green-500/10'
    }
  }

  const getConditionColor = (score: number) => {
    if (score < 0.4) return 'text-red-400'
    if (score < 0.7) return 'text-yellow-400'
    return 'text-green-400'
  }

  const assetTypes = [...new Set(data?.items?.map(i => i.ASSET_TYPE) || [])]

  return (
    <div className="h-full flex flex-col bg-navy-950">
      <div className="flex-shrink-0 p-6 border-b border-navy-700/50">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-navy-800/50 rounded-xl p-4 border border-navy-700">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                <Zap size={16} />
                Total Assets
              </div>
              <div className="text-2xl font-bold text-white">
                {isLoading ? '...' : data?.total?.toLocaleString()}
              </div>
            </div>
            <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/30">
              <div className="flex items-center gap-2 text-red-400 text-sm mb-1">
                <AlertTriangle size={16} />
                Critical Risk
              </div>
              <div className="text-2xl font-bold text-red-500">
                {isLoading ? '...' : data?.items?.filter(i => i.CONDITION_SCORE < 0.3).length}
              </div>
            </div>
            <div className="bg-orange-500/10 rounded-xl p-4 border border-orange-500/30">
              <div className="flex items-center gap-2 text-orange-400 text-sm mb-1">
                <AlertTriangle size={16} />
                High Risk
              </div>
              <div className="text-2xl font-bold text-orange-500">
                {isLoading ? '...' : data?.items?.filter(i => i.CONDITION_SCORE >= 0.3 && i.CONDITION_SCORE < 0.5).length}
              </div>
            </div>
            <div className="bg-yellow-500/10 rounded-xl p-4 border border-yellow-500/30">
              <div className="flex items-center gap-2 text-yellow-400 text-sm mb-1">
                <CheckCircle size={16} />
                Poor Condition
              </div>
              <div className="text-2xl font-bold text-yellow-500">
                {isLoading ? '...' : data?.items?.filter(i => i.CONDITION_SCORE < 0.4).length}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-shrink-0 bg-navy-900/50 border-b border-navy-700/50 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search assets..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-navy-800 border border-navy-600 rounded-lg pl-9 pr-4 py-1.5 text-sm text-white w-64"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-slate-400" />
              <select 
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="bg-navy-800 border border-navy-600 rounded-lg px-3 py-1.5 text-sm text-white"
              >
                <option value="All">All Types</option>
                {assetTypes.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <select 
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="bg-navy-800 border border-navy-600 rounded-lg px-3 py-1.5 text-sm text-white"
              >
                <option value="All">All Risk Tiers</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
              <select 
                value={regionFilter}
                onChange={(e) => setRegionFilter(e.target.value)}
                className="bg-navy-800 border border-navy-600 rounded-lg px-3 py-1.5 text-sm text-white"
              >
                <option value="All">All Regions</option>
                <option value="NorCal">NorCal</option>
                <option value="Central">Central</option>
                <option value="SoCal">SoCal</option>
              </select>
            </div>
          </div>
          <div className="text-sm text-slate-400">
            Showing {filteredItems.length} of {data?.items?.length || 0} assets
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-navy-800/30 rounded-xl border border-navy-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-navy-800/50">
                <tr className="text-left text-sm text-slate-400">
                  <th className="px-4 py-3 font-medium">Asset ID</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Region</th>
                  <th className="px-4 py-3 font-medium">Risk Tier</th>
                  <th className="px-4 py-3 font-medium">Condition</th>
                  <th className="px-4 py-3 font-medium">Age (yrs)</th>
                  <th className="px-4 py-3 font-medium">Fire District</th>
                  <th className="px-4 py-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-700/50">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-slate-400">Loading...</td>
                  </tr>
                ) : filteredItems.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-slate-400">No assets found</td>
                  </tr>
                ) : (
                  filteredItems.slice(0, 100).map((item) => (
                    <tr key={item.ASSET_ID} className="hover:bg-navy-700/30 transition-colors cursor-pointer group">
                      <td className="px-4 py-3 text-white font-medium">{item.ASSET_ID}</td>
                      <td className="px-4 py-3 text-slate-300">{item.ASSET_TYPE}</td>
                      <td className="px-4 py-3 text-slate-300">{item.REGION}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(getConditionRisk(item.CONDITION_SCORE))}`}>
                          {getConditionRisk(item.CONDITION_SCORE)}
                        </span>
                      </td>
                      <td className={`px-4 py-3 font-medium ${getConditionColor(item.CONDITION_SCORE)}`}>
                        {((item.CONDITION_SCORE ?? 0) * 100).toFixed(0)}%
                      </td>
                      <td className="px-4 py-3 text-slate-300">{item.ASSET_AGE_YEARS}</td>
                      <td className="px-4 py-3 text-slate-300">{item.FIRE_THREAT_DISTRICT}</td>
                      <td className="px-4 py-3">
                        <ChevronRight size={16} className="text-slate-500 group-hover:text-white transition-colors" />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {filteredItems.length > 100 && (
            <div className="mt-4 text-center text-sm text-slate-400">
              Showing first 100 results. Use filters to narrow your search.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
