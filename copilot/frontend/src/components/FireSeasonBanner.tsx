// VIGIL Risk Planning - Fire Season Banner Component

import { FireSeasonStatus } from '../types';
import { motion } from 'framer-motion';

interface FireSeasonBannerProps {
  fireStatus: FireSeasonStatus | null;
  loading?: boolean;
}

export function FireSeasonBanner({ fireStatus, loading }: FireSeasonBannerProps) {
  if (loading || !fireStatus) {
    return (
      <div className="fire-banner py-3 px-6">
        <div className="flex items-center justify-center gap-3">
          <span className="text-white/70 loading-dots">Loading fire season status</span>
        </div>
      </div>
    );
  }

  const isActive = fireStatus.status === 'ACTIVE';
  const daysCount = isActive ? fireStatus.days_remaining : fireStatus.days_until_fire_season;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`py-3 px-6 ${isActive ? 'fire-banner' : 'bg-gradient-to-r from-amber-600 to-orange-500'}`}
    >
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{isActive ? '🔥' : '⚠️'}</span>
          <div>
            <h2 className="text-white font-bold text-lg">
              {isActive ? 'FIRE SEASON ACTIVE' : 'Pre-Fire Season'}
            </h2>
            <p className="text-white/80 text-sm">
              {isActive 
                ? 'Enhanced monitoring and mitigation protocols in effect'
                : 'Preparation window for vegetation management'
              }
            </p>
          </div>
        </div>

        <motion.div
          key={daysCount}
          initial={{ scale: 1.2, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="flex items-center gap-4"
        >
          <div className="text-center">
            <div className="text-4xl font-bold text-white drop-shadow-lg">
              {daysCount ?? '—'}
            </div>
            <div className="text-white/80 text-sm uppercase tracking-wider">
              {isActive ? 'Days Remaining' : 'Days Until Fire Season'}
            </div>
          </div>
          
          {!isActive && fireStatus.fire_season_start && (
            <div className="text-right">
              <div className="text-white/60 text-xs">Season Starts</div>
              <div className="text-white font-semibold">
                {new Date(fireStatus.fire_season_start).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric'
                })}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}
