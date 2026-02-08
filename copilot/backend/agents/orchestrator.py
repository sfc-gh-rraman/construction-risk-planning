"""
VIGIL Risk Planning - Agent Orchestrator

The Orchestrator classifies user intent and routes to specialized agents:
- Vegetation Guardian: GO95 compliance, encroachment analysis, trim priorities
- Asset Inspector: Asset health, condition assessment, replacement planning
- Fire Risk Analyst: Ignition risk, fire season readiness, Tier 3 monitoring
- Water Treeing Detective: Hidden Discovery - underground cable failure detection
"""

import re
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from .vegetation_agent import VegetationGuardian
from .asset_agent import AssetInspector
from .fire_risk_agent import FireRiskAnalyst
from .discovery_agent import WaterTreeingDetective

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates multi-agent system for utility risk planning intelligence.
    
    Flow:
    1. Classify user intent from message
    2. Route to appropriate agent(s)
    3. Aggregate responses with sources
    4. Maintain conversation context
    """
    
    # Agent personas for different interaction styles
    PERSONAS = {
        "safety_guardian": {
            "name": "Safety Guardian",
            "style": "formal",
            "prefix": "As your Safety Guardian, ",
            "emoji": "🛡️"
        },
        "field_partner": {
            "name": "Field Partner", 
            "style": "practical",
            "prefix": "Hey there! ",
            "emoji": "👷"
        },
        "executive_advisor": {
            "name": "Executive Advisor",
            "style": "strategic",
            "prefix": "From a portfolio perspective, ",
            "emoji": "📊"
        },
        "data_detective": {
            "name": "Data Detective",
            "style": "analytical",
            "prefix": "I've been analyzing the data and found something interesting: ",
            "emoji": "🔍"
        }
    }
    
    def __init__(self, snowflake_service):
        self.sf = snowflake_service
        
        # Initialize specialized agents
        self.vegetation_agent = VegetationGuardian(snowflake_service)
        self.asset_agent = AssetInspector(snowflake_service)
        self.fire_risk_agent = FireRiskAnalyst(snowflake_service)
        self.discovery_agent = WaterTreeingDetective(snowflake_service)
        
        # Conversation context
        self.context = {
            "current_asset": None,
            "current_region": None,
            "last_intent": None,
            "last_results": None,
            "persona": "safety_guardian"
        }
        
        logger.info("VIGIL AgentOrchestrator initialized with 4 specialized agents")
    
    def set_persona(self, persona_id: str):
        """Set the agent persona for responses."""
        if persona_id in self.PERSONAS:
            self.context["persona"] = persona_id
            logger.info(f"Persona set to: {persona_id}")
    
    def _get_fire_season_countdown(self) -> Dict[str, Any]:
        """Calculate days until fire season (June 1)."""
        today = date.today()
        year = today.year
        if today.month >= 6:
            year += 1
        fire_season_start = date(year, 6, 1)
        days_remaining = (fire_season_start - today).days
        
        if days_remaining > 90:
            urgency = "low"
            status = "Good preparation window"
        elif days_remaining > 30:
            urgency = "medium"
            status = "Accelerate critical work"
        else:
            urgency = "high"
            status = "URGENT - Fire season imminent"
        
        return {
            "days_remaining": days_remaining,
            "fire_season_start": fire_season_start.isoformat(),
            "urgency": urgency,
            "status": status
        }
    
    async def process_message(
        self,
        message: str,
        persona: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        asset_id: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a user message and return appropriate response."""
        # Update persona
        if persona:
            self.set_persona(persona)
        
        # Update context from provided dict
        if context:
            if context.get("asset_id"):
                self.context["current_asset"] = context["asset_id"]
            if context.get("region"):
                self.context["current_region"] = context["region"]
        
        # Update context from explicit params
        if asset_id:
            self.context["current_asset"] = asset_id
        if region:
            self.context["current_region"] = region
        
        # Classify intent
        intent = self._classify_intent(message)
        self.context["last_intent"] = intent
        
        logger.info(f"Classified intent: {intent}")
        
        # Add fire season context to all responses
        fire_season = self._get_fire_season_countdown()
        
        try:
            # Route to appropriate handler
            if intent == "hidden_discovery":
                result = await self._handle_hidden_discovery(message)
            elif intent == "water_treeing":
                result = await self._handle_water_treeing(message)
            elif intent == "vegetation":
                result = await self._handle_vegetation(message)
            elif intent == "fire_risk":
                result = await self._handle_fire_risk(message)
            elif intent == "asset_health":
                result = await self._handle_asset_health(message)
            elif intent == "work_order":
                result = await self._handle_work_order(message)
            elif intent == "compliance":
                result = await self._handle_compliance(message)
            else:
                # Default to Cortex Analyst for data queries
                result = await self._handle_cortex_analyst(message)
            
            # Add fire season context
            result["fire_season"] = fire_season
            
            self.context["last_results"] = result
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            persona = self.PERSONAS.get(self.context.get("persona", "safety_guardian"))
            return {
                "narrative": f"I encountered an error: {str(e)}. Please try rephrasing your question.",
                "agent": "VIGIL Orchestrator",
                "persona": persona,
                "sources": [],
                "data": {},
                "intent": intent,
                "fire_season": fire_season
            }
    
    def _classify_intent(self, message: str) -> str:
        """Classify user intent to route to appropriate agent."""
        message_lower = message.lower()
        
        # Hidden Discovery / Water Treeing (highest priority)
        water_treeing_keywords = [
            r"hidden", r"discovery", r"water\s*tree", r"underground\s*cable",
            r"rain.*voltage", r"voltage.*rain", r"ami.*correlat", r"moisture.*degrad",
            r"xlpe.*fail", r"cable.*fail"
        ]
        for pattern in water_treeing_keywords:
            if re.search(pattern, message_lower):
                return "hidden_discovery"
        
        # Fire Risk
        fire_keywords = [
            r"fire\s*season", r"fire\s*risk", r"ignition", r"tier\s*3", r"hftd",
            r"fire\s*district", r"wildfire", r"psps", r"red\s*flag"
        ]
        for pattern in fire_keywords:
            if re.search(pattern, message_lower):
                return "fire_risk"
        
        # Vegetation
        veg_keywords = [
            r"vegetation", r"clearance", r"encroach", r"trim", r"go95", r"go\s*95",
            r"tree", r"eucalyptus", r"species", r"growth\s*rate"
        ]
        for pattern in veg_keywords:
            if re.search(pattern, message_lower):
                return "vegetation"
        
        # Asset Health
        asset_keywords = [
            r"asset\s*health", r"pole", r"transformer", r"conductor", r"equipment",
            r"condition", r"replace", r"inspection", r"age"
        ]
        for pattern in asset_keywords:
            if re.search(pattern, message_lower):
                return "asset_health"
        
        # Work Orders
        work_keywords = [
            r"work\s*order", r"priority", r"backlog", r"schedule", r"crew",
            r"issue.*order", r"create.*order"
        ]
        for pattern in work_keywords:
            if re.search(pattern, message_lower):
                return "work_order"
        
        # Compliance
        compliance_keywords = [
            r"compliance", r"violation", r"cpuc", r"regulat", r"standard"
        ]
        for pattern in compliance_keywords:
            if re.search(pattern, message_lower):
                return "compliance"
        
        # Default to data query
        return "data_query"
    
    # =========================================================================
    # Intent Handlers
    # =========================================================================
    
    async def _handle_hidden_discovery(self, message: str) -> Dict[str, Any]:
        """Handle the Hidden Discovery - Water Treeing detection."""
        response = await self.discovery_agent.find_water_treeing_pattern()
        persona = self.PERSONAS.get(self.context.get("persona", "data_detective"))
        return {
            "narrative": response["narrative"],
            "agent": "Water Treeing Detective",
            "persona": persona,
            "sources": response.get("sources", []),
            "data": response.get("data", {}),
            "intent": "hidden_discovery",
            "visualization": "water_treeing_map",
            "alert_level": "high"
        }
    
    async def _handle_water_treeing(self, message: str) -> Dict[str, Any]:
        """Handle detailed Water Treeing analysis."""
        response = await self.discovery_agent.analyze_cable_health()
        persona = self.PERSONAS.get(self.context.get("persona", "data_detective"))
        return {
            "narrative": response["narrative"],
            "agent": "Water Treeing Detective",
            "persona": persona,
            "sources": response.get("sources", []),
            "data": response.get("data", {}),
            "intent": "water_treeing",
            "visualization": "cable_analysis"
        }
    
    async def _handle_vegetation(self, message: str) -> Dict[str, Any]:
        """Handle vegetation analysis requests."""
        if "compliance" in message.lower() or "go95" in message.lower():
            response = await self.vegetation_agent.get_compliance_summary()
        elif "priority" in message.lower() or "urgent" in message.lower():
            response = await self.vegetation_agent.get_trim_priorities()
        else:
            response = await self.vegetation_agent.get_vegetation_overview(
                region=self.context.get("current_region")
            )
        
        persona = self.PERSONAS.get(self.context.get("persona", "safety_guardian"))
        return {
            "narrative": response["narrative"],
            "agent": "Vegetation Guardian",
            "persona": persona,
            "sources": response.get("sources", []),
            "data": response.get("data", {}),
            "intent": "vegetation",
            "visualization": "vegetation_map"
        }
    
    async def _handle_fire_risk(self, message: str) -> Dict[str, Any]:
        """Handle fire risk analysis requests."""
        response = await self.fire_risk_agent.get_fire_risk_overview()
        persona = self.PERSONAS.get(self.context.get("persona", "safety_guardian"))
        return {
            "narrative": response["narrative"],
            "agent": "Fire Risk Analyst",
            "persona": persona,
            "sources": response.get("sources", []),
            "data": response.get("data", {}),
            "intent": "fire_risk",
            "visualization": "fire_risk_dashboard"
        }
    
    async def _handle_asset_health(self, message: str) -> Dict[str, Any]:
        """Handle asset health requests."""
        response = await self.asset_agent.get_asset_overview(
            region=self.context.get("current_region")
        )
        persona = self.PERSONAS.get(self.context.get("persona", "safety_guardian"))
        return {
            "narrative": response["narrative"],
            "agent": "Asset Inspector",
            "persona": persona,
            "sources": response.get("sources", []),
            "data": response.get("data", {}),
            "intent": "asset_health",
            "visualization": "asset_health_dashboard"
        }
    
    async def _handle_work_order(self, message: str) -> Dict[str, Any]:
        """Handle work order requests."""
        if "issue" in message.lower() or "create" in message.lower():
            response = await self.vegetation_agent.prepare_work_order(
                asset_id=self.context.get("current_asset")
            )
        else:
            response = await self.vegetation_agent.get_work_order_backlog()
        
        persona = self.PERSONAS.get(self.context.get("persona", "field_partner"))
        return {
            "narrative": response["narrative"],
            "agent": "Vegetation Guardian",
            "persona": persona,
            "sources": response.get("sources", []),
            "data": response.get("data", {}),
            "intent": "work_order",
            "visualization": "work_order_list"
        }
    
    async def _handle_compliance(self, message: str) -> Dict[str, Any]:
        """Handle compliance requests."""
        response = await self.vegetation_agent.get_compliance_summary()
        persona = self.PERSONAS.get(self.context.get("persona", "safety_guardian"))
        return {
            "narrative": response["narrative"],
            "agent": "Vegetation Guardian",
            "persona": persona,
            "sources": response.get("sources", []),
            "data": response.get("data", {}),
            "intent": "compliance",
            "visualization": "compliance_dashboard"
        }
    
    async def _handle_cortex_analyst(self, message: str) -> Dict[str, Any]:
        """Handle general data queries using Cortex Analyst."""
        logger.info(f"Processing query via Cortex Analyst: {message}")
        
        # Try direct SQL with pattern matching first
        try:
            result = self.sf.direct_sql_query(message)
            
            if result.get("results") and len(result["results"]) > 0:
                return self._format_query_response(
                    results=result["results"],
                    sql=result.get("sql", ""),
                    explanation=result.get("explanation", ""),
                    source="Direct SQL"
                )
        except Exception as e:
            logger.warning(f"Direct SQL query failed: {e}")
        
        # Try Cortex Analyst LLM
        try:
            result = self.sf.cortex_analyst(message)
            
            if result.get("data") and len(result["data"]) > 0:
                return self._format_query_response(
                    results=result["data"],
                    sql=result.get("sql", ""),
                    explanation=result.get("answer", ""),
                    source="Cortex Analyst"
                )
        except Exception as e:
            logger.warning(f"Cortex Analyst failed: {e}")
        
        # Return helpful suggestions
        persona = self.PERSONAS.get(self.context.get("persona", "safety_guardian"))
        return {
            "narrative": self._get_help_message(),
            "agent": "VIGIL Orchestrator",
            "persona": persona,
            "sources": ["VIGIL System"],
            "data": {},
            "intent": "data_query"
        }
    
    def _format_query_response(
        self,
        results: List[Dict],
        sql: str,
        explanation: str,
        source: str
    ) -> Dict[str, Any]:
        """Format query results for display."""
        persona = self.PERSONAS.get(self.context.get("persona", "safety_guardian"))
        response_parts = [f"{persona['emoji']} **Query Results**\n"]
        
        if explanation:
            response_parts.append(f"_{explanation}_\n")
        
        # Format based on result count
        if len(results) == 1 and len(results[0]) == 1:
            key, value = list(results[0].items())[0]
            response_parts.append(f"**{key.replace('_', ' ').title()}**: {value}")
        elif len(results) <= 20:
            columns = list(results[0].keys())
            response_parts.append("| " + " | ".join(col.replace('_', ' ').title() for col in columns) + " |")
            response_parts.append("|" + "|".join(["---"] * len(columns)) + "|")
            
            for row in results:
                values = []
                for col in columns:
                    val = row.get(col)
                    if val is None:
                        values.append("-")
                    elif isinstance(val, float):
                        if abs(val) >= 1e6:
                            values.append(f"${val/1e6:.1f}M")
                        elif abs(val) >= 1e3:
                            values.append(f"${val/1e3:.0f}K")
                        else:
                            values.append(f"{val:.2f}")
                    else:
                        values.append(str(val)[:30])
                response_parts.append("| " + " | ".join(values) + " |")
        else:
            response_parts.append(f"Found {len(results)} results. Showing first 20.")
        
        response_parts.append(f"\n✅ **{len(results)} rows** | Source: {source}")
        
        persona = self.PERSONAS.get(self.context.get("persona", "safety_guardian"))
        return {
            "narrative": "\n".join(response_parts),
            "agent": "Data Analyst",
            "persona": persona,
            "sources": [source, "RISK_PLANNING_DB"],
            "data": {"sql": sql, "row_count": len(results)},
            "intent": "data_query"
        }
    
    def _get_help_message(self) -> str:
        """Return helpful suggestions when query doesn't match."""
        fire_season = self._get_fire_season_countdown()
        
        return f"""I can help you with utility risk planning. Here's what I can answer:

🔥 **Fire Season** ({fire_season['days_remaining']} days until June 1)
• "How many days until fire season?"
• "Show me Tier 3 fire district assets"
• "What is our fire season readiness?"

🌲 **Vegetation Management**
• "Show vegetation compliance by region"
• "What encroachments need priority attention?"
• "List non-compliant GO95 clearances"

⚡ **Asset Health**
• "Show me high-risk assets"
• "Which poles need replacement?"
• "What is the average asset health score?"

📋 **Work Orders**
• "Show work order backlog by priority"
• "What vegetation work is planned?"

🔍 **Hidden Discovery**
• "Show me the Water Treeing pattern"
• "Find rain-correlated voltage dips"
• "Which underground cables are at risk?"
"""


# Singleton
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator(snowflake_service=None) -> AgentOrchestrator:
    """Get or create orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        if snowflake_service is None:
            from ..services import get_snowflake_service
            snowflake_service = get_snowflake_service()
        _orchestrator = AgentOrchestrator(snowflake_service)
    return _orchestrator
