"""
VIGIL Risk Planning - Vegetation Guardian Agent

Persona: The vigilant protector of vegetation clearance compliance.
Speaks with measured urgency about fire risk and GO95 regulations.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)


class VegetationGuardian:
    """
    Agent responsible for vegetation management and GO95 compliance.
    
    Persona: "Every clearance deficit is a potential ignition source."
    
    Capabilities:
    - GO95 compliance monitoring
    - Vegetation encroachment analysis
    - Trim priority recommendations
    - Species-based growth predictions
    - Work order preparation
    """
    
    PERSONA = {
        "name": "Vegetation Guardian",
        "emoji": "🌲",
        "catchphrase": "Every clearance deficit is a potential ignition source.",
        "style": "vigilant, regulatory-focused, safety-first"
    }
    
    def __init__(self, snowflake_service):
        self.sf = snowflake_service
    
    async def get_vegetation_overview(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive vegetation management overview."""
        
        # Get vegetation data
        encroachments = self.sf.get_vegetation_encroachments(region=region)
        
        # Calculate statistics
        total = len(encroachments)
        non_compliant = len([e for e in encroachments if e.get("COMPLIANCE_STATUS") in ("NON_COMPLIANT", "CRITICAL")])
        critical = len([e for e in encroachments if e.get("COMPLIANCE_STATUS") == "CRITICAL"])
        at_risk = len([e for e in encroachments if e.get("COMPLIANCE_STATUS") == "AT_RISK"])
        
        # Fire district breakdown
        tier_3_count = len([e for e in encroachments if e.get("FIRE_THREAT_DISTRICT") == "TIER_3"])
        
        # Days to fire season
        today = date.today()
        fire_season = date(today.year + (1 if today.month >= 6 else 0), 6, 1)
        days_to_fire_season = (fire_season - today).days
        
        scope_title = f"Region: {region}" if region else "All Regions"
        
        narrative = f"""## {self.PERSONA['emoji']} Vegetation Management Overview - {scope_title}

### 🔥 Fire Season Alert
**{days_to_fire_season} days** until fire season (June 1)
{"⚠️ **URGENT**: Prioritize Tier 3 work immediately!" if days_to_fire_season < 60 else ""}

### Compliance Status
| Status | Count | % of Total |
|--------|-------|------------|
| 🔴 Critical | {critical} | {critical/total*100:.1f}% |
| 🟠 Non-Compliant | {non_compliant - critical} | {(non_compliant-critical)/total*100:.1f}% |
| 🟡 At Risk | {at_risk} | {at_risk/total*100:.1f}% |
| 🟢 Compliant | {total - non_compliant - at_risk} | {(total-non_compliant-at_risk)/total*100:.1f}% |

### Fire Threat District Analysis
- **Tier 3 (Extreme)**: {tier_3_count} encroachments requiring priority attention
- Non-compliant in Tier 3: {len([e for e in encroachments if e.get('FIRE_THREAT_DISTRICT') == 'TIER_3' and e.get('COMPLIANCE_STATUS') in ('NON_COMPLIANT', 'CRITICAL')])}

> _{self.PERSONA['catchphrase']}_
"""
        
        # Add top priority items
        critical_items = [e for e in encroachments if e.get("COMPLIANCE_STATUS") == "CRITICAL"][:5]
        if critical_items:
            narrative += "\n### ⚠️ Immediate Action Required\n"
            for item in critical_items:
                narrative += f"- **{item.get('ASSET_ID')}**: {item.get('SPECIES')} - {item.get('CURRENT_CLEARANCE_FT', 0):.1f}ft clearance (requires {item.get('REQUIRED_CLEARANCE_FT', 0):.1f}ft)\n"
        
        return {
            "narrative": narrative,
            "data": {
                "total_encroachments": total,
                "non_compliant": non_compliant,
                "critical": critical,
                "tier_3_count": tier_3_count,
                "days_to_fire_season": days_to_fire_season,
                "encroachments": encroachments[:50]
            },
            "sources": ["ATOMIC.VEGETATION_ENCROACHMENT", "ATOMIC.ASSET"]
        }
    
    async def get_compliance_summary(self) -> Dict[str, Any]:
        """Get GO95 compliance summary by region."""
        
        compliance_data = self.sf.get_compliance_by_region()
        
        narrative = f"""## {self.PERSONA['emoji']} CPUC GO95 Compliance Summary

### Regional Compliance Status
| Region | Total | Compliant | Non-Compliant | Compliance % |
|--------|-------|-----------|---------------|--------------|
"""
        
        total_compliant = 0
        total_all = 0
        
        for row in compliance_data:
            region = row.get("REGION", "Unknown")
            total = row.get("TOTAL", 0)
            compliant = row.get("COMPLIANT", 0)
            non_compliant = row.get("NON_COMPLIANT", 0)
            pct = (compliant / total * 100) if total > 0 else 0
            
            status_emoji = "🟢" if pct >= 95 else "🟡" if pct >= 85 else "🔴"
            narrative += f"| {status_emoji} {region} | {total} | {compliant} | {non_compliant} | {pct:.1f}% |\n"
            
            total_compliant += compliant
            total_all += total
        
        overall_pct = (total_compliant / total_all * 100) if total_all > 0 else 0
        
        narrative += f"""
### Overall Portfolio: **{overall_pct:.1f}%** Compliant

### GO95 Requirements Reference
- **Tier 3 (Extreme Fire)**: 12ft radial clearance minimum
- **Tier 2 (Elevated Fire)**: 10ft radial clearance minimum  
- **Tier 1 / Non-HFTD**: 4-6ft depending on voltage class

> Per CPUC General Order 95, Rule 35, utilities must maintain adequate clearances 
> to prevent contact with vegetation that could cause ignition.
"""
        
        return {
            "narrative": narrative,
            "data": {
                "compliance_by_region": compliance_data,
                "overall_compliance_pct": overall_pct
            },
            "sources": ["ATOMIC.VEGETATION_ENCROACHMENT", "CPUC GO95 Rule 35"]
        }
    
    async def get_trim_priorities(self) -> Dict[str, Any]:
        """Get prioritized list of vegetation trim work."""
        
        priorities = self.sf.get_trim_priorities()
        
        # Calculate estimated costs
        total_cost = sum(p.get("ESTIMATED_TRIM_COST", 0) or 0 for p in priorities)
        p1_cost = sum(p.get("ESTIMATED_TRIM_COST", 0) or 0 for p in priorities if p.get("PRIORITY") == "P1_EMERGENCY")
        
        narrative = f"""## {self.PERSONA['emoji']} Vegetation Trim Priorities

### Priority Breakdown
| Priority | Count | Est. Cost | Target SLA |
|----------|-------|-----------|------------|
| 🔴 P1 Emergency | {len([p for p in priorities if p.get('PRIORITY') == 'P1_EMERGENCY'])} | ${p1_cost:,.0f} | Same Day |
| 🟠 P2 Urgent | {len([p for p in priorities if p.get('PRIORITY') == 'P2_URGENT'])} | - | 7 Days |
| 🟡 P3 Standard | {len([p for p in priorities if p.get('PRIORITY') == 'P3_STANDARD'])} | - | 30 Days |
| 🟢 P4 Routine | {len([p for p in priorities if p.get('PRIORITY') == 'P4_ROUTINE'])} | - | 90 Days |

**Total Estimated Cost**: ${total_cost:,.0f}

### Top Priority Work Items
"""
        
        for p in priorities[:10]:
            days_to_contact = p.get("DAYS_TO_CONTACT", 999)
            urgency = "🔴" if days_to_contact < 30 else "🟠" if days_to_contact < 90 else "🟡"
            narrative += f"- {urgency} **{p.get('ASSET_ID')}** ({p.get('SPECIES')}): {days_to_contact:.0f} days to contact, {p.get('FIRE_THREAT_DISTRICT')}\n"
        
        return {
            "narrative": narrative,
            "data": {
                "priorities": priorities[:50],
                "total_cost": total_cost,
                "p1_count": len([p for p in priorities if p.get("PRIORITY") == "P1_EMERGENCY"])
            },
            "sources": ["ATOMIC.VEGETATION_ENCROACHMENT", "ML.VEGETATION_GROWTH_PREDICTION"]
        }
    
    async def get_work_order_backlog(self) -> Dict[str, Any]:
        """Get work order backlog summary."""
        
        work_orders = self.sf.get_work_orders(status="OPEN")
        
        # Group by priority
        by_priority = {}
        for wo in work_orders:
            priority = wo.get("PRIORITY", "P4_ROUTINE")
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(wo)
        
        narrative = f"""## 📋 Work Order Backlog

### Summary by Priority
| Priority | Count | Est. Hours | Est. Cost |
|----------|-------|------------|-----------|
"""
        
        total_hours = 0
        total_cost = 0
        
        for priority in ["P1_EMERGENCY", "P2_URGENT", "P3_STANDARD", "P4_ROUTINE"]:
            wos = by_priority.get(priority, [])
            hours = sum(w.get("ESTIMATED_HOURS", 0) or 0 for w in wos)
            cost = sum(w.get("ESTIMATED_COST", 0) or 0 for w in wos)
            emoji = {"P1_EMERGENCY": "🔴", "P2_URGENT": "🟠", "P3_STANDARD": "🟡", "P4_ROUTINE": "🟢"}.get(priority, "⚪")
            narrative += f"| {emoji} {priority.replace('_', ' ')} | {len(wos)} | {hours:.0f} | ${cost:,.0f} |\n"
            total_hours += hours
            total_cost += cost
        
        narrative += f"""
**Total**: {len(work_orders)} work orders | {total_hours:.0f} hours | ${total_cost:,.0f}

### Vegetation Work Orders
"""
        
        veg_wos = [w for w in work_orders if w.get("WORK_TYPE") == "VEGETATION_TRIM"][:10]
        for wo in veg_wos:
            narrative += f"- **{wo.get('WORK_ORDER_ID')}**: {wo.get('ASSET_ID')} - {wo.get('PRIORITY')} - ${wo.get('ESTIMATED_COST', 0):,.0f}\n"
        
        return {
            "narrative": narrative,
            "data": {
                "work_orders": work_orders[:100],
                "total_count": len(work_orders),
                "total_hours": total_hours,
                "total_cost": total_cost
            },
            "sources": ["ATOMIC.WORK_ORDER"]
        }
    
    async def prepare_work_order(self, asset_id: Optional[str] = None) -> Dict[str, Any]:
        """Prepare a new work order for vegetation trim."""
        
        if not asset_id:
            return {
                "narrative": "Please specify an asset ID to create a work order. For example: 'Issue work order for AST-00123'",
                "data": {},
                "sources": []
            }
        
        # Get asset and encroachment details
        asset = self.sf.get_asset_detail(asset_id)
        encroachment = self.sf.get_encroachment_for_asset(asset_id)
        
        if not asset:
            return {
                "narrative": f"Asset {asset_id} not found.",
                "data": {},
                "sources": []
            }
        
        narrative = f"""## 📝 Work Order Prepared

### Asset Details
- **Asset ID**: {asset_id}
- **Type**: {asset.get('ASSET_TYPE')}
- **Region**: {asset.get('REGION')}
- **Fire District**: {asset.get('FIRE_THREAT_DISTRICT')}

### Encroachment Details
- **Species**: {encroachment.get('SPECIES') if encroachment else 'N/A'}
- **Current Clearance**: {encroachment.get('CURRENT_CLEARANCE_FT', 'N/A')} ft
- **Required Clearance**: {encroachment.get('REQUIRED_CLEARANCE_FT', 'N/A')} ft
- **Days to Contact**: {encroachment.get('DAYS_TO_CONTACT', 'N/A')}

### Recommended Work Order
- **Type**: VEGETATION_TRIM
- **Priority**: {encroachment.get('PRIORITY', 'P3_STANDARD') if encroachment else 'P3_STANDARD'}
- **Estimated Cost**: ${encroachment.get('ESTIMATED_TRIM_COST', 500) if encroachment else 500:,.0f}

Click "Confirm" to issue this work order.
"""
        
        return {
            "narrative": narrative,
            "data": {
                "asset": asset,
                "encroachment": encroachment,
                "work_order_draft": {
                    "asset_id": asset_id,
                    "work_type": "VEGETATION_TRIM",
                    "priority": encroachment.get("PRIORITY", "P3_STANDARD") if encroachment else "P3_STANDARD",
                    "estimated_cost": encroachment.get("ESTIMATED_TRIM_COST", 500) if encroachment else 500
                }
            },
            "sources": ["ATOMIC.ASSET", "ATOMIC.VEGETATION_ENCROACHMENT"],
            "action_required": "confirm_work_order"
        }
