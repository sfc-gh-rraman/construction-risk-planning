import { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Database, 
  Cloud, 
  Brain, 
  Cpu, 
  TreePine, 
  Zap, 
  Flame, 
  Shield, 
  ArrowRight, 
  CheckCircle,
  Activity,
  Loader2,
  GitBranch,
  Workflow,
  Sparkles
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function getMLSummary() {
  const res = await fetch(`${API_BASE}/ml/summary`)
  if (!res.ok) throw new Error('Failed')
  return res.json()
}

interface DataFlowPacket {
  id: number
  from: number
  to: number
  type: 'data' | 'ml' | 'query' | 'result'
}

function AnimatedDataFlow() {
  const [packets, setPackets] = useState<DataFlowPacket[]>([])
  const [packetId, setPacketId] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      const types: DataFlowPacket['type'][] = ['data', 'ml', 'query', 'result']
      const newPacket: DataFlowPacket = {
        id: packetId,
        from: Math.floor(Math.random() * 3),
        to: Math.floor(Math.random() * 3) + 1,
        type: types[Math.floor(Math.random() * types.length)]
      }
      setPacketId(p => p + 1)
      setPackets(prev => [...prev.slice(-5), newPacket])
    }, 800)

    return () => clearInterval(interval)
  }, [packetId])

  const getPacketColor = (type: DataFlowPacket['type']) => {
    switch (type) {
      case 'data': return 'bg-blue-500'
      case 'ml': return 'bg-purple-500'
      case 'query': return 'bg-orange-500'
      case 'result': return 'bg-green-500'
    }
  }

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      <AnimatePresence>
        {packets.map((packet) => (
          <motion.div
            key={packet.id}
            initial={{ x: `${packet.from * 25 + 12}%`, y: '100%', opacity: 0, scale: 0.5 }}
            animate={{ x: `${packet.to * 25 + 12}%`, y: '-10%', opacity: [0, 1, 1, 0], scale: [0.5, 1, 1, 0.5] }}
            exit={{ opacity: 0 }}
            transition={{ duration: 2, ease: "easeInOut" }}
            className={`absolute w-3 h-3 rounded-full ${getPacketColor(packet.type)} shadow-lg`}
            style={{ boxShadow: `0 0 10px currentColor` }}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}

function LiveQueryCounter({ count, label }: { count: number; label: string }) {
  const [displayCount, setDisplayCount] = useState(0)
  
  useEffect(() => {
    const interval = setInterval(() => {
      setDisplayCount(prev => {
        if (prev < count) return prev + Math.ceil((count - prev) / 10)
        return count
      })
    }, 50)
    return () => clearInterval(interval)
  }, [count])

  return (
    <div className="flex items-center gap-2 text-xs">
      <Activity size={12} className="text-green-400 animate-pulse" />
      <span className="font-mono text-green-400">{displayCount.toLocaleString()}</span>
      <span className="text-slate-500">{label}</span>
    </div>
  )
}

export function Architecture() {
  const [mounted, setMounted] = useState(false)
  const [activeLayer, setActiveLayer] = useState<number | null>(null)

  const { data: mlData } = useQuery({
    queryKey: ['mlSummary'],
    queryFn: getMLSummary,
    refetchInterval: 30000
  })

  useEffect(() => {
    setMounted(true)
  }, [])

  const totalPredictions = useMemo(() => {
    if (!mlData?.models) return 0
    return Object.values(mlData.models).reduce((acc: number, m: any) => acc + (m.total_predictions || 0), 0)
  }, [mlData])

  const layers = [
    {
      title: 'Data Sources',
      color: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
      activeColor: 'from-blue-500/40 to-blue-600/20 border-blue-500/60',
      icon: Database,
      liveCount: 5000,
      items: [
        { name: 'Asset Registry', desc: '5,000+ grid assets', live: true },
        { name: 'Vegetation Data', desc: 'GO95 encroachment points', live: true },
        { name: 'Risk Assessments', desc: 'ML-scored risk tiers', live: true },
        { name: 'Work Orders', desc: 'Maintenance tracking', live: false },
        { name: 'Weather/Fire Data', desc: 'Real-time conditions', live: true },
      ]
    },
    {
      title: 'Snowflake Data Cloud',
      color: 'from-cyan-500/20 to-cyan-600/10 border-cyan-500/30',
      activeColor: 'from-cyan-500/40 to-cyan-600/20 border-cyan-500/60',
      icon: Cloud,
      liveCount: 12,
      items: [
        { name: 'Snowflake Tables', desc: '12 source tables', live: true },
        { name: 'Dynamic Tables', desc: 'Real-time ML aggregation', live: true },
        { name: 'Cortex Search', desc: 'GO95 document retrieval', live: false },
        { name: 'SPCS', desc: 'Container services', live: false },
      ]
    },
    {
      title: 'AI/ML Layer',
      color: 'from-purple-500/20 to-purple-600/10 border-purple-500/30',
      activeColor: 'from-purple-500/40 to-purple-600/20 border-purple-500/60',
      icon: Brain,
      liveCount: totalPredictions,
      items: [
        { name: 'Asset Health Model', desc: 'GradientBoostingRegressor', live: true },
        { name: 'Vegetation Growth', desc: 'RandomForestRegressor', live: true },
        { name: 'Ignition Risk', desc: 'GradientBoostingClassifier', live: true },
        { name: 'Water Treeing', desc: 'Correlation Analysis', live: true },
      ]
    },
    {
      title: 'Application Layer',
      color: 'from-orange-500/20 to-orange-600/10 border-orange-500/30',
      activeColor: 'from-orange-500/40 to-orange-600/20 border-orange-500/60',
      icon: Cpu,
      liveCount: 8,
      items: [
        { name: 'React Frontend', desc: 'Interactive dashboard', live: true },
        { name: 'FastAPI Backend', desc: 'REST API services', live: true },
        { name: '3D Map (deck.gl)', desc: 'Hexbin visualization', live: true },
        { name: 'Cortex Agent', desc: 'Multi-persona copilot', live: true },
      ]
    },
  ]

  const capabilities = [
    { icon: Flame, title: 'Fire Risk Intelligence', desc: 'PSPS threat assessment with ignition probability scoring', color: 'text-orange-400' },
    { icon: TreePine, title: 'Vegetation Compliance', desc: 'GO95 tracking with automated scheduling', color: 'text-green-400' },
    { icon: Zap, title: 'Asset Health', desc: 'Condition monitoring and failure prediction', color: 'text-blue-400' },
    { icon: Shield, title: 'Regulatory Compliance', desc: 'CPUC audit-ready reporting', color: 'text-purple-400' },
  ]

  return (
    <div className="h-full overflow-auto bg-navy-950 p-6">
      <div className="max-w-6xl mx-auto relative">
        <AnimatedDataFlow />
        
        <div className={`text-center mb-10 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <div className="flex items-center justify-center gap-3 mb-3">
            <Workflow size={32} className="text-purple-400" />
            <h1 className="text-3xl font-bold text-white">VIGIL Architecture</h1>
          </div>
          <p className="text-slate-400 max-w-2xl mx-auto">
            End-to-end grid intelligence platform built on Snowflake, powered by Cortex AI
          </p>
          <div className="flex items-center justify-center gap-6 mt-4">
            <LiveQueryCounter count={totalPredictions} label="ML predictions" />
            <LiveQueryCounter count={5000} label="assets monitored" />
            <LiveQueryCounter count={4} label="active models" />
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-6 relative">
          {layers.map((layer, i) => {
            const Icon = layer.icon
            const isActive = activeLayer === i
            return (
              <motion.div 
                key={i}
                className={`bg-gradient-to-br ${isActive ? layer.activeColor : layer.color} border rounded-xl p-4 cursor-pointer transition-all duration-300`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: mounted ? 1 : 0, y: mounted ? 0 : 20 }}
                transition={{ delay: i * 0.1 }}
                onMouseEnter={() => setActiveLayer(i)}
                onMouseLeave={() => setActiveLayer(null)}
                whileHover={{ scale: 1.02 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Icon size={20} className="text-white" />
                    <h3 className="font-semibold text-white">{layer.title}</h3>
                  </div>
                  {layer.liveCount > 0 && (
                    <div className="flex items-center gap-1 text-xs bg-black/20 px-2 py-0.5 rounded-full">
                      <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                      <span className="text-green-400 font-mono">{layer.liveCount.toLocaleString()}</span>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  {layer.items.map((item, j) => (
                    <motion.div 
                      key={j} 
                      className="bg-navy-900/50 rounded-lg px-3 py-2 flex items-center justify-between"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 + j * 0.05 }}
                    >
                      <div>
                        <div className="text-sm text-white font-medium flex items-center gap-2">
                          {item.name}
                          {item.live && <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />}
                        </div>
                        <div className="text-xs text-slate-400">{item.desc}</div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )
          })}
        </div>

        <div className="flex items-center justify-center gap-2 mb-6">
          {[0, 1, 2].map(i => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: mounted ? 1 : 0, scale: mounted ? 1 : 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
            >
              <ArrowRight size={24} className="text-slate-600" />
            </motion.div>
          ))}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 border border-purple-500/30 rounded-full"
          >
            <Sparkles size={16} className="text-purple-400" />
            <span className="text-sm text-purple-300">Data flows in real-time</span>
          </motion.div>
        </div>

        <motion.div 
          className="bg-navy-800/50 border border-navy-700 rounded-xl p-6 mb-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: mounted ? 1 : 0, y: mounted ? 0 : 20 }}
          transition={{ delay: 0.6 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 text-center flex items-center justify-center gap-2">
            <GitBranch size={20} className="text-purple-400" />
            Key Capabilities
          </h3>
          <div className="grid grid-cols-4 gap-4">
            {capabilities.map((cap, i) => {
              const Icon = cap.icon
              return (
                <motion.div 
                  key={i} 
                  className="flex items-start gap-3 bg-navy-900/30 rounded-lg p-3"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 + i * 0.1 }}
                  whileHover={{ scale: 1.02 }}
                >
                  <div className={`w-10 h-10 rounded-lg bg-navy-800 flex items-center justify-center flex-shrink-0`}>
                    <Icon size={20} className={cap.color} />
                  </div>
                  <div>
                    <div className="text-white font-medium text-sm">{cap.title}</div>
                    <div className="text-slate-400 text-xs">{cap.desc}</div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </motion.div>

        <motion.div 
          className="bg-gradient-to-r from-vigil-green/10 to-vigil-blue/10 border border-vigil-green/30 rounded-xl p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: mounted ? 1 : 0 }}
          transition={{ delay: 0.9 }}
        >
          <div className="flex items-start gap-4">
            <CheckCircle size={24} className="text-vigil-green flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Built for Enterprise Scale</h3>
              <p className="text-slate-300 text-sm mb-3">
                VIGIL leverages Snowflake's enterprise capabilities for security, scalability, and governance.
              </p>
              <div className="flex flex-wrap gap-2">
                {['SOC 2 Compliant', 'RBAC Security', 'Audit Logging', 'Data Lineage', 'Multi-region', 'Auto-scaling'].map((tag, i) => (
                  <motion.span 
                    key={i} 
                    className="px-2 py-1 bg-navy-800 rounded text-xs text-slate-300"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1 + i * 0.05 }}
                  >
                    {tag}
                  </motion.span>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
