import { 
  LayoutDashboard, 
  Map, 
  TreePine, 
  Wrench, 
  FileText,
  Cpu,
  ChevronLeft,
  ChevronRight,
  Activity,
  Flame
} from 'lucide-react'
import { useState } from 'react'
import type { Page } from '../App'

interface LayoutProps {
  children: React.ReactNode
  currentPage: Page
  onNavigate: (page: Page) => void
}

const navItems = [
  { id: 'dashboard' as Page, label: 'Risk Dashboard', icon: LayoutDashboard },
  { id: 'map' as Page, label: 'Asset Map', icon: Map },
  { id: 'vegetation' as Page, label: 'Vegetation', icon: TreePine },
  { id: 'workorders' as Page, label: 'Work Orders', icon: Wrench },
  { id: 'assets' as Page, label: 'Asset Registry', icon: FileText },
  { id: 'architecture' as Page, label: 'Architecture', icon: Cpu },
]

export function Layout({ children, currentPage, onNavigate }: LayoutProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <div className="h-screen flex overflow-hidden bg-navy-950">
      <aside 
        className={`
          ${isCollapsed ? 'w-16' : 'w-64'} 
          flex-shrink-0 bg-navy-900 border-r border-navy-700/50 
          flex flex-col transition-all duration-300
        `}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-navy-700/50">
          {!isCollapsed && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-fire-500 to-vegetation-500 flex items-center justify-center">
                <Flame size={16} className="text-white" />
              </div>
              <div>
                <span className="font-display font-bold text-lg text-white">VIGIL</span>
                <span className="text-xs text-slate-500 block -mt-1">Grid Intelligence</span>
              </div>
            </div>
          )}
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 hover:bg-navy-700 rounded-md text-slate-400 hover:text-white transition-colors"
          >
            {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = currentPage === item.id
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                  transition-all duration-200 group
                  ${isActive 
                    ? 'bg-vigil-orange/10 text-vigil-orange' 
                    : 'text-slate-400 hover:text-white hover:bg-navy-700/50'
                  }
                `}
              >
                <item.icon 
                  size={20} 
                  className={isActive ? 'text-vigil-orange' : 'text-slate-500 group-hover:text-vigil-orange/60'}
                />
                {!isCollapsed && <span>{item.label}</span>}
                {isActive && !isCollapsed && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-vigil-orange" />
                )}
              </button>
            )
          })}
        </nav>

        <div className="p-4 border-t border-navy-700/50">
          {!isCollapsed ? (
            <div className="text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-500">System Status</span>
                <span className="flex items-center gap-1 text-vigil-green">
                  <Activity size={12} />
                  Online
                </span>
              </div>
              <div className="flex items-center gap-2 text-slate-500">
                <div className="flex -space-x-1">
                  <div className="w-2 h-2 rounded-full bg-vigil-green" />
                  <div className="w-2 h-2 rounded-full bg-vigil-green" />
                  <div className="w-2 h-2 rounded-full bg-vigil-green" />
                </div>
                <span>3 Agents Active</span>
              </div>
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="w-2 h-2 rounded-full bg-vigil-green animate-pulse" />
            </div>
          )}
        </div>
      </aside>

      <main className="flex-1 overflow-hidden flex flex-col">
        <header className="h-14 flex-shrink-0 border-b border-navy-700/50 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <h1 className="font-display font-semibold text-lg text-white">
              {navItems.find(n => n.id === currentPage)?.label || 'VIGIL'}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="w-2 h-2 rounded-full bg-vigil-green animate-pulse" />
              Snowflake Cortex Connected
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
