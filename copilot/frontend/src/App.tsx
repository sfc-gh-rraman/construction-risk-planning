import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './components/Layout'
import { 
  Landing,
  RiskDashboard, 
  AssetMap, 
  Vegetation, 
  WorkOrders,
  AssetRegistry,
  Architecture,
  MLPredictions
} from './pages'

export type Page = 'landing' | 'dashboard' | 'map' | 'vegetation' | 'workorders' | 'assets' | 'architecture' | 'ml'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('landing')

  if (currentPage === 'landing') {
    return (
      <QueryClientProvider client={queryClient}>
        <Landing onNavigate={setCurrentPage} />
      </QueryClientProvider>
    )
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <RiskDashboard />
      case 'map':
        return <AssetMap />
      case 'vegetation':
        return <Vegetation />
      case 'workorders':
        return <WorkOrders />
      case 'assets':
        return <AssetRegistry />
      case 'architecture':
        return <Architecture />
      case 'ml':
        return <MLPredictions />
      default:
        return <RiskDashboard />
    }
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Layout currentPage={currentPage} onNavigate={setCurrentPage}>
        {renderPage()}
      </Layout>
    </QueryClientProvider>
  )
}

export default App
