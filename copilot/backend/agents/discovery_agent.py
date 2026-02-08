"""
VIGIL Risk Planning - Water Treeing Detective Agent

THE HIDDEN DISCOVERY: Detecting invisible underground cable degradation.

Persona: Curious data scientist who gets excited about finding patterns others miss.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WaterTreeingDetective:
    """
    Agent responsible for detecting Water Treeing in underground cables.
    
    THE HIDDEN DISCOVERY:
    Water Treeing is a degradation mechanism in XLPE-insulated underground cables
    where moisture infiltrates the insulation over time, creating tree-like structures
    that eventually cause dielectric failure.
    
    KEY INSIGHT: This failure mode is INVISIBLE to routine visual inspections.
    We detect it by correlating AMI (smart meter) voltage anomalies with rainfall.
    
    Cables with Water Treeing show voltage dips that correlate with rain events.
    
    Persona: "The data sees what inspectors can't."
    
    Capabilities:
    - Rain-voltage correlation analysis
    - AMI anomaly detection
    - Cable failure prediction
    - Pattern discovery in sensor data
    """
    
    PERSONA = {
        "name": "Water Treeing Detective",
        "emoji": "🔍",
        "catchphrase": "The data sees what inspectors can't.",
        "style": "analytical, curious, excited about discoveries"
    }
    
    def __init__(self, snowflake_service):
        self.sf = snowflake_service
    
    async def find_water_treeing_pattern(self) -> Dict[str, Any]:
        """
        THE HIDDEN DISCOVERY: Find cables showing Water Treeing indicators.
        
        This is the "wow moment" - detecting invisible cable degradation
        by correlating AMI voltage data with weather patterns.
        """
        
        # Get cable failure predictions with Water Treeing indicators
        cables = self.sf.get_water_treeing_candidates()
        
        # Get AMI readings with rain correlation
        ami_anomalies = self.sf.get_rain_correlated_dips()
        
        # Calculate impact
        affected_cables = len([c for c in cables if c.get("RAIN_CORRELATION_SCORE", 0) > 0.5])
        total_customers = sum(c.get("CUSTOMER_IMPACT_COUNT", 0) or 0 for c in cables if c.get("RAIN_CORRELATION_SCORE", 0) > 0.5)
        total_cost = sum(c.get("ESTIMATED_REPLACEMENT_COST", 0) or 0 for c in cables if c.get("RAIN_CORRELATION_SCORE", 0) > 0.5)
        
        narrative = f"""## {self.PERSONA['emoji']} HIDDEN DISCOVERY: Water Treeing Detection

### ⚡ What We Found
**{affected_cables} underground cables** are showing voltage anomalies that correlate with rainfall.
This pattern indicates **Water Treeing** - moisture-induced insulation degradation that is 
**invisible to visual inspection**.

### Why This Matters
- These cables will **fail catastrophically** within 6-24 months
- **{total_customers:,} customers** are at risk of extended outages
- Estimated replacement cost: **${total_cost/1e6:.1f}M**
- Traditional inspections **cannot detect this** - only data correlation can

### The Pattern
| Material | Moisture | Avg Age | Cables | Rain Correlation |
|----------|----------|---------|--------|------------------|
"""
        
        # Group by material and moisture exposure
        by_group = {}
        for c in cables:
            key = (c.get("MATERIAL", "Unknown"), c.get("MOISTURE_EXPOSURE", "Unknown"))
            if key not in by_group:
                by_group[key] = []
            by_group[key].append(c)
        
        for (material, moisture), group in sorted(by_group.items(), key=lambda x: len(x[1]), reverse=True):
            if len(group) > 0:
                avg_age = sum(c.get("CABLE_AGE_YEARS", 0) or 0 for c in group) / len(group)
                avg_corr = sum(c.get("RAIN_CORRELATION_SCORE", 0) or 0 for c in group) / len(group)
                indicator = "🔴" if material == "XLPE" and moisture == "HIGH" else "🟡"
                narrative += f"| {indicator} {material} | {moisture} | {avg_age:.0f}y | {len(group)} | {avg_corr:.2f} |\n"
        
        narrative += """
### How We Detected This
1. **AMI Data Analysis**: Analyzed voltage readings from smart meters
2. **Weather Correlation**: Correlated voltage dips with rainfall events
3. **ML Pattern Detection**: XGBoost model trained on known failure cases

### Key Risk Indicators
- Cable material: **XLPE** (Cross-linked Polyethylene)
- Age: **15-25 years** (peak failure window)
- Moisture exposure: **HIGH**
- Rain correlation score: **>0.5**

### Top 10 At-Risk Cables
| Asset ID | Age | Rain Corr | Failure Prob | Customers |
|----------|-----|-----------|--------------|-----------|
"""
        
        # Sort by failure probability
        top_risk = sorted(cables, key=lambda x: x.get("FAILURE_PROBABILITY", 0) or 0, reverse=True)[:10]
        for c in top_risk:
            narrative += f"| {c.get('ASSET_ID')} | {c.get('CABLE_AGE_YEARS', 0):.0f}y | {c.get('RAIN_CORRELATION_SCORE', 0):.2f} | {(c.get('FAILURE_PROBABILITY', 0) or 0)*100:.0f}% | {c.get('CUSTOMER_IMPACT_COUNT', 0):,} |\n"
        
        narrative += f"""
### Recommendation
**Immediate Action Required:**
1. Schedule diagnostic testing for all {affected_cables} flagged cables
2. Prioritize replacement of cables with failure probability >70%
3. Install additional monitoring on high-risk segments
4. Budget ${total_cost/1e6:.1f}M for proactive replacement program

> _{self.PERSONA['catchphrase']}_
"""
        
        return {
            "narrative": narrative,
            "data": {
                "affected_cables": affected_cables,
                "total_customers_at_risk": total_customers,
                "total_replacement_cost": total_cost,
                "cables": cables[:50],
                "ami_anomalies": ami_anomalies[:100]
            },
            "sources": ["ATOMIC.AMI_READING", "ML.CABLE_FAILURE_PREDICTION", "ATOMIC.ASSET"],
            "discovery_type": "water_treeing",
            "alert_level": "high"
        }
    
    async def analyze_cable_health(self) -> Dict[str, Any]:
        """Get detailed cable health analysis with Water Treeing focus."""
        
        cables = self.sf.get_underground_cables()
        predictions = self.sf.get_cable_predictions()
        
        total = len(cables)
        xlpe = len([c for c in cables if c.get("MATERIAL") == "XLPE"])
        high_moisture = len([c for c in cables if c.get("MOISTURE_EXPOSURE") == "HIGH"])
        
        # Prediction tiers
        critical = len([p for p in predictions if p.get("RISK_TIER") == "CRITICAL"])
        high = len([p for p in predictions if p.get("RISK_TIER") == "HIGH"])
        
        narrative = f"""## {self.PERSONA['emoji']} Underground Cable Health Analysis

### Cable Inventory
- **Total Underground Cables**: {total}
- **XLPE Insulation**: {xlpe} ({xlpe/total*100:.0f}%)
- **High Moisture Exposure**: {high_moisture} ({high_moisture/total*100:.0f}%)

### Water Treeing Risk Tiers
| Tier | Count | Action Required |
|------|-------|-----------------|
| 🔴 Critical | {critical} | Immediate Replacement |
| 🟠 High | {high} | Schedule Replacement |
| 🟡 Medium | {len([p for p in predictions if p.get('RISK_TIER') == 'MEDIUM'])} | Enhanced Monitoring |
| 🟢 Low | {len([p for p in predictions if p.get('RISK_TIER') == 'LOW'])} | Routine Monitoring |

### Age Distribution (XLPE Cables)
"""
        
        # Age buckets for XLPE cables
        xlpe_cables = [c for c in cables if c.get("MATERIAL") == "XLPE"]
        age_buckets = {
            "0-10 years": len([c for c in xlpe_cables if (c.get("ASSET_AGE_YEARS") or 0) <= 10]),
            "10-15 years": len([c for c in xlpe_cables if 10 < (c.get("ASSET_AGE_YEARS") or 0) <= 15]),
            "15-20 years": len([c for c in xlpe_cables if 15 < (c.get("ASSET_AGE_YEARS") or 0) <= 20]),
            "20-25 years": len([c for c in xlpe_cables if 20 < (c.get("ASSET_AGE_YEARS") or 0) <= 25]),
            "25+ years": len([c for c in xlpe_cables if (c.get("ASSET_AGE_YEARS") or 0) > 25])
        }
        
        narrative += "| Age Range | Count | Water Treeing Risk |\n|-----------|-------|-------------------|\n"
        risk_levels = ["🟢 Low", "🟡 Emerging", "🟠 Moderate", "🔴 High", "🔴 Critical"]
        for (bucket, count), risk in zip(age_buckets.items(), risk_levels):
            narrative += f"| {bucket} | {count} | {risk} |\n"
        
        narrative += """
### Water Treeing Mechanism
Water Treeing occurs when moisture penetrates XLPE insulation through:
1. Manufacturing defects (voids, contaminants)
2. Mechanical damage (installation, dig-ins)
3. Environmental stress (temperature cycling, moisture)

The water creates dendritic (tree-like) structures that progressively 
degrade the dielectric strength until catastrophic failure occurs.

### Detection Method
Traditional inspections cannot see Water Treeing. We detect it by:
- Analyzing voltage readings from downstream AMI meters
- Correlating voltage dips with rainfall events
- ML model trained on historical failure patterns
"""
        
        return {
            "narrative": narrative,
            "data": {
                "total_cables": total,
                "xlpe_count": xlpe,
                "predictions": predictions[:50],
                "age_distribution": age_buckets
            },
            "sources": ["ATOMIC.ASSET", "ML.CABLE_FAILURE_PREDICTION"]
        }
    
    async def get_ami_correlation_analysis(self) -> Dict[str, Any]:
        """Analyze AMI readings for rain-voltage correlation patterns."""
        
        ami_data = self.sf.get_ami_readings()
        
        # Calculate statistics
        total_readings = len(ami_data)
        dip_events = len([a for a in ami_data if a.get("VOLTAGE_DIP_FLAG")])
        rain_correlated = len([a for a in ami_data if a.get("RAIN_CORRELATED_DIP")])
        
        narrative = f"""## {self.PERSONA['emoji']} AMI Voltage Analysis

### Reading Statistics
- **Total AMI Readings Analyzed**: {total_readings:,}
- **Voltage Dip Events**: {dip_events:,} ({dip_events/total_readings*100:.2f}%)
- **Rain-Correlated Dips**: {rain_correlated:,} ({rain_correlated/total_readings*100:.2f}%)

### Correlation Analysis
When we see voltage dips that consistently occur during or shortly after 
rainfall events on the same cable segment, it's a strong indicator of 
moisture ingress - the hallmark of Water Treeing.

### Assets with Highest Rain Correlation
| Asset ID | Dip Events | Rain Correlated | Correlation % |
|----------|------------|-----------------|---------------|
"""
        
        # Group by asset
        by_asset = {}
        for reading in ami_data:
            asset_id = reading.get("ASSET_ID")
            if asset_id not in by_asset:
                by_asset[asset_id] = {"dips": 0, "rain_correlated": 0, "total": 0}
            by_asset[asset_id]["total"] += 1
            if reading.get("VOLTAGE_DIP_FLAG"):
                by_asset[asset_id]["dips"] += 1
            if reading.get("RAIN_CORRELATED_DIP"):
                by_asset[asset_id]["rain_correlated"] += 1
        
        # Sort by rain correlation percentage
        asset_stats = []
        for asset_id, stats in by_asset.items():
            if stats["dips"] > 0:
                corr_pct = stats["rain_correlated"] / stats["dips"] * 100
                asset_stats.append({
                    "asset_id": asset_id,
                    "dips": stats["dips"],
                    "rain_correlated": stats["rain_correlated"],
                    "correlation_pct": corr_pct
                })
        
        asset_stats.sort(key=lambda x: x["correlation_pct"], reverse=True)
        
        for stat in asset_stats[:15]:
            indicator = "🔴" if stat["correlation_pct"] > 60 else "🟠" if stat["correlation_pct"] > 30 else "🟢"
            narrative += f"| {indicator} {stat['asset_id']} | {stat['dips']} | {stat['rain_correlated']} | {stat['correlation_pct']:.0f}% |\n"
        
        narrative += """
### Interpretation
- **>60% correlation**: Strong Water Treeing indicator - immediate attention
- **30-60% correlation**: Emerging pattern - schedule investigation
- **<30% correlation**: Normal variation - routine monitoring
"""
        
        return {
            "narrative": narrative,
            "data": {
                "total_readings": total_readings,
                "dip_events": dip_events,
                "rain_correlated": rain_correlated,
                "asset_stats": asset_stats[:50]
            },
            "sources": ["ATOMIC.AMI_READING"]
        }
