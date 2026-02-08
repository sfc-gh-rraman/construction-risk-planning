import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { TreePine, AlertTriangle, CheckCircle, Clock, DollarSign, Filter, Search, ChevronRight } from 'lucide-react'


interface VegetationData {
  summary: {
    total_encroachments: number
    critical: number
    high_priority: number
    out_of_compliance: number
    total_trim_cost: number
    avg_clearance_ft: number
  }
  items: VegetationItem[]
}

interface VegetationItem {
  ENCROACHMENT_ID: string
  ASSET_ID: string
  REGION: string
  FIRE_THREAT_DISTRICT: string
  CURRENT_CLEARANCE_FT: number
  REQUIRED_CLEARANCE_FT: number
  TRIM_PRIORITY: string
  CLEARANCE_DEFICIT_FT: number
  DAYS_TO_CONTACT: number
  SPECIES: string
  GROWTH_RATE_FT_YEAR: number
  TREE_HEIGHT_FT: number
  CIRCUIT_NAME: string
}

async function getVegetationData(): Promise<VegetationData> {
  const res = await fetch('/api/vegetation')
  if (!res.ok) throw new Error('Failed to fetch vegetation data')
  return res.json()
}

export function Vegetation() {
  const [searchTerm, setSearchTerm] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('All')
  const [regionFilter, setRegionFilter] = useState('All')

  const { data, isLoading } = useQuery<VegetationData>({
    queryKey: ['vegetation'],
    queryFn: getVegetationData,
    refetchInterval: 60000,
  })

  const filteredItems = data?.items?.filter(item => {
    if (priorityFilter !== 'All' && item.TRIM_PRIORITY !== priorityFilter) return false
    if (regionFilter !== 'All' && item.REGION !== regionFilter) return false
    if (searchTerm && !item.ENCROACHMENT_ID.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !item.ASSET_ID.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  }) || []

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'CRITICAL': return 'text-red-500 bg-red-500/10 border-red-500/30'
      case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/30'
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30'
      default: return 'text-green-500 bg-green-500/10 border-green-500/30'
    }
  }

  return (
    <div className="h-full flex flex-col bg-navy-950">
      <div className="flex-shrink-0 p-6 border-b border-navy-700/50">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-5 gap-4">
            <div className="bg-navy-800/50 rounded-xl p-4 border border-navy-700">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                <TreePine size={16} />
                Total Encroachments
              </div>
              <div className="text-2xl font-bold text-white">
                {isLoading ? '...' : data?.summary?.total_encroachments?.toLocaleString()}
              </div>
            </div>
            <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/30">
              <div className="flex items-center gap-2 text-red-400 text-sm mb-1">
                <AlertTriangle size={16} />
                Critical
              </div>
              <div className="text-2xl font-bold text-red-500">
                {isLoading ? '...' : data?.summary?.critical}
              </div>
            </div>
            <div className="bg-orange-500/10 rounded-xl p-4 border border-orange-500/30">
              <div className="flex items-center gap-2 text-orange-400 text-sm mb-1">
                <Clock size={16} />
                High Priority
              </div>
              <div className="text-2xl font-bold text-orange-500">
                {isLoading ? '...' : data?.summary?.high_priority}
              </div>
            </div>
            <div className="bg-yellow-500/10 rounded-xl p-4 border border-yellow-500/30">
              <div className="flex items-center gap-2 text-yellow-400 text-sm mb-1">
                <CheckCircle size={16} />
                Out of Compliance
              </div>
              <div className="text-2xl font-bold text-yellow-500">
                {isLoading ? '...' : data?.summary?.out_of_compliance}
              </div>
            </div>
            <div className="bg-navy-800/50 rounded-xl p-4 border border-navy-700">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                <DollarSign size={16} />
                Est. Trim Cost
              </div>
              <div className="text-2xl font-bold text-vigil-green">
                ${isLoading ? '...' : ((data?.summary?.total_trim_cost || 0) / 1000000).toFixed(1)}M
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
                placeholder="Search encroachments..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-navy-800 border border-navy-600 rounded-lg pl-9 pr-4 py-1.5 text-sm text-white w-64"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-slate-400" />
              <select 
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="bg-navy-800 border border-navy-600 rounded-lg px-3 py-1.5 text-sm text-white"
              >
                <option value="All">All Priorities</option>
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
            Showing {filteredItems.length} of {data?.items?.length || 0} encroachments
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto">
          {isLoading ? (
            <div className="space-y-4">
              {[1,2,3,4,5].map(i => (
                <div key={i} className="bg-navy-800/50 rounded-xl p-4 border border-navy-700 animate-pulse h-24" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredItems.map((item) => (
                <div 
                  key={item.ENCROACHMENT_ID}
                  className="bg-navy-800/50 rounded-xl p-4 border border-navy-700 hover:border-navy-600 transition-colors cursor-pointer group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`px-3 py-1 rounded-lg border text-sm font-medium ${getPriorityColor(item.TRIM_PRIORITY)}`}>
                        {item.TRIM_PRIORITY}
                      </div>
                      <div>
                        <div className="text-white font-semibold">{item.ENCROACHMENT_ID}</div>
                        <div className="text-sm text-slate-400">{item.SPECIES} • {item.CIRCUIT_NAME}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-8">
                      <div className="text-right">
                        <div className="text-sm text-slate-400">Clearance</div>
                        <div className="text-white">
                          <span className={item.CURRENT_CLEARANCE_FT < item.REQUIRED_CLEARANCE_FT ? 'text-red-400' : 'text-green-400'}>
                            {item.CURRENT_CLEARANCE_FT?.toFixed(1)}ft
                          </span>
                          <span className="text-slate-500"> / {item.REQUIRED_CLEARANCE_FT}ft req</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-slate-400">Days to Contact</div>
                        <div className={`text-white ${item.DAYS_TO_CONTACT < 30 ? 'text-red-400' : item.DAYS_TO_CONTACT < 60 ? 'text-yellow-400' : ''}`}>
                          {item.DAYS_TO_CONTACT}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-slate-400">Fire Tier</div>
                        <div className="text-white">{item.FIRE_THREAT_DISTRICT}</div>
                      </div>
                      <ChevronRight size={20} className="text-slate-500 group-hover:text-white transition-colors" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
