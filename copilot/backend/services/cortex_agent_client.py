"""
VIGIL Risk Planning - Cortex Agent REST API Client

Calls the Snowflake Cortex Agents REST API and streams responses
including "thinking steps" back to the frontend via SSE.

Also provides access to:
- Cortex Analyst for semantic SQL generation
- Cortex Search for document retrieval (GO95 regulations)
"""

import os
import json
import logging
import httpx
from typing import AsyncGenerator, Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class CortexAgentClient:
    """
    Client for calling Snowflake Cortex Agents REST API.
    
    Endpoint: POST /api/v2/databases/{db}/schemas/{schema}/agents/{name}:run
    
    Authentication: OAuth token from SPCS (/snowflake/session/token)
    """
    
    def __init__(self):
        self.database = os.environ.get("SNOWFLAKE_DATABASE", "RISK_PLANNING_DB")
        self.schema = os.environ.get("SNOWFLAKE_SCHEMA", "CONSTRUCTION_RISK")
        self.agent_name = os.environ.get("CORTEX_AGENT_NAME", "VIGIL_RISK_AGENT")
        self.host = os.environ.get("SNOWFLAKE_HOST", "")
        self._token = None
        
        self.SEARCH_SERVICES = {
            "go95": f"{self.database}.DOCS.GO95_SEARCH_SERVICE",
            "vegetation": f"{self.database}.DOCS.VEGETATION_SEARCH_SERVICE",
            "work_orders": f"{self.database}.DOCS.WORK_ORDER_SEARCH_SERVICE",
            "ami_anomalies": f"{self.database}.DOCS.AMI_ANOMALY_SEARCH_SERVICE"
        }
        
        logger.info(f"CortexAgentClient initialized: db={self.database}, schema={self.schema}, agent={self.agent_name}")
    
    def _get_token(self) -> str:
        """Get OAuth token from SPCS session file."""
        token_path = "/snowflake/session/token"
        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                return f.read().strip()
        raise RuntimeError("No SPCS token available - not running in SPCS?")
    
    def _get_base_url(self) -> str:
        """Get the Snowflake REST API base URL."""
        if not self.host:
            raise RuntimeError("SNOWFLAKE_HOST environment variable not set")
        return f"https://{self.host}"
    
    def _get_agent_url(self) -> str:
        """Get the agent run endpoint URL - named agent format."""
        base = self._get_base_url()
        return f"{base}/api/v2/databases/{self.database}/schemas/{self.schema}/agents/{self.agent_name}:run"
    
    def _format_messages_for_api(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Format messages for Cortex Agent API.
        
        The API expects content to be an array of content objects:
        {"role": "user", "content": [{"type": "text", "text": "..."}]}
        
        NOT a bare string:
        {"role": "user", "content": "..."} <-- WRONG
        """
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg["role"],
                "content": [
                    {
                        "type": "text",
                        "text": msg["content"]
                    }
                ]
            })
        return formatted
    
    async def run_agent_stream(
        self,
        messages: List[Dict[str, str]],
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Call the Cortex Agent REST API with streaming enabled.
        
        Yields events including:
        - type: "thinking" - Planning/reasoning steps
        - type: "text" - Response text chunks
        - type: "tool_use" - SQL execution info
        - type: "chart" - Vega-Lite chart spec
        - type: "done" - Stream complete
        - type: "error" - Error occurred
        """
        try:
            token = self._get_token()
            url = self._get_agent_url()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "X-Snowflake-Authorization-Token-Type": "OAUTH",
            }
            
            formatted_messages = self._format_messages_for_api(messages)
            
            body = {
                "messages": formatted_messages,
                "stream": True,
            }
            
            if conversation_id:
                body["thread_id"] = conversation_id
            
            logger.info(f"Calling Cortex Agent: {url}")
            logger.debug(f"Request body: {json.dumps(body)[:200]}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=body,
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Agent API error: {response.status_code} - {error_text}")
                        yield {
                            "type": "error",
                            "content": f"Agent API error: {response.status_code}",
                            "details": error_text.decode() if error_text else ""
                        }
                        return
                    
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        
                        while "\n\n" in buffer:
                            event_str, buffer = buffer.split("\n\n", 1)
                            
                            event = self._parse_sse_event(event_str)
                            if event:
                                yield event
                    
                    if buffer.strip():
                        event = self._parse_sse_event(buffer)
                        if event:
                            yield event
            
            yield {"type": "done"}
            
        except Exception as e:
            logger.error(f"Cortex Agent stream error: {e}")
            yield {
                "type": "error",
                "content": str(e)
            }
    
    def _parse_sse_event(self, event_str: str) -> Optional[Dict[str, Any]]:
        """
        Parse an SSE event string from Cortex Agent API.
        
        Event types from Cortex Agent:
        - response.output_text.delta - ACTUAL OUTPUT TEXT (display to user)
        - response.thinking.delta - Agent's internal reasoning (show in thinking panel)
        - response.status - Status updates (planning, reasoning, etc.)
        - response.tool_result - Tool execution results (SQL, search)
        - response.chart - Vega-Lite chart specification
        """
        try:
            lines = event_str.strip().split("\n")
            event_type = None
            data = None
            
            for line in lines:
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        return {"type": "done"}
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        data = {"raw": data_str}
            
            if data is None:
                return None
            
            logger.debug(f"SSE: type={event_type}")
            
            if not isinstance(data, dict):
                return {"type": "text", "content": str(data)}
            
            if event_type == "response.output_text.delta" or event_type == "response.text.delta":
                text = data.get("text", "")
                if text:
                    return {"type": "text", "content": text}
                return None
            
            elif event_type == "response.thinking.delta":
                text = data.get("text", "")
                if text:
                    return {
                        "type": "thinking",
                        "title": "Reasoning",
                        "content": text
                    }
                return None
            
            elif event_type == "response.status":
                status = data.get("status", "")
                message = data.get("message", "")
                
                status_titles = {
                    "planning": "Planning analysis approach",
                    "reasoning_agent_start": "Starting analysis",
                    "reasoning_agent_stop": "Analysis complete",
                    "reevaluating_plan": "Refining approach",
                    "streaming_analyst_results": "Running SQL query",
                    "analyzing_risk": "Analyzing fire risk factors",
                    "evaluating_compliance": "Checking GO95 compliance",
                }
                
                title = status_titles.get(status, message or status)
                if title:
                    return {
                        "type": "status",
                        "title": title,
                        "status": status
                    }
                return None
            
            elif event_type == "response.tool_result.status":
                status = data.get("status", "")
                message = data.get("message", "")
                
                return {
                    "type": "tool_status",
                    "title": message or status,
                    "status": status
                }
            
            elif event_type == "response.tool_result":
                content = data.get("content", [])
                
                result = {"type": "tool_result"}
                
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if "json" in item:
                                json_data = item["json"]
                                if "sql" in json_data:
                                    result["sql"] = json_data["sql"]
                                if "error" in json_data:
                                    result["error"] = json_data["error"].get("message", str(json_data["error"]))
                                if "data" in json_data:
                                    result["data"] = json_data["data"]
                            if "text" in item:
                                result["content"] = item["text"]
                
                return result if len(result) > 1 else None
            
            elif event_type == "response.chart":
                chart_spec = data.get("chart_spec", {})
                
                if isinstance(chart_spec, str):
                    try:
                        chart_spec = json.loads(chart_spec)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse chart_spec JSON: {e}")
                        return None
                
                if chart_spec and isinstance(chart_spec, dict):
                    return {
                        "type": "chart",
                        "chart_spec": chart_spec
                    }
                return None
            
            elif event_type == "response.done":
                return {"type": "done"}
            
            elif event_type == "response.content.delta":
                text = data.get("text", "")
                if text:
                    return {"type": "text", "content": text}
                content = data.get("content", [])
                if isinstance(content, list):
                    texts = [c.get("text", "") for c in content if isinstance(c, dict)]
                    if texts:
                        return {"type": "text", "content": "".join(texts)}
                return None
            
            logger.debug(f"SSE UNKNOWN: type={event_type}, keys={list(data.keys())}")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse SSE event: {e}")
            return None
    
    async def run_agent(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Convenience method to run agent with a single message.
        """
        messages = conversation_history or []
        messages.append({"role": "user", "content": message})
        
        async for event in self.run_agent_stream(messages):
            yield event
    
    def get_go95_clearance_requirement(
        self, 
        voltage_class: str, 
        fire_threat_tier: str
    ) -> Dict[str, Any]:
        """
        Get specific GO95 clearance requirement for given parameters.
        
        CPUC GO95 Rule 35 specifies minimum clearances:
        - Tier 3 (Extreme): 12 feet minimum
        - Tier 2 (Elevated): 4-6 feet minimum
        - Non-HFTD: 4 feet minimum
        """
        go95_clearances = {
            "TIER_3": {
                "4KV": 4.0, "12KV": 6.0, "21KV": 8.0, "33KV": 10.0, "69KV": 12.0,
                "LOW_VOLTAGE": 4.0, "MEDIUM_VOLTAGE": 6.0, "HIGH_VOLTAGE": 12.0, "TRANSMISSION": 15.0
            },
            "TIER_2": {
                "4KV": 4.0, "12KV": 4.0, "21KV": 4.0, "33KV": 6.0, "69KV": 8.0,
                "LOW_VOLTAGE": 4.0, "MEDIUM_VOLTAGE": 4.0, "HIGH_VOLTAGE": 6.0, "TRANSMISSION": 10.0
            },
            "TIER_1": {
                "4KV": 2.5, "12KV": 4.0, "21KV": 4.0, "33KV": 4.0, "69KV": 6.0,
                "LOW_VOLTAGE": 2.5, "MEDIUM_VOLTAGE": 4.0, "HIGH_VOLTAGE": 6.0, "TRANSMISSION": 10.0
            },
            "NON_HFTD": {
                "4KV": 2.5, "12KV": 4.0, "21KV": 4.0, "33KV": 4.0, "69KV": 4.0,
                "LOW_VOLTAGE": 2.5, "MEDIUM_VOLTAGE": 4.0, "HIGH_VOLTAGE": 4.0, "TRANSMISSION": 10.0
            }
        }
        
        ftd = fire_threat_tier.upper().replace("-", "_").replace(" ", "_")
        vc = voltage_class.upper().replace("-", "_").replace(" ", "_")
        
        if "TIER" in ftd and "_" not in ftd:
            ftd = ftd.replace("TIER", "TIER_")
        
        clearance = go95_clearances.get(ftd, {}).get(vc)
        
        if clearance:
            return {
                "success": True,
                "voltage_class": vc,
                "fire_threat_tier": ftd,
                "required_clearance_ft": clearance,
                "regulation": "CPUC GO95 Rule 35",
                "description": f"Minimum vegetation clearance of {clearance} feet required for {vc} lines in {ftd} areas."
            }
        else:
            return {
                "success": False,
                "error": f"No clearance requirement found for {voltage_class} in {fire_threat_tier}",
                "available_tiers": list(go95_clearances.keys())
            }
    
    def analyze_compliance_gap(
        self,
        current_clearance: float,
        voltage_class: str,
        fire_threat_tier: str
    ) -> Dict[str, Any]:
        """Analyze compliance gap and provide recommendations."""
        requirement = self.get_go95_clearance_requirement(voltage_class, fire_threat_tier)
        
        if not requirement.get("success"):
            return requirement
        
        required = requirement["required_clearance_ft"]
        deficit = required - current_clearance
        
        compliance_status = "COMPLIANT" if deficit <= 0 else "VIOLATION"
        urgency = "NONE"
        
        if deficit > 0:
            ftd_upper = fire_threat_tier.upper()
            if "TIER_3" in ftd_upper or "TIER3" in ftd_upper:
                urgency = "CRITICAL" if deficit > 6 else "HIGH"
            elif "TIER_2" in ftd_upper or "TIER2" in ftd_upper:
                urgency = "HIGH" if deficit > 4 else "MEDIUM"
            else:
                urgency = "MEDIUM" if deficit > 2 else "LOW"
        
        recommendations = {
            "CRITICAL": f"IMMEDIATE ACTION REQUIRED: {deficit:.1f}ft deficit in Tier 3 fire area. Schedule emergency trim within 7 days.",
            "HIGH": f"Priority trim required: {deficit:.1f}ft deficit. Schedule vegetation management within 30 days.",
            "MEDIUM": f"Standard trim needed: {deficit:.1f}ft deficit. Include in next quarterly trim cycle.",
            "LOW": f"Minor deficit of {deficit:.1f}ft. Address during routine maintenance.",
            "NONE": "Clearance meets GO95 requirements. Continue routine monitoring."
        }
        
        return {
            "success": True,
            "current_clearance_ft": current_clearance,
            "required_clearance_ft": required,
            "deficit_ft": max(0, deficit),
            "compliance_status": compliance_status,
            "urgency": urgency,
            "fire_threat_tier": fire_threat_tier,
            "voltage_class": voltage_class,
            "regulation": "CPUC GO95 Rule 35",
            "recommendation": recommendations.get(urgency, f"Address {deficit:.1f}ft clearance deficit.")
        }
    
    def get_species_growth_info(self, species: str) -> Dict[str, Any]:
        """Get growth rate and management information for a tree species."""
        species_data = {
            "EUCALYPTUS": {"growth_rate_ft_year": 6.0, "max_height_ft": 150, "fire_risk": "EXTREME",
                "management_notes": "Highly flammable bark shreds. Requires aggressive management in HFTD areas."},
            "OAK": {"growth_rate_ft_year": 2.0, "max_height_ft": 80, "fire_risk": "MODERATE",
                "management_notes": "Protected species in many areas. Coordinate with arborist for trimming."},
            "PINE": {"growth_rate_ft_year": 3.0, "max_height_ft": 100, "fire_risk": "HIGH",
                "management_notes": "Resinous, burns readily. Monitor for beetle kill which increases fire risk."},
            "PALM": {"growth_rate_ft_year": 1.5, "max_height_ft": 60, "fire_risk": "HIGH",
                "management_notes": "Dead fronds are extremely flammable. Remove dead material annually."},
            "WILLOW": {"growth_rate_ft_year": 4.0, "max_height_ft": 50, "fire_risk": "LOW",
                "management_notes": "Fast growing near waterways. Typically lower fire risk due to moisture."},
            "MANZANITA": {"growth_rate_ft_year": 1.0, "max_height_ft": 20, "fire_risk": "EXTREME",
                "management_notes": "Highly flammable native shrub. Critical to maintain clearance in HFTD."}
        }
        
        species_upper = species.upper().replace(" ", "_")
        
        if species_upper in species_data:
            return {"success": True, "species": species_upper, **species_data[species_upper]}
        else:
            return {
                "success": True, "species": species_upper,
                "growth_rate_ft_year": 2.5, "max_height_ft": 60, "fire_risk": "MODERATE",
                "management_notes": f"Limited data for {species}. Using default growth assumptions.",
                "is_estimated": True
            }


_agent_client: Optional[CortexAgentClient] = None


def get_cortex_agent_client() -> CortexAgentClient:
    """Get or create Cortex Agent client singleton."""
    global _agent_client
    if _agent_client is None:
        _agent_client = CortexAgentClient()
    return _agent_client
