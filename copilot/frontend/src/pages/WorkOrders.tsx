import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Wrench, Clock, CheckCircle, AlertTriangle, Filter, Search, ChevronRight, Calendar, User } from 'lucide-react'


interface WorkOrderData {
  summary: {
    total: number
    open: number
    in_progress: number
    completed: number
    overdue: number
  }
  items: WorkOrderItem[]
}

interface WorkOrderItem {
  WORK_ORDER_ID: string
  ASSET_ID: string
  WORK_ORDER_TYPE: string
  STATUS: string
  PRIORITY: string
  SCHEDULED_DATE: string
  COMPLETED_DATE: string | null
  ASSIGNED_CREW: string
  ESTIMATED_COST: number
  REGION: string
  ASSET_TYPE: string
  DESCRIPTION: string
  CIRCUIT_NAME: string
}

async function getWorkOrders(): Promise<WorkOrderData> {
  const res = await fetch('/api/workorders')
  if (!res.ok) throw new Error('Failed to fetch work orders')
  return res.json()
}

export function WorkOrders() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [typeFilter, setTypeFilter] = useState('All')

  const { data, isLoading } = useQuery<WorkOrderData>({
    queryKey: ['workorders'],
    queryFn: getWorkOrders,
    refetchInterval: 60000,
  })

  const filteredItems = data?.items?.filter(item => {
    if (statusFilter !== 'All' && item.STATUS !== statusFilter) return false
    if (typeFilter !== 'All' && item.WORK_ORDER_TYPE !== typeFilter) return false
    if (searchTerm && !item.WORK_ORDER_ID.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !item.ASSET_ID.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  }) || []

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN': return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
      case 'IN_PROGRESS': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
      case 'COMPLETED': return 'text-green-400 bg-green-500/10 border-green-500/30'
      case 'OVERDUE': return 'text-red-400 bg-red-500/10 border-red-500/30'
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'EMERGENCY': return 'text-red-500'
      case 'HIGH': return 'text-orange-500'
      case 'MEDIUM': return 'text-yellow-500'
      default: return 'text-green-500'
    }
  }

  return (
    <div className="h-full flex flex-col bg-navy-950">
      <div className="flex-shrink-0 p-6 border-b border-navy-700/50">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-5 gap-4">
            <div className="bg-navy-800/50 rounded-xl p-4 border border-navy-700">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                <Wrench size={16} />
                Total Work Orders
              </div>
              <div className="text-2xl font-bold text-white">
                {isLoading ? '...' : data?.summary?.total?.toLocaleString()}
              </div>
            </div>
            <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-500/30">
              <div className="flex items-center gap-2 text-blue-400 text-sm mb-1">
                <Clock size={16} />
                Open
              </div>
              <div className="text-2xl font-bold text-blue-400">
                {isLoading ? '...' : data?.summary?.open}
              </div>
            </div>
            <div className="bg-yellow-500/10 rounded-xl p-4 border border-yellow-500/30">
              <div className="flex items-center gap-2 text-yellow-400 text-sm mb-1">
                <Wrench size={16} />
                In Progress
              </div>
              <div className="text-2xl font-bold text-yellow-400">
                {isLoading ? '...' : data?.summary?.in_progress}
              </div>
            </div>
            <div className="bg-green-500/10 rounded-xl p-4 border border-green-500/30">
              <div className="flex items-center gap-2 text-green-400 text-sm mb-1">
                <CheckCircle size={16} />
                Completed
              </div>
              <div className="text-2xl font-bold text-green-400">
                {isLoading ? '...' : data?.summary?.completed}
              </div>
            </div>
            <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/30">
              <div className="flex items-center gap-2 text-red-400 text-sm mb-1">
                <AlertTriangle size={16} />
                Overdue
              </div>
              <div className="text-2xl font-bold text-red-400">
                {isLoading ? '...' : data?.summary?.overdue}
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
                placeholder="Search work orders..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-navy-800 border border-navy-600 rounded-lg pl-9 pr-4 py-1.5 text-sm text-white w-64"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-slate-400" />
              <select 
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-navy-800 border border-navy-600 rounded-lg px-3 py-1.5 text-sm text-white"
              >
                <option value="All">All Statuses</option>
                <option value="OPEN">Open</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
              </select>
              <select 
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="bg-navy-800 border border-navy-600 rounded-lg px-3 py-1.5 text-sm text-white"
              >
                <option value="All">All Types</option>
                <option value="VEGETATION_TRIM">Vegetation Trim</option>
                <option value="INSPECTION">Inspection</option>
                <option value="REPAIR">Repair</option>
                <option value="REPLACEMENT">Replacement</option>
              </select>
            </div>
          </div>
          <div className="text-sm text-slate-400">
            Showing {filteredItems.length} of {data?.items?.length || 0} work orders
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
                  key={item.WORK_ORDER_ID}
                  className="bg-navy-800/50 rounded-xl p-4 border border-navy-700 hover:border-navy-600 transition-colors cursor-pointer group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`px-3 py-1 rounded-lg border text-sm font-medium ${getStatusColor(item.STATUS)}`}>
                        {item.STATUS?.replace('_', ' ')}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-white font-semibold">{item.WORK_ORDER_ID}</span>
                          <span className={`text-sm ${getPriorityColor(item.PRIORITY)}`}>● {item.PRIORITY}</span>
                        </div>
                        <div className="text-sm text-slate-400">
                          {item.WORK_ORDER_TYPE?.replace('_', ' ')} • {item.ASSET_TYPE} • {item.CIRCUIT_NAME}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-8">
                      <div className="flex items-center gap-2 text-slate-400">
                        <User size={14} />
                        <span className="text-sm">{item.ASSIGNED_CREW || 'Unassigned'}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-400">
                        <Calendar size={14} />
                        <span className="text-sm">{item.SCHEDULED_DATE ? new Date(item.SCHEDULED_DATE).toLocaleDateString() : 'N/A'}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-slate-400">Est. Cost</div>
                        <div className="text-white">${item.ESTIMATED_COST?.toLocaleString() || 0}</div>
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
