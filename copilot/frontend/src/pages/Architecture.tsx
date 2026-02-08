import { useState, useEffect } from 'react'
import { Database, Cloud, Brain, Cpu, TreePine, Zap, Flame, Shield, ArrowRight, CheckCircle } from 'lucide-react'


export function Architecture() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const layers = [
    {
      title: 'Data Sources',
      color: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
      icon: Database,
      items: [
        { name: 'Asset Registry', desc: '5,000+ grid assets' },
        { name: 'Vegetation Data', desc: 'GO95 encroachment points' },
        { name: 'Risk Assessments', desc: 'ML-scored risk tiers' },
        { name: 'Work Orders', desc: 'Maintenance tracking' },
        { name: 'Weather/Fire Data', desc: 'Real-time conditions' },
      ]
    },
    {
      title: 'Snowflake Data Cloud',
      color: 'from-cyan-500/20 to-cyan-600/10 border-cyan-500/30',
      icon: Cloud,
      items: [
        { name: 'Snowflake Tables', desc: 'Structured data storage' },
        { name: 'Dynamic Tables', desc: 'Real-time transformations' },
        { name: 'Cortex Search', desc: 'Document retrieval' },
        { name: 'SPCS', desc: 'Container services' },
      ]
    },
    {
      title: 'AI/ML Layer',
      color: 'from-purple-500/20 to-purple-600/10 border-purple-500/30',
      icon: Brain,
      items: [
        { name: 'Cortex LLM', desc: 'Natural language processing' },
        { name: 'Risk Scoring ML', desc: 'Composite risk calculation' },
        { name: 'Growth Prediction', desc: 'Vegetation growth models' },
        { name: 'VIGIL Agent', desc: 'Intelligent copilot' },
      ]
    },
    {
      title: 'Application Layer',
      color: 'from-orange-500/20 to-orange-600/10 border-orange-500/30',
      icon: Cpu,
      items: [
        { name: 'React Frontend', desc: 'Interactive dashboard' },
        { name: 'FastAPI Backend', desc: 'REST API services' },
        { name: '3D Map Visualization', desc: 'deck.gl + MapLibre' },
        { name: 'Real-time Streaming', desc: 'SSE for copilot' },
      ]
    },
  ]

  const capabilities = [
    { icon: Flame, title: 'Fire Risk Intelligence', desc: 'PSPS threat assessment with ignition probability scoring' },
    { icon: TreePine, title: 'Vegetation Compliance', desc: 'GO95 tracking with automated scheduling' },
    { icon: Zap, title: 'Asset Health', desc: 'Condition monitoring and failure prediction' },
    { icon: Shield, title: 'Regulatory Compliance', desc: 'CPUC audit-ready reporting' },
  ]

  return (
    <div className="h-full overflow-auto bg-navy-950 p-6">
      <div className="max-w-6xl mx-auto">
        <div className={`text-center mb-10 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <h1 className="text-3xl font-bold text-white mb-3">VIGIL Architecture</h1>
          <p className="text-slate-400 max-w-2xl mx-auto">
            End-to-end grid intelligence platform built on Snowflake, powered by Cortex AI
          </p>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-10">
          {layers.map((layer, i) => {
            const Icon = layer.icon
            return (
              <div 
                key={i}
                className={`bg-gradient-to-br ${layer.color} border rounded-xl p-4 transition-all duration-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
                style={{ transitionDelay: `${i * 100}ms` }}
              >
                <div className="flex items-center gap-2 mb-4">
                  <Icon size={20} className="text-white" />
                  <h3 className="font-semibold text-white">{layer.title}</h3>
                </div>
                <div className="space-y-2">
                  {layer.items.map((item, j) => (
                    <div key={j} className="bg-navy-900/50 rounded-lg px-3 py-2">
                      <div className="text-sm text-white font-medium">{item.name}</div>
                      <div className="text-xs text-slate-400">{item.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        <div className="flex items-center justify-center gap-4 mb-10">
          {[0, 1, 2].map(i => (
            <ArrowRight key={i} size={24} className={`text-slate-600 transition-all duration-500 ${mounted ? 'opacity-100' : 'opacity-0'}`} style={{ transitionDelay: `${400 + i * 100}ms` }} />
          ))}
        </div>

        <div className={`bg-navy-800/50 border border-navy-700 rounded-xl p-6 mb-10 transition-all duration-700 delay-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <h3 className="text-lg font-semibold text-white mb-4 text-center">Key Capabilities</h3>
          <div className="grid grid-cols-4 gap-4">
            {capabilities.map((cap, i) => {
              const Icon = cap.icon
              return (
                <div key={i} className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-vigil-orange/20 flex items-center justify-center flex-shrink-0">
                    <Icon size={20} className="text-vigil-orange" />
                  </div>
                  <div>
                    <div className="text-white font-medium text-sm">{cap.title}</div>
                    <div className="text-slate-400 text-xs">{cap.desc}</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className={`bg-gradient-to-r from-vigil-green/10 to-vigil-blue/10 border border-vigil-green/30 rounded-xl p-6 transition-all duration-700 delay-700 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
          <div className="flex items-start gap-4">
            <CheckCircle size={24} className="text-vigil-green flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Built for Enterprise Scale</h3>
              <p className="text-slate-300 text-sm mb-3">
                VIGIL leverages Snowflake's enterprise capabilities for security, scalability, and governance.
              </p>
              <div className="flex flex-wrap gap-2">
                {['SOC 2 Compliant', 'RBAC Security', 'Audit Logging', 'Data Lineage', 'Multi-region', 'Auto-scaling'].map((tag, i) => (
                  <span key={i} className="px-2 py-1 bg-navy-800 rounded text-xs text-slate-300">{tag}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
