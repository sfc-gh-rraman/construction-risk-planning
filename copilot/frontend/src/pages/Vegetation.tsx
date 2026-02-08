import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import { 
  TreePine, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  DollarSign, 
  Filter, 
  Search, 
  ChevronRight,
  TrendingUp,
  Activity,
  Brain,
  Loader2
} from 'lucide-react'
import { LineChart, Line, ResponsiveContainer, Tooltip, AreaChart, Area, BarChart, Bar, Cell } from 'recharts'

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

interface VegPrediction {
  PREDICTED_DAYS_TO_CONTACT: number
  GROWTH_RISK: string
  PREDICTED_GROWTH_RATE: number
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function getVegetationData(): Promise<VegetationData> {
  const res = await fetch(`${API_BASE}/vegetation`)
  if (!res.ok) throw new Error('Failed to fetch vegetation data')
  return res.json()
}

async function getVegPredictions(): Promise<{ predictions: VegPrediction[] }> {
  const res = await fetch(`${API_BASE}/ml/vegetation-growth?limit=100`)
  if (!res.ok) throw new Error('Failed to fetch predictions')
  return res.json()
}

function generateGrowthSparkline(item: VegetationItem) {
  const currentClearance = item.CURRENT_CLEARANCE_FT
  const growthRate = item.GROWTH_RATE_FT_YEAR || 2
  const monthlyGrowth = growthRate / 12
  
  return Array.from({ length: 12 }, (_, i) => ({
    month: i,
    clearance: Math.max(0, currentClearance - (monthlyGrowth * i)),
    required: item.REQUIRED_CLEARANCE_FT
  }))
}

function GrowthSparkline({ data, current, required }: { 
  data: { month: number; clearance: number; required: number }[]
  current: number
  required: number
}) {
  const contactMonth = data.findIndex(d => d.clearance <= required)
  
  return (
    <div className="w-32 h-8">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="clearanceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={current < required ? "#ef4444" : "#22c55e"} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={current < required ? "#ef4444" : "#22c55e"} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <Area 
            type="monotone" 
            dataKey="clearance" 
            stroke={current < required ? "#ef4444" : "#22c55e"}
            fill="url(#clearanceGradient)"
            strokeWidth={1.5}
          />
          <Line 
            type="monotone" 
            dataKey="required" 
            stroke="#f97316" 
            strokeDasharray="3 3"
            strokeWidth={1}
            dot={false}
          />
          <Tooltip
            contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', fontSize: '11px' }}
            labelStyle={{ color: '#9ca3af' }}
            formatter={(value: number, name: string) => [
              `${value.toFixed(1)}ft`, 
              name === 'clearance' ? 'Projected' : 'Required'
            ]}
            labelFormatter={(month) => `Month ${month}`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

function DaysCountdown({ days, isML }: { days: number; isML?: boolean }) {
  const color = days < 30 ? 'text-red-400' : days < 60 ? 'text-yellow-400' : 'text-green-400'
  const bgColor = days < 30 ? 'bg-red-500/10' : days < 60 ? 'bg-yellow-500/10' : 'bg-green-500/10'
  
  return (
    <div className={`flex items-center gap-2 ${bgColor} rounded-lg px-3 py-1.5`}>
      <Clock size={14} className={color} />
      <span className={`font-bold ${color}`}>{days}</span>
      <span className="text-xs text-slate-400">days</span>
      {isML && <Brain size={10} className="text-purple-400" />}
    </div>
  )
}

function RiskByCircuitChart({ items }: { items: VegetationItem[] }) {
  const circuitData = useMemo(() => {
    const grouped = items.reduce((acc, item) => {
      const circuit = item.CIRCUIT_NAME || 'Unknown'
      if (!acc[circuit]) {
        acc[circuit] = { circuit, critical: 0, high: 0, medium: 0, low: 0, total: 0 }
      }
      acc[circuit].total++
      if (item.TRIM_PRIORITY === 'CRITICAL') acc[circuit].critical++
      else if (item.TRIM_PRIORITY === 'HIGH') acc[circuit].high++
      else if (item.TRIM_PRIORITY === 'MEDIUM') acc[circuit].medium++
      else acc[circuit].low++
      return acc
    }, {} as Record<string, { circuit: string; critical: number; high: number; medium: number; low: number; total: number }>)
    
    return Object.values(grouped)
      .sort((a, b) => (b.critical + b.high) - (a.critical + a.high))
      .slice(0, 8)
  }, [items])
  
  return (
    <div className="bg-navy-800/50 rounded-xl p-4 border border-navy-700">
      <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
        <Activity size={14} />
        Risk Heatmap by Circuit
      </h3>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={circuitData} layout="vertical">
            <Bar dataKey="critical" stackId="a" fill="#ef4444" radius={[0, 0, 0, 0]} />
            <Bar dataKey="high" stackId="a" fill="#f97316" radius={[0, 0, 0, 0]} />
            <Bar dataKey="medium" stackId="a" fill="#eab308" radius={[0, 0, 0, 0]} />
            <Bar dataKey="low" stackId="a" fill="#22c55e" radius={[0, 4, 4, 0]} />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', fontSize: '11px' }}
              labelStyle={{ color: '#fff' }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center justify-center gap-4 mt-2 text-xs">
        <div className="flex items-center gap-1"><div className="w-2 h-2 bg-red-500 rounded" /><span className="text-slate-400">Critical</span></div>
        <div className="flex items-center gap-1"><div className="w-2 h-2 bg-orange-500 rounded" /><span className="text-slate-400">High</span></div>
        <div className="flex items-center gap-1"><div className="w-2 h-2 bg-yellow-500 rounded" /><span className="text-slate-400">Medium</span></div>
        <div className="flex items-center gap-1"><div className="w-2 h-2 bg-green-500 rounded" /><span className="text-slate-400">Low</span></div>
      </div>
    </div>
  )
}

export function Vegetation() {
  const [searchTerm, setSearchTerm] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('All')
  const [regionFilter, setRegionFilter] = useState('All')
  const [showMLPredictions, setShowMLPredictions] = useState(true)

  const { data, isLoading } = useQuery<VegetationData>({
    queryKey: ['vegetation'],
    queryFn: getVegetationData,
    refetchInterval: 60000,
  })

  const { data: mlData, isLoading: mlLoading } = useQuery({
    queryKey: ['vegPredictions'],
    queryFn: getVegPredictions,
    enabled: showMLPredictions
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

  const urgentCount = useMemo(() => 
    filteredItems.filter(i => i.DAYS_TO_CONTACT < 30).length,
    [filteredItems]
  )

  return (
    <div className="h-full flex flex-col bg-navy-950">
      <div className="flex-shrink-0 p-6 border-b border-navy-700/50">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-6 gap-4">
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
            <div className="bg-purple-500/10 rounded-xl p-4 border border-purple-500/30">
              <div className="flex items-center gap-2 text-purple-400 text-sm mb-1">
                <Brain size={16} />
                ML Urgent (&lt;30d)
              </div>
              <div className="text-2xl font-bold text-purple-400 flex items-center gap-2">
                {mlLoading ? <Loader2 size={20} className="animate-spin" /> : urgentCount}
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
          
          <div className="mt-4">
            <RiskByCircuitChart items={data?.items || []} />
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
            <button
              onClick={() => setShowMLPredictions(!showMLPredictions)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                showMLPredictions 
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' 
                  : 'bg-navy-800 text-slate-400 border border-navy-600'
              }`}
            >
              <Brain size={14} />
              ML Predictions
            </button>
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
              {filteredItems.map((item) => {
                const sparklineData = generateGrowthSparkline(item)
                return (
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
                      <div className="flex items-center gap-6">
                        <div className="text-center">
                          <div className="text-xs text-slate-500 mb-1">12-Month Growth Projection</div>
                          <GrowthSparkline 
                            data={sparklineData} 
                            current={item.CURRENT_CLEARANCE_FT}
                            required={item.REQUIRED_CLEARANCE_FT}
                          />
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-slate-400 mb-1">Clearance</div>
                          <div className="text-white">
                            <span className={item.CURRENT_CLEARANCE_FT < item.REQUIRED_CLEARANCE_FT ? 'text-red-400' : 'text-green-400'}>
                              {item.CURRENT_CLEARANCE_FT?.toFixed(1)}ft
                            </span>
                            <span className="text-slate-500 text-xs"> / {item.REQUIRED_CLEARANCE_FT}ft</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-slate-400 mb-1">Growth Rate</div>
                          <div className="flex items-center gap-1 text-white">
                            <TrendingUp size={12} className="text-orange-400" />
                            {item.GROWTH_RATE_FT_YEAR?.toFixed(1)} ft/yr
                          </div>
                        </div>
                        <DaysCountdown days={item.DAYS_TO_CONTACT} isML={showMLPredictions} />
                        <div className="text-right">
                          <div className="text-xs text-slate-400 mb-1">Fire Tier</div>
                          <div className="text-orange-400 font-medium">{item.FIRE_THREAT_DISTRICT}</div>
                        </div>
                        <ChevronRight size={20} className="text-slate-500 group-hover:text-white transition-colors" />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
