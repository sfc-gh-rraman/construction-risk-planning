"""
VIGIL Risk Planning - Asset Inspector Agent

Persona: Methodical equipment analyst who knows every pole, transformer, and cable.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AssetInspector:
    """
    Agent responsible for asset health monitoring and condition assessment.
    
    Persona: "I know every asset in this grid like the back of my hand."
    
    Capabilities:
    - Asset health scoring
    - Replacement prioritization
    - Inspection scheduling
    - Equipment age analysis
    - ML-based health predictions
    """
    
    PERSONA = {
        "name": "Asset Inspector",
        "emoji": "🔧",
        "catchphrase": "A healthy grid starts with healthy assets.",
        "style": "methodical, detail-oriented, proactive"
    }
    
    def __init__(self, snowflake_service):
        self.sf = snowflake_service
    
    async def get_asset_overview(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive asset health overview."""
        
        assets = self.sf.get_assets(region=region)
        
        total = len(assets)
        
        # Health distribution
        critical = len([a for a in assets if (a.get("HEALTH_SCORE") or 100) < 40])
        poor = len([a for a in assets if 40 <= (a.get("HEALTH_SCORE") or 100) < 60])
        fair = len([a for a in assets if 60 <= (a.get("HEALTH_SCORE") or 100) < 80])
        good = len([a for a in assets if (a.get("HEALTH_SCORE") or 100) >= 80])
        
        # Risk distribution
        high_risk = len([a for a in assets if (a.get("RISK_SCORE") or 0) > 70])
        
        # Age analysis
        avg_age = sum(a.get("ASSET_AGE_YEARS", 0) or 0 for a in assets) / total if total > 0 else 0
        old_assets = len([a for a in assets if (a.get("ASSET_AGE_YEARS") or 0) > 30])
        
        # Replacement value
        total_value = sum(a.get("REPLACEMENT_COST", 0) or 0 for a in assets)
        at_risk_value = sum(a.get("REPLACEMENT_COST", 0) or 0 for a in assets if (a.get("RISK_SCORE") or 0) > 70)
        
        scope_title = f"Region: {region}" if region else "All Regions"
        
        narrative = f"""## {self.PERSONA['emoji']} Asset Health Overview - {scope_title}

### Portfolio Summary
- **Total Assets**: {total:,}
- **Average Age**: {avg_age:.1f} years
- **Total Replacement Value**: ${total_value/1e6:.1f}M

### Health Distribution
| Condition | Count | % | Value at Risk |
|-----------|-------|---|---------------|
| 🔴 Critical (<40) | {critical} | {critical/total*100:.1f}% | ${sum(a.get('REPLACEMENT_COST', 0) or 0 for a in assets if (a.get('HEALTH_SCORE') or 100) < 40)/1e6:.1f}M |
| 🟠 Poor (40-60) | {poor} | {poor/total*100:.1f}% | - |
| 🟡 Fair (60-80) | {fair} | {fair/total*100:.1f}% | - |
| 🟢 Good (80+) | {good} | {good/total*100:.1f}% | - |

### Risk Summary
- **High Risk Assets** (score >70): {high_risk}
- **Value at Risk**: ${at_risk_value/1e6:.1f}M
- **Assets >30 years old**: {old_assets}

### Asset Type Breakdown
| Type | Count | Avg Health | Avg Age |
|------|-------|------------|---------|
"""
        
        # Group by asset type
        by_type = {}
        for a in assets:
            atype = a.get("ASSET_TYPE", "UNKNOWN")
            if atype not in by_type:
                by_type[atype] = []
            by_type[atype].append(a)
        
        for atype, type_assets in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            avg_health = sum(a.get("HEALTH_SCORE", 0) or 0 for a in type_assets) / len(type_assets)
            avg_type_age = sum(a.get("ASSET_AGE_YEARS", 0) or 0 for a in type_assets) / len(type_assets)
            narrative += f"| {atype} | {len(type_assets)} | {avg_health:.1f} | {avg_type_age:.1f} |\n"
        
        narrative += f"\n> _{self.PERSONA['catchphrase']}_"
        
        return {
            "narrative": narrative,
            "data": {
                "total_assets": total,
                "health_distribution": {"critical": critical, "poor": poor, "fair": fair, "good": good},
                "high_risk_count": high_risk,
                "avg_age": avg_age,
                "total_value": total_value,
                "assets": assets[:100]
            },
            "sources": ["ATOMIC.ASSET", "ML.ASSET_HEALTH_PREDICTION"]
        }
    
    async def get_replacement_priorities(self) -> Dict[str, Any]:
        """Get prioritized list of assets needing replacement."""
        
        assets = self.sf.get_assets()
        
        # Filter to high-risk, poor health assets
        replacement_candidates = [
            a for a in assets 
            if (a.get("HEALTH_SCORE") or 100) < 50 or (a.get("RISK_SCORE") or 0) > 75
        ]
        
        # Sort by risk score descending
        replacement_candidates.sort(key=lambda x: x.get("RISK_SCORE", 0) or 0, reverse=True)
        
        total_cost = sum(a.get("REPLACEMENT_COST", 0) or 0 for a in replacement_candidates)
        
        narrative = f"""## {self.PERSONA['emoji']} Asset Replacement Priorities

### Summary
- **Assets Requiring Attention**: {len(replacement_candidates)}
- **Total Replacement Cost**: ${total_cost/1e6:.1f}M

### Top 15 Priority Replacements
| Asset ID | Type | Age | Health | Risk | Est. Cost |
|----------|------|-----|--------|------|-----------|
"""
        
        for a in replacement_candidates[:15]:
            narrative += f"| {a.get('ASSET_ID')} | {a.get('ASSET_TYPE')} | {a.get('ASSET_AGE_YEARS', 0):.0f}y | {a.get('HEALTH_SCORE', 0):.0f} | {a.get('RISK_SCORE', 0):.0f} | ${(a.get('REPLACEMENT_COST', 0) or 0)/1e3:.0f}K |\n"
        
        narrative += """
### Recommendation
Prioritize assets with:
1. Risk score > 80 in Tier 3 fire districts
2. Health score < 40 with high criticality
3. Age > 40 years with declining performance
"""
        
        return {
            "narrative": narrative,
            "data": {
                "replacement_candidates": replacement_candidates[:50],
                "total_cost": total_cost
            },
            "sources": ["ATOMIC.ASSET", "ML.ASSET_HEALTH_PREDICTION"]
        }
    
    async def get_asset_detail(self, asset_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific asset."""
        
        asset = self.sf.get_asset_detail(asset_id)
        
        if not asset:
            return {
                "narrative": f"Asset {asset_id} not found.",
                "data": {},
                "sources": []
            }
        
        # Get related data
        work_orders = self.sf.get_work_orders_for_asset(asset_id)
        risk_assessment = self.sf.get_risk_assessment_for_asset(asset_id)
        
        health = asset.get("HEALTH_SCORE", 0) or 0
        health_status = "🔴 Critical" if health < 40 else "🟠 Poor" if health < 60 else "🟡 Fair" if health < 80 else "🟢 Good"
        
        narrative = f"""## {self.PERSONA['emoji']} Asset Detail: {asset_id}

### Basic Information
| Property | Value |
|----------|-------|
| Type | {asset.get('ASSET_TYPE')} |
| Material | {asset.get('MATERIAL')} |
| Region | {asset.get('REGION')} |
| Circuit | {asset.get('CIRCUIT_ID')} |
| Install Date | {asset.get('INSTALL_DATE')} |
| Age | {asset.get('ASSET_AGE_YEARS', 0):.0f} years |

### Health & Risk
| Metric | Value | Status |
|--------|-------|--------|
| Health Score | {health:.0f}/100 | {health_status} |
| Risk Score | {asset.get('RISK_SCORE', 0):.0f}/100 | {'🔴 High' if (asset.get('RISK_SCORE') or 0) > 70 else '🟢 Normal'} |
| Fire District | {asset.get('FIRE_THREAT_DISTRICT')} | - |
| Criticality | {asset.get('CRITICALITY_FACTOR', 1):.1f}x | - |

### Replacement
- **Estimated Cost**: ${asset.get('REPLACEMENT_COST', 0):,.0f}
- **Last Inspection**: {asset.get('LAST_INSPECTION_DATE')}
- **Next Due**: {asset.get('NEXT_INSPECTION_DUE')}

### Work Order History
"""
        
        if work_orders:
            for wo in work_orders[:5]:
                narrative += f"- {wo.get('WORK_ORDER_ID')}: {wo.get('WORK_TYPE')} - {wo.get('STATUS')}\n"
        else:
            narrative += "No recent work orders.\n"
        
        return {
            "narrative": narrative,
            "data": {
                "asset": asset,
                "work_orders": work_orders,
                "risk_assessment": risk_assessment
            },
            "sources": ["ATOMIC.ASSET", "ATOMIC.WORK_ORDER", "ATOMIC.RISK_ASSESSMENT"]
        }
    
    async def get_inspection_schedule(self) -> Dict[str, Any]:
        """Get upcoming inspection schedule."""
        
        assets = self.sf.get_assets()
        
        # Filter to assets with upcoming inspections
        from datetime import date, timedelta
        today = date.today()
        next_30_days = today + timedelta(days=30)
        
        upcoming = [
            a for a in assets 
            if a.get("NEXT_INSPECTION_DUE") and a.get("NEXT_INSPECTION_DUE") <= next_30_days.isoformat()
        ]
        
        overdue = [
            a for a in assets
            if a.get("NEXT_INSPECTION_DUE") and a.get("NEXT_INSPECTION_DUE") < today.isoformat()
        ]
        
        narrative = f"""## {self.PERSONA['emoji']} Inspection Schedule

### Summary
- **Overdue Inspections**: {len(overdue)} ⚠️
- **Due in Next 30 Days**: {len(upcoming)}

### Overdue - Immediate Attention Required
| Asset ID | Type | Last Inspection | Days Overdue |
|----------|------|-----------------|--------------|
"""
        
        for a in sorted(overdue, key=lambda x: x.get("NEXT_INSPECTION_DUE", ""))[:10]:
            days_overdue = (today - date.fromisoformat(a.get("NEXT_INSPECTION_DUE", today.isoformat()))).days
            narrative += f"| {a.get('ASSET_ID')} | {a.get('ASSET_TYPE')} | {a.get('LAST_INSPECTION_DATE')} | {days_overdue} |\n"
        
        return {
            "narrative": narrative,
            "data": {
                "overdue": overdue[:50],
                "upcoming": upcoming[:50]
            },
            "sources": ["ATOMIC.ASSET"]
        }
