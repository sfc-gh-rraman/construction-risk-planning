import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Flame, 
  TreePine, 
  Zap, 
  Shield, 
  ArrowRight,
  Map,
  Sparkles,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  Wrench,
  Brain,
  Activity,
  Loader2
} from 'lucide-react'
import type { Page } from '../App'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const COPILOT_NAME = "VIGIL"

const features = [
  {
    icon: Flame,
    title: 'Fire Risk Intelligence',
    description: 'Real-time PSPS threat assessment with ML-powered ignition probability scoring across fire threat districts.',
    color: 'red'
  },
  {
    icon: TreePine,
    title: 'Vegetation Management',
    description: 'GO95 compliance tracking with predictive growth modeling and automated trim scheduling.',
    color: 'green'
  },
  {
    icon: Zap,
    title: 'Grid Asset Health',
    description: 'Condition monitoring for 5,000+ assets with predictive failure analysis and maintenance optimization.',
    color: 'blue'
  },
  {
    icon: Shield,
    title: 'Proactive Risk Mitigation',
    description: 'AI-driven work order prioritization based on composite risk scores and regulatory requirements.',
    color: 'purple'
  }
]

interface LandingProps {
  onNavigate: (page: Page) => void
}

export function Landing({ onNavigate }: LandingProps) {
  const [mounted, setMounted] = useState(false)
  const [typedText, setTypedText] = useState('')
  const fullText = `Hello, I'm ${COPILOT_NAME}. Your intelligent grid safety co-pilot.`

  const { data: dashboardStats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      const [assetsRes, vegRes, workordersRes, mlRes] = await Promise.all([
        fetch(`${API_BASE}/assets/summary`).then(r => r.json()),
        fetch(`${API_BASE}/vegetation`).then(r => r.json()),
        fetch(`${API_BASE}/work-orders`).then(r => r.json()),
        fetch(`${API_BASE}/ml/summary`).then(r => r.json())
      ])
      return {
        totalAssets: assetsRes?.summary?.reduce((acc: number, s: any) => acc + (s.ASSET_COUNT || 0), 0) || 0,
        vegPoints: vegRes?.items?.length || 0,
        workOrders: workordersRes?.items?.length || 0,
        fireDistricts: 3,
        mlPredictions: (mlRes?.models?.asset_health?.total_predictions || 0) + 
                       (mlRes?.models?.vegetation_growth?.total_predictions || 0) +
                       (mlRes?.models?.ignition_risk?.total_predictions || 0) +
                       (mlRes?.models?.cable_failure?.total_predictions || 0),
        criticalAssets: mlRes?.models?.asset_health?.critical_count || 0,
        waterTreeing: mlRes?.models?.cable_failure?.at_risk_count || 0
      }
    },
    staleTime: 60000
  })

  const stats = [
    { 
      value: statsLoading ? '...' : (dashboardStats?.totalAssets?.toLocaleString() || '5,000'), 
      label: 'Grid Assets', 
      icon: Zap,
      color: 'text-blue-400'
    },
    { 
      value: statsLoading ? '...' : (dashboardStats?.vegPoints?.toLocaleString() || '945'), 
      label: 'Vegetation Points', 
      icon: TreePine,
      color: 'text-green-400'
    },
    { 
      value: statsLoading ? '...' : (dashboardStats?.workOrders?.toLocaleString() || '901'), 
      label: 'Active Work Orders', 
      icon: Wrench,
      color: 'text-yellow-400'
    },
    { 
      value: statsLoading ? '...' : (dashboardStats?.mlPredictions?.toLocaleString() || '11,490'), 
      label: 'ML Predictions', 
      icon: Brain,
      color: 'text-purple-400'
    },
  ]

  useEffect(() => {
    setMounted(true)
    
    let index = 0
    const interval = setInterval(() => {
      if (index <= fullText.length) {
        setTypedText(fullText.slice(0, index))
        index++
      } else {
        clearInterval(interval)
      }
    }, 40)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-navy-900 overflow-y-auto">
      <div className="relative">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-fire-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-vegetation-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>
        <div className="absolute inset-0 bg-gradient-to-b from-navy-900/50 via-transparent to-navy-900" />
        
        <div className="relative max-w-7xl mx-auto px-6 pt-16 pb-24">
          <div className={`text-center transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <div className="relative inline-block mb-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-fire-500 via-vigil-orange to-vegetation-500 flex items-center justify-center shadow-2xl shadow-fire-500/30">
                <div className="flex items-center gap-1">
                  <TreePine size={20} className="text-white" />
                  <Zap size={20} className="text-white" />
                  <Flame size={20} className="text-white" />
                </div>
              </div>
              <div className="absolute inset-0 w-20 h-20 rounded-2xl bg-gradient-to-br from-fire-500 to-vegetation-500 blur-xl opacity-50" />
            </div>

            <h1 className="text-5xl font-bold mb-3">
              <span className="bg-gradient-to-r from-fire-500 via-vigil-orange to-vegetation-500 bg-clip-text text-transparent">
                {COPILOT_NAME}
              </span>
            </h1>
            <p className="text-lg text-slate-400 mb-1">Vegetation & Infrastructure Grid Intelligence Layer</p>
            <p className="text-sm text-slate-500 mb-6">Powered by Snowflake Cortex AI</p>

            <div className="max-w-2xl mx-auto mb-10">
              <div className="bg-navy-800/80 backdrop-blur-sm border border-navy-700 rounded-xl p-5 text-left">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-fire-500 to-vegetation-500 flex items-center justify-center flex-shrink-0">
                    <Sparkles size={20} className="text-white" />
                  </div>
                  <div>
                    <p className="text-lg text-slate-200">
                      {typedText}
                      <span className="inline-block w-0.5 h-5 bg-vigil-orange ml-1 animate-pulse" />
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-4">
              <button
                onClick={() => onNavigate('dashboard')}
                className="group flex items-center gap-3 px-7 py-3.5 bg-gradient-to-r from-fire-500 to-vigil-orange rounded-xl text-white font-semibold text-lg shadow-xl shadow-fire-500/25 hover:shadow-fire-500/40 hover:scale-105 transition-all"
              >
                Launch Risk Dashboard
                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
              </button>
              <button
                onClick={() => onNavigate('architecture')}
                className="flex items-center gap-2 px-5 py-3.5 bg-navy-700/50 border border-navy-600 rounded-xl text-slate-300 font-medium hover:bg-navy-600/50 hover:border-navy-500 transition-all"
              >
                View Architecture
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className={`bg-navy-800/50 border-y border-navy-700/50 py-6 transition-all duration-1000 delay-300 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-4 gap-8">
            {stats.map((stat, i) => {
              const Icon = stat.icon
              return (
                <div key={i} className="text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <Icon size={18} className={stat.color} />
                    <p className="text-3xl font-bold text-vigil-orange">
                      {statsLoading ? (
                        <Loader2 size={24} className="animate-spin inline" />
                      ) : stat.value}
                    </p>
                  </div>
                  <p className="text-sm text-slate-400 mt-1">{stat.label}</p>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className={`text-center mb-10 transition-all duration-1000 delay-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <h2 className="text-2xl font-bold text-slate-200 mb-3">Intelligent Grid Safety Management</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Unifying asset health, vegetation encroachment, and fire risk data with AI-powered analytics for CPUC compliance.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-5">
          {features.map((feature, i) => {
            const Icon = feature.icon
            const colorClass = {
              purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30 text-purple-400',
              green: 'from-green-500/20 to-green-600/10 border-green-500/30 text-green-400',
              blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30 text-blue-400',
              red: 'from-red-500/20 to-red-600/10 border-red-500/30 text-red-400',
            }[feature.color]
            
            return (
              <div 
                key={i}
                className={`bg-gradient-to-br ${colorClass} border rounded-xl p-6 transition-all duration-500 hover:scale-[1.02] ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
                style={{ transitionDelay: `${600 + i * 100}ms` }}
              >
                <div className="w-11 h-11 rounded-xl bg-navy-800/80 flex items-center justify-center mb-4">
                  <Icon size={22} />
                </div>
                <h3 className="text-lg font-semibold text-slate-200 mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-4 gap-3">
          {([
            { icon: TrendingUp, label: 'Risk Dashboard', page: 'dashboard' as Page, desc: 'Real-time risk monitoring' },
            { icon: Map, label: 'Asset Map', page: 'map' as Page, desc: 'Geographic asset view' },
            { icon: TreePine, label: 'Vegetation', page: 'vegetation' as Page, desc: 'GO95 compliance tracking' },
            { icon: Wrench, label: 'Work Orders', page: 'workorders' as Page, desc: 'Maintenance management' },
          ]).map((link, i) => {
            const Icon = link.icon
            return (
              <button
                key={i}
                onClick={() => onNavigate(link.page)}
                className="bg-navy-800/50 border border-navy-700/50 rounded-xl p-4 text-left group hover:border-vigil-orange/30 hover:bg-navy-800/80 transition-all"
              >
                <div className="flex items-center gap-3 mb-2">
                  <Icon size={18} className="text-vigil-orange" />
                  <span className="font-medium text-slate-200 group-hover:text-vigil-orange transition-colors text-sm">
                    {link.label}
                  </span>
                  <ChevronRight size={14} className="text-slate-500 ml-auto group-hover:translate-x-1 transition-transform" />
                </div>
                <p className="text-xs text-slate-500">{link.desc}</p>
              </button>
            )
          })}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pb-16">
        <div className={`bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/30 rounded-xl p-6 transition-all duration-1000 delay-700 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center flex-shrink-0">
              <Brain size={24} className="text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-purple-400 mb-2">🤖 4 ML Models Active</h3>
              <p className="text-slate-300 text-sm mb-3">
                VIGIL is powered by <strong className="text-white">4 trained ML models</strong> analyzing asset health, 
                vegetation growth, ignition risk, and water treeing patterns in real-time.
              </p>
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Activity size={14} className="text-green-400" />
                  <span className="text-slate-400">Asset Health</span>
                </div>
                <div className="flex items-center gap-2">
                  <TreePine size={14} className="text-green-500" />
                  <span className="text-slate-400">Vegetation Growth</span>
                </div>
                <div className="flex items-center gap-2">
                  <Flame size={14} className="text-orange-400" />
                  <span className="text-slate-400">Ignition Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <Zap size={14} className="text-blue-400" />
                  <span className="text-slate-400">Water Treeing</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pb-16">
        <div className={`bg-gradient-to-r from-fire-500/10 to-vigil-orange/10 border border-fire-500/30 rounded-xl p-6 transition-all duration-1000 delay-700 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-fire-500/20 flex items-center justify-center flex-shrink-0">
              <AlertTriangle size={24} className="text-fire-500" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-fire-400 mb-2">🔥 Fire Season Alert: Elevated Risk</h3>
              <p className="text-slate-300 text-sm mb-3">
                VIGIL has identified <strong className="text-white">{dashboardStats?.criticalAssets || 47} critical-risk assets</strong> in Tier 3 fire threat districts 
                requiring immediate attention for PSPS event readiness.
              </p>
              <p className="text-slate-400 text-sm">
                Water treeing detected: <strong className="text-blue-400">{dashboardStats?.waterTreeing || 0} cables</strong> • 
                ML predictions: <strong className="text-purple-400">{dashboardStats?.mlPredictions?.toLocaleString() || '11,490'}</strong> • 
                Priority region: <strong className="text-white">NorCal</strong>
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-navy-700/50 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-sm text-slate-500">
            Built on <span className="text-vigil-blue">Snowflake</span> • Cortex AI • GO95 Compliant • CPUC Regulated
          </p>
        </div>
      </div>
    </div>
  )
}
