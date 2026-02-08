"""
VIGIL Risk Planning - Fire Risk Analyst Agent

Persona: Urgent voice of wildfire prevention. Speaks with authority about fire districts.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import date

logger = logging.getLogger(__name__)


class FireRiskAnalyst:
    """
    Agent responsible for fire risk assessment and season readiness.
    
    Persona: "Fire season waits for no one."
    
    Capabilities:
    - Fire threat district analysis
    - Ignition risk modeling
    - Fire season readiness scoring
    - PSPS circuit identification
    - Red flag warning response
    """
    
    PERSONA = {
        "name": "Fire Risk Analyst",
        "emoji": "🔥",
        "catchphrase": "Fire season waits for no one.",
        "style": "urgent, authoritative, action-oriented"
    }
    
    def __init__(self, snowflake_service):
        self.sf = snowflake_service
    
    def _get_fire_season_countdown(self) -> Dict[str, Any]:
        """Calculate days until fire season."""
        today = date.today()
        year = today.year
        if today.month >= 6:
            year += 1
        fire_season_start = date(year, 6, 1)
        days = (fire_season_start - today).days
        
        return {
            "days_remaining": days,
            "start_date": fire_season_start.isoformat(),
            "urgency": "critical" if days < 30 else "high" if days < 60 else "medium" if days < 90 else "low"
        }
    
    async def get_fire_risk_overview(self) -> Dict[str, Any]:
        """Get comprehensive fire risk overview."""
        
        fire_season = self._get_fire_season_countdown()
        assets = self.sf.get_assets()
        encroachments = self.sf.get_vegetation_encroachments()
        
        # Fire district breakdown
        tier_3_assets = [a for a in assets if a.get("FIRE_THREAT_DISTRICT") == "TIER_3"]
        tier_2_assets = [a for a in assets if a.get("FIRE_THREAT_DISTRICT") == "TIER_2"]
        tier_1_assets = [a for a in assets if a.get("FIRE_THREAT_DISTRICT") == "TIER_1"]
        
        # High risk items in Tier 3
        tier_3_high_risk = [a for a in tier_3_assets if (a.get("RISK_SCORE") or 0) > 70]
        tier_3_non_compliant = [e for e in encroachments if e.get("FIRE_THREAT_DISTRICT") == "TIER_3" and e.get("COMPLIANCE_STATUS") in ("NON_COMPLIANT", "CRITICAL")]
        
        # Urgency indicator
        urgency_emoji = "🔴" if fire_season["days_remaining"] < 30 else "🟠" if fire_season["days_remaining"] < 60 else "🟡"
        
        narrative = f"""## {self.PERSONA['emoji']} Fire Risk Dashboard

### {urgency_emoji} Fire Season Countdown
# **{fire_season['days_remaining']} DAYS** until June 1
{"**⚠️ CRITICAL: Accelerate all Tier 3 work immediately!**" if fire_season['days_remaining'] < 30 else ""}

### Fire Threat District Summary
| District | Assets | High Risk | Non-Compliant Veg |
|----------|--------|-----------|-------------------|
| 🔴 Tier 3 (Extreme) | {len(tier_3_assets)} | {len(tier_3_high_risk)} | {len(tier_3_non_compliant)} |
| 🟠 Tier 2 (Elevated) | {len(tier_2_assets)} | {len([a for a in tier_2_assets if (a.get('RISK_SCORE') or 0) > 70])} | - |
| 🟡 Tier 1 (Moderate) | {len(tier_1_assets)} | - | - |
| ⚪ Non-HFTD | {len(assets) - len(tier_3_assets) - len(tier_2_assets) - len(tier_1_assets)} | - | - |

### Tier 3 Immediate Action Required
"""
        
        # List critical Tier 3 issues
        critical_items = sorted(tier_3_high_risk, key=lambda x: x.get("RISK_SCORE", 0), reverse=True)[:10]
        if critical_items:
            for item in critical_items:
                narrative += f"- **{item.get('ASSET_ID')}** ({item.get('ASSET_TYPE')}): Risk {item.get('RISK_SCORE', 0):.0f}, Health {item.get('HEALTH_SCORE', 0):.0f}\n"
        else:
            narrative += "_No critical Tier 3 items requiring immediate action._\n"
        
        # Readiness score
        compliant_tier_3 = len([e for e in encroachments if e.get("FIRE_THREAT_DISTRICT") == "TIER_3" and e.get("COMPLIANCE_STATUS") == "COMPLIANT"])
        total_tier_3_veg = len([e for e in encroachments if e.get("FIRE_THREAT_DISTRICT") == "TIER_3"])
        readiness_score = (compliant_tier_3 / total_tier_3_veg * 100) if total_tier_3_veg > 0 else 100
        
        narrative += f"""
### Fire Season Readiness
| Metric | Value | Target |
|--------|-------|--------|
| Tier 3 Vegetation Compliance | {readiness_score:.1f}% | 100% |
| Tier 3 High-Risk Assets Mitigated | {len(tier_3_assets) - len(tier_3_high_risk)}/{len(tier_3_assets)} | 100% |
| Days Remaining | {fire_season['days_remaining']} | - |

> _{self.PERSONA['catchphrase']}_
"""
        
        return {
            "narrative": narrative,
            "data": {
                "fire_season": fire_season,
                "tier_3_count": len(tier_3_assets),
                "tier_3_high_risk": len(tier_3_high_risk),
                "tier_3_non_compliant": len(tier_3_non_compliant),
                "readiness_score": readiness_score,
                "critical_assets": critical_items
            },
            "sources": ["ATOMIC.ASSET", "ATOMIC.VEGETATION_ENCROACHMENT", "ML.IGNITION_RISK_PREDICTION"]
        }
    
    async def get_ignition_risk_analysis(self) -> Dict[str, Any]:
        """Get ML-based ignition risk predictions."""
        
        predictions = self.sf.get_ignition_predictions()
        
        # Group by risk tier
        critical = [p for p in predictions if p.get("RISK_TIER") == "CRITICAL"]
        high = [p for p in predictions if p.get("RISK_TIER") == "HIGH"]
        medium = [p for p in predictions if p.get("RISK_TIER") == "MEDIUM"]
        
        narrative = f"""## {self.PERSONA['emoji']} Ignition Risk Predictions

### ML Model Summary
Model: XGBoost Classifier (F1: 0.87)

### Risk Distribution
| Risk Tier | Count | Immediate Action |
|-----------|-------|------------------|
| 🔴 Critical | {len(critical)} | Yes - Same Day |
| 🟠 High | {len(high)} | Yes - 7 Days |
| 🟡 Medium | {len(medium)} | Monitor |
| 🟢 Low | {len(predictions) - len(critical) - len(high) - len(medium)} | Routine |

### Critical Risk Assets (Immediate Action Required)
"""
        
        for p in critical[:10]:
            narrative += f"- **{p.get('ASSET_ID')}**: {p.get('FIRE_THREAT_DISTRICT')} - Probability {(p.get('IGNITION_PROBABILITY') or 0)*100:.0f}%\n"
        
        narrative += """
### Key Risk Factors (SHAP Analysis)
1. **Fire Threat District** (35%) - Tier 3 locations
2. **Vegetation Clearance Deficit** (25%) - Non-compliant clearances
3. **Weather Conditions** (20%) - Wind speed, humidity
4. **Equipment Age** (12%) - Assets >30 years
5. **Historical Failures** (8%) - Prior outages
"""
        
        return {
            "narrative": narrative,
            "data": {
                "predictions": predictions[:100],
                "critical_count": len(critical),
                "high_count": len(high)
            },
            "sources": ["ML.IGNITION_RISK_PREDICTION", "ATOMIC.ASSET"]
        }
    
    async def get_psps_circuits(self) -> Dict[str, Any]:
        """Get circuits likely to require PSPS (Public Safety Power Shutoff)."""
        
        circuits = self.sf.get_circuits()
        
        # Filter to high-risk circuits in fire districts
        psps_candidates = [
            c for c in circuits
            if c.get("FIRE_THREAT_DISTRICT") in ("TIER_3", "TIER_2")
        ]
        
        narrative = f"""## {self.PERSONA['emoji']} PSPS Circuit Analysis

### Summary
- **Total Circuits in Fire Districts**: {len(psps_candidates)}
- **Tier 3 Circuits**: {len([c for c in psps_candidates if c.get('FIRE_THREAT_DISTRICT') == 'TIER_3'])}
- **Customers Potentially Affected**: {sum(c.get('CUSTOMERS_SERVED', 0) or 0 for c in psps_candidates):,}

### High-Priority PSPS Circuits
| Circuit | District | Customers | Critical Facilities |
|---------|----------|-----------|---------------------|
"""
        
        # Sort by customer impact
        psps_candidates.sort(key=lambda x: x.get("CUSTOMERS_SERVED", 0) or 0, reverse=True)
        
        for c in psps_candidates[:15]:
            narrative += f"| {c.get('CIRCUIT_NAME')} | {c.get('FIRE_THREAT_DISTRICT')} | {c.get('CUSTOMERS_SERVED', 0):,} | {c.get('CRITICAL_FACILITIES_COUNT', 0)} |\n"
        
        return {
            "narrative": narrative,
            "data": {
                "psps_circuits": psps_candidates[:50],
                "total_customers": sum(c.get("CUSTOMERS_SERVED", 0) or 0 for c in psps_candidates)
            },
            "sources": ["ATOMIC.CIRCUIT"]
        }
    
    async def get_weather_risk(self) -> Dict[str, Any]:
        """Get current weather risk conditions."""
        
        forecasts = self.sf.get_weather_forecasts()
        
        red_flag = [f for f in forecasts if f.get("RED_FLAG_WARNING")]
        high_wind = [f for f in forecasts if (f.get("WIND_SPEED_MPH") or 0) > 25]
        low_humidity = [f for f in forecasts if (f.get("HUMIDITY_PCT") or 100) < 20]
        
        narrative = f"""## {self.PERSONA['emoji']} Weather Risk Conditions

### Current Alerts
- **Red Flag Warnings**: {len(red_flag)} locations
- **High Wind (>25 mph)**: {len(high_wind)} locations
- **Low Humidity (<20%)**: {len(low_humidity)} locations

### Regional Forecast Summary
| Region | Wind (mph) | Humidity | Fire Weather | Alert |
|--------|------------|----------|--------------|-------|
"""
        
        # Group by region
        by_region = {}
        for f in forecasts:
            region = f.get("REGION", "Unknown")
            if region not in by_region:
                by_region[region] = []
            by_region[region].append(f)
        
        for region, region_forecasts in by_region.items():
            max_wind = max(f.get("WIND_SPEED_MPH", 0) or 0 for f in region_forecasts)
            min_humidity = min(f.get("HUMIDITY_PCT", 100) or 100 for f in region_forecasts)
            has_red_flag = any(f.get("RED_FLAG_WARNING") for f in region_forecasts)
            fire_weather = "🔴 Extreme" if has_red_flag else "🟠 High" if max_wind > 25 or min_humidity < 20 else "🟢 Normal"
            alert = "⚠️ RED FLAG" if has_red_flag else "-"
            narrative += f"| {region} | {max_wind:.0f} | {min_humidity:.0f}% | {fire_weather} | {alert} |\n"
        
        return {
            "narrative": narrative,
            "data": {
                "forecasts": forecasts[:50],
                "red_flag_count": len(red_flag),
                "high_wind_count": len(high_wind)
            },
            "sources": ["ATOMIC.WEATHER_FORECAST"]
        }
