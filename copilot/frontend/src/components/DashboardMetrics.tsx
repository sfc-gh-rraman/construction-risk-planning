// VIGIL Risk Planning - Dashboard Metrics Component

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { DashboardMetrics, RISK_TIER_COLORS, REGIONS } from '../types';

interface DashboardMetricsProps {
  metrics: DashboardMetrics | null;
  selectedRegion: string;
  onRegionChange: (region: string) => void;
  loading?: boolean;
}

export function DashboardMetricsPanel({ 
  metrics, 
  selectedRegion, 
  onRegionChange,
  loading 
}: DashboardMetricsProps) {
  const summaryStats = useMemo(() => {
    if (!metrics) return null;

    const assetSummary = metrics.asset_summary;
    const riskSummary = metrics.risk_summary;
    const complianceSummary = metrics.compliance_summary;

    // Filter by region if selected
    const filterByRegion = <T extends { REGION: string }>(data: T[]) => {
      if (selectedRegion === 'All') return data;
      return data.filter(d => d.REGION === selectedRegion);
    };

    const filteredAssets = filterByRegion(assetSummary);
    const filteredRisk = filterByRegion(riskSummary);
    const filteredCompliance = filterByRegion(complianceSummary);

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
      avgReplacementCost: filteredAssets.reduce((sum, a) => sum + (a.TOTAL_REPLACEMENT_COST || 0), 0),
    };
  }, [metrics, selectedRegion]);

  if (loading || !summaryStats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-gray-800 rounded-xl h-24" />
        ))}
      </div>
    );
  }

  const stats = [
    {
      label: 'Total Assets',
      value: summaryStats.totalAssets.toLocaleString(),
      icon: '⚡',
      color: 'text-blue-400',
    },
    {
      label: 'Critical Risk',
      value: summaryStats.criticalRiskAssets.toLocaleString(),
      icon: '🔴',
      color: 'text-red-500',
      alert: summaryStats.criticalRiskAssets > 0,
    },
    {
      label: 'High Risk',
      value: summaryStats.highRiskAssets.toLocaleString(),
      icon: '🟠',
      color: 'text-orange-500',
    },
    {
      label: 'Non-Compliant',
      value: summaryStats.outOfCompliance.toLocaleString(),
      icon: '🌳',
      color: 'text-amber-400',
    },
    {
      label: 'Poor Condition',
      value: summaryStats.poorConditionAssets.toLocaleString(),
      icon: '⚠️',
      color: 'text-yellow-500',
    },
    {
      label: 'Est. Trim Cost',
      value: `$${(summaryStats.totalTrimCost / 1e6).toFixed(1)}M`,
      icon: '💰',
      color: 'text-green-400',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Region Selector */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        <span className="text-gray-400 text-sm whitespace-nowrap">Region:</span>
        <button
          onClick={() => onRegionChange('All')}
          className={`px-3 py-1 rounded-full text-sm transition-colors ${
            selectedRegion === 'All'
              ? 'bg-vigil-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          All
        </button>
        {REGIONS.map(region => (
          <button
            key={region}
            onClick={() => onRegionChange(region)}
            className={`px-3 py-1 rounded-full text-sm whitespace-nowrap transition-colors ${
              selectedRegion === region
                ? 'bg-vigil-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {region}
          </button>
        ))}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`bg-gray-800/80 rounded-xl p-4 border ${
              stat.alert ? 'border-red-500/50 animate-pulse' : 'border-gray-700'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{stat.icon}</span>
              <span className="text-xs text-gray-400 uppercase tracking-wider">
                {stat.label}
              </span>
            </div>
            <div className={`text-2xl font-bold ${stat.color}`}>
              {stat.value}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Risk Distribution by Region */}
      {metrics && selectedRegion === 'All' && (
        <div className="bg-gray-800/80 rounded-xl p-4 border border-gray-700">
          <h4 className="text-sm font-semibold text-gray-400 uppercase mb-3">
            Risk Distribution by Region
          </h4>
          <div className="space-y-2">
            {REGIONS.map(region => {
              const regionRisk = metrics.risk_summary.filter(r => r.REGION === region);
              const total = regionRisk.reduce((sum, r) => sum + r.ASSET_COUNT, 0);
              if (total === 0) return null;

              return (
                <div key={region} className="flex items-center gap-3">
                  <span className="w-20 text-sm text-gray-300">{region}</span>
                  <div className="flex-1 h-4 bg-gray-700 rounded-full overflow-hidden flex">
                    {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(tier => {
                      const tierData = regionRisk.find(r => r.RISK_TIER === tier);
                      const pct = tierData ? (tierData.ASSET_COUNT / total) * 100 : 0;
                      return (
                        <div
                          key={tier}
                          style={{ 
                            width: `${pct}%`,
                            backgroundColor: RISK_TIER_COLORS[tier]
                          }}
                          className="h-full transition-all duration-500"
                          title={`${tier}: ${tierData?.ASSET_COUNT || 0}`}
                        />
                      );
                    })}
                  </div>
                  <span className="w-16 text-right text-sm text-gray-400">
                    {total.toLocaleString()}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
