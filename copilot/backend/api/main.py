"""
VIGIL Risk Planning - FastAPI Main Application

Vegetation & Infrastructure Grid Intelligence Layer
A risk-based planning platform for utility wildfire mitigation.
"""

import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
import json

# Import services and agents
import sys
import os

# Support both SPCS deployment and local development imports
try:
    from backend.services.snowflake_service_spcs import get_snowflake_service, SnowflakeServiceSPCS
    from backend.services.cortex_agent_client import get_cortex_agent_client, CortexAgentClient
    from backend.agents.orchestrator import get_orchestrator, AgentOrchestrator
except ImportError:
    # Local development - add parent to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.snowflake_service_spcs import get_snowflake_service, SnowflakeServiceSPCS
    from services.cortex_agent_client import get_cortex_agent_client, CortexAgentClient
    from agents.orchestrator import get_orchestrator, AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global service instances
snowflake_service: Optional[SnowflakeServiceSPCS] = None
cortex_client: Optional[CortexAgentClient] = None
orchestrator: Optional[AgentOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global snowflake_service, cortex_client, orchestrator
    
    logger.info("🔥 VIGIL Risk Planning API starting up...")
    
    # Initialize services
    try:
        snowflake_service = get_snowflake_service()
        cortex_client = get_cortex_agent_client()
        orchestrator = get_orchestrator(snowflake_service)
        
        # Log fire season status
        fire_status = snowflake_service.get_fire_season_countdown()
        logger.info(f"🔥 Fire Season Status: {fire_status['message']}")
        
        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🔥 VIGIL Risk Planning API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="VIGIL Risk Planning API",
    description="""
    **Vegetation & Infrastructure Grid Intelligence Layer**
    
    A comprehensive risk-based planning platform for utility wildfire mitigation.
    
    ## Features
    - 🔥 Fire season countdown and risk monitoring
    - 🌳 Vegetation management with GO95 compliance
    - ⚡ Asset health prediction and replacement planning
    - 🔍 Hidden Discovery: Water Treeing detection in underground cables
    - 🤖 Multi-agent AI copilot with distinct personas
    
    ## Regions
    - NorCal (Northern California)
    - SoCal (Southern California)  
    - PNW (Pacific Northwest)
    - Southwest
    - Mountain
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================
# Pydantic Models
# ===================

class ChatMessage(BaseModel):
    """Chat message from user."""
    message: str = Field(..., description="User's message to the copilot")
    persona: Optional[str] = Field(None, description="Desired agent persona")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Response from the copilot."""
    message: str
    agent: str
    persona: Dict[str, Any]
    data: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None
    fire_season: Dict[str, Any]
    timestamp: str


class WorkOrderRequest(BaseModel):
    """Work order creation request."""
    asset_id: str
    work_order_type: str = "VEGETATION_MANAGEMENT"
    priority: str = "MEDIUM"
    description: str
    estimated_cost: float = 0
    scheduled_date: Optional[str] = None


class WorkOrderResponse(BaseModel):
    """Work order creation response."""
    work_order_id: str
    status: str
    message: str


# ===================
# Health & Info Endpoints
# ===================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API info."""
    fire_status = snowflake_service.get_fire_season_countdown()
    return {
        "name": "VIGIL Risk Planning API",
        "version": "1.0.0",
        "status": "operational",
        "fire_season": fire_status,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "snowflake": snowflake_service is not None,
            "cortex": cortex_client is not None,
            "orchestrator": orchestrator is not None
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/fire-season", tags=["Risk"])
async def get_fire_season():
    """Get current fire season status and countdown."""
    return snowflake_service.get_fire_season_countdown()


# ===================
# Chat/Copilot Endpoints
# ===================

@app.post("/chat", response_model=ChatResponse, tags=["Copilot"])
async def chat(request: ChatMessage):
    """
    Send a message to the VIGIL copilot.
    
    The copilot uses multiple specialized agents:
    - **Vegetation Guardian**: GO95 compliance and trim management
    - **Asset Inspector**: Asset health and replacement planning
    - **Fire Risk Analyst**: Fire risk assessment and PSPS planning
    - **Water Treeing Detective**: Hidden discovery of underground cable failures
    """
    try:
        response = await orchestrator.process_message(
            message=request.message,
            persona=request.persona,
            context=request.context
        )
        
        return ChatResponse(
            message=response["narrative"],
            agent=response["agent"],
            persona=response["persona"],
            data=response.get("data"),
            sources=response.get("sources"),
            fire_season=snowflake_service.get_fire_season_countdown(),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream", tags=["Copilot"])
async def chat_stream(request: ChatMessage):
    """
    Stream a response from the VIGIL copilot using Server-Sent Events.
    
    Yields SSE events:
    - fire_season: Initial fire season status
    - status: Agent thinking/planning steps
    - thinking: Agent reasoning
    - text: Response text chunks
    - tool_result: SQL execution results
    - chart: Vega-Lite chart specifications
    - complete: Final response with metadata
    - error: Error information
    """
    async def event_generator():
        try:
            fire_status = snowflake_service.get_fire_season_countdown()
            yield {
                "event": "fire_season",
                "data": json.dumps(fire_status)
            }
            
            try:
                messages = [{"role": "user", "content": request.message}]
                accumulated_text = ""
                
                async for event in cortex_client.run_agent_stream(messages):
                    event_type = event.get("type", "")
                    
                    if event_type == "text":
                        text_chunk = event.get("content", "")
                        accumulated_text += text_chunk
                        yield {
                            "event": "text",
                            "data": json.dumps({"chunk": text_chunk, "done": False})
                        }
                    
                    elif event_type == "thinking":
                        yield {
                            "event": "thinking",
                            "data": json.dumps({
                                "title": event.get("title", "Thinking"),
                                "content": event.get("content", "")
                            })
                        }
                    
                    elif event_type == "status":
                        yield {
                            "event": "status",
                            "data": json.dumps({
                                "title": event.get("title", ""),
                                "status": event.get("status", "")
                            })
                        }
                    
                    elif event_type == "tool_result":
                        yield {
                            "event": "tool_result",
                            "data": json.dumps({
                                "sql": event.get("sql"),
                                "data": event.get("data"),
                                "error": event.get("error")
                            })
                        }
                    
                    elif event_type == "chart":
                        yield {
                            "event": "chart",
                            "data": json.dumps({"chart_spec": event.get("chart_spec", {})})
                        }
                    
                    elif event_type == "error":
                        yield {
                            "event": "error",
                            "data": json.dumps({"error": event.get("content", "Unknown error")})
                        }
                    
                    elif event_type == "done":
                        break
                
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "agent": "VIGIL Agent",
                        "persona": {"name": "Safety Guardian", "emoji": "🛡️"},
                        "narrative": accumulated_text,
                        "done": True
                    })
                }
                
            except Exception as agent_error:
                logger.warning(f"Cortex Agent unavailable, falling back to orchestrator: {agent_error}")
                
                response = await orchestrator.process_message(
                    message=request.message,
                    persona=request.persona,
                    context=request.context
                )
                
                narrative = response["narrative"]
                chunk_size = 100
                for i in range(0, len(narrative), chunk_size):
                    chunk = narrative[i:i+chunk_size]
                    yield {
                        "event": "text",
                        "data": json.dumps({"chunk": chunk, "done": False})
                    }
                
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "agent": response.get("agent", "VIGIL"),
                        "persona": response.get("persona", {}),
                        "data": response.get("data"),
                        "sources": response.get("sources"),
                        "done": True
                    })
                }
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())


# ===================
# Dashboard Endpoints
# ===================

@app.get("/dashboard/metrics", tags=["Dashboard"])
async def get_dashboard_metrics():
    """Get all metrics for the main dashboard."""
    try:
        return snowflake_service.get_dashboard_metrics()
    except Exception as e:
        logger.error(f"Dashboard metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/map", tags=["Dashboard"])
async def get_map_data():
    """Get asset locations with risk data for 3D map visualization."""
    try:
        data = snowflake_service.get_map_data()
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [row["LONGITUDE"], row["LATITUDE"]]
                    },
                    "properties": {
                        "asset_id": row["ASSET_ID"],
                        "asset_type": row["ASSET_TYPE"],
                        "condition_score": row["CONDITION_SCORE"],
                        "risk_score": row["COMPOSITE_RISK_SCORE"],
                        "risk_tier": row["RISK_TIER"],
                        "fire_district": row["FIRE_THREAT_DISTRICT"],
                        "region": row["REGION"]
                    }
                }
                for row in data
            ],
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"Map data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================
# Asset Endpoints
# ===================

@app.get("/assets", tags=["Assets"])
async def get_assets(
    region: Optional[str] = Query(None, description="Filter by region"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type")
):
    """Get assets with optional filtering."""
    try:
        items = snowflake_service.get_assets(region=region, asset_type=asset_type)
        return {
            "items": items,
            "total": len(items),
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets/summary", tags=["Assets"])
async def get_asset_summary():
    """Get asset summary by region and type."""
    try:
        return {
            "summary": snowflake_service.get_asset_summary(),
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets/replacement-priorities", tags=["Assets"])
async def get_replacement_priorities(limit: int = Query(50, le=200)):
    """Get assets prioritized for replacement."""
    try:
        return {
            "priorities": snowflake_service.get_replacement_priorities(limit=limit),
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================
# Vegetation Endpoints
# ===================

@app.get("/vegetation", tags=["Vegetation"])
async def get_vegetation(region: Optional[str] = Query(None)):
    """Get vegetation encroachment data."""
    try:
        items = snowflake_service.get_vegetation_encroachments(region=region)
        compliance = snowflake_service.get_compliance_summary()
        total_summary = {
            "total_encroachments": len(items),
            "critical": sum(1 for i in items if i.get("TRIM_PRIORITY") == "CRITICAL"),
            "high_priority": sum(1 for i in items if i.get("TRIM_PRIORITY") == "HIGH"),
            "out_of_compliance": sum(1 for i in items if i.get("TRIM_PRIORITY") in ["CRITICAL", "HIGH"]),
            "total_trim_cost": sum(i.get("ESTIMATED_TRIM_COST", 0) or 0 for i in items),
            "avg_clearance_ft": sum(i.get("CURRENT_CLEARANCE_FT", 0) or 0 for i in items) / max(len(items), 1)
        }
        return {
            "summary": total_summary,
            "items": items,
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vegetation/compliance", tags=["Vegetation"])
async def get_compliance_summary():
    """Get GO95 compliance summary by region and fire district."""
    try:
        return {
            "compliance": snowflake_service.get_compliance_summary(),
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vegetation/trim-priorities", tags=["Vegetation"])
async def get_trim_priorities(limit: int = Query(50, le=200)):
    """Get vegetation trim priorities."""
    try:
        return {
            "priorities": snowflake_service.get_trim_priorities(limit=limit),
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vegetation/clearance-requirement", tags=["Vegetation"])
async def get_clearance_requirement(
    voltage_class: str = Query(..., description="Voltage class (e.g., HIGH_VOLTAGE)"),
    fire_district: str = Query(..., description="Fire threat district (e.g., TIER_3)")
):
    """Get GO95 clearance requirement for specific voltage class and fire district."""
    try:
        return cortex_client.get_go95_clearance_requirement(voltage_class, fire_district)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================
# Risk Endpoints
# ===================

@app.get("/risk", tags=["Risk"])
async def get_risk_assessments(region: Optional[str] = Query(None)):
    """Get risk assessment data."""
    try:
        return {
            "assessments": snowflake_service.get_risk_assessments(region=region),
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/risk/summary", tags=["Risk"])
async def get_risk_summary():
    """Get risk summary by region and tier."""
    try:
        return {
            "summary": snowflake_service.get_risk_summary(),
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/risk/psps-candidates", tags=["Risk"])
async def get_psps_candidates():
    """Get circuits that are PSPS (Public Safety Power Shutoff) candidates."""
    try:
        return {
            "candidates": snowflake_service.get_psps_candidates(),
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================
# Work Order Endpoints
# ===================

@app.get("/work-orders", tags=["Work Orders"])
async def get_work_orders(status: Optional[str] = Query(None)):
    """Get work orders with optional status filter."""
    try:
        items = snowflake_service.get_work_orders(status=status)
        summary = {
            "total": len(items),
            "open": sum(1 for i in items if i.get("STATUS") == "OPEN"),
            "in_progress": sum(1 for i in items if i.get("STATUS") == "IN_PROGRESS"),
            "completed": sum(1 for i in items if i.get("STATUS") == "COMPLETED"),
            "overdue": sum(1 for i in items if i.get("STATUS") == "OVERDUE")
        }
        return {
            "summary": summary,
            "items": items,
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workorders", tags=["Work Orders"])
async def get_workorders_alias(status: Optional[str] = Query(None)):
    """Alias for /work-orders endpoint."""
    return await get_work_orders(status)


@app.get("/work-orders/backlog", tags=["Work Orders"])
async def get_work_order_backlog():
    """Get work order backlog summary."""
    try:
        return {
            "backlog": snowflake_service.get_work_order_backlog(),
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/work-orders", response_model=WorkOrderResponse, tags=["Work Orders"])
async def create_work_order(request: WorkOrderRequest):
    """
    Create a new work order.
    
    This is the "Issue Work Order" functionality that creates actual records.
    """
    try:
        work_order_id = snowflake_service.create_work_order({
            "asset_id": request.asset_id,
            "work_order_type": request.work_order_type,
            "priority": request.priority,
            "description": request.description,
            "estimated_cost": request.estimated_cost,
            "scheduled_date": request.scheduled_date
        })
        
        return WorkOrderResponse(
            work_order_id=work_order_id,
            status="created",
            message=f"Work order {work_order_id} created successfully"
        )
        
    except Exception as e:
        logger.error(f"Work order creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================
# Hidden Discovery Endpoints
# ===================

@app.get("/discovery/water-treeing", tags=["Hidden Discovery"])
async def get_water_treeing_candidates():
    """
    🔍 HIDDEN DISCOVERY: Get underground cables showing Water Treeing indicators.
    
    Water Treeing is detected by correlating AMI voltage dips with rainfall events.
    This failure mode is invisible to traditional inspections.
    """
    try:
        return {
            "candidates": snowflake_service.get_water_treeing_candidates(),
            "ami_anomalies": snowflake_service.get_rain_correlated_dips()[:100],
            "fire_season": snowflake_service.get_fire_season_countdown(),
            "discovery_info": {
                "name": "Water Treeing Detection",
                "description": "Detecting invisible underground cable degradation via AMI data correlation",
                "key_indicators": [
                    "XLPE insulation material",
                    "15-25 years age",
                    "HIGH moisture exposure",
                    "Rain correlation score > 0.5"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/discovery/ami-correlation", tags=["Hidden Discovery"])
async def get_ami_correlation():
    """Get AMI readings analysis for rain-voltage correlation patterns."""
    try:
        ami_data = snowflake_service.get_ami_readings()
        
        # Calculate correlation statistics by asset
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
        
        # Calculate correlation percentages
        correlations = []
        for asset_id, stats in by_asset.items():
            if stats["dips"] > 0:
                correlations.append({
                    "asset_id": asset_id,
                    "total_readings": stats["total"],
                    "voltage_dips": stats["dips"],
                    "rain_correlated": stats["rain_correlated"],
                    "correlation_pct": stats["rain_correlated"] / stats["dips"] * 100
                })
        
        correlations.sort(key=lambda x: x["correlation_pct"], reverse=True)
        
        return {
            "correlations": correlations[:50],
            "summary": {
                "total_assets_analyzed": len(by_asset),
                "assets_with_high_correlation": len([c for c in correlations if c["correlation_pct"] > 60]),
                "total_readings": len(ami_data)
            },
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================
# ML Prediction Endpoints
# ===================

@app.get("/ml/asset-health", tags=["ML Predictions"])
async def get_asset_health_predictions(limit: int = Query(100, le=500)):
    """Get ML-predicted asset health scores and replacement timing."""
    try:
        results = snowflake_service.execute_query(f"""
            SELECT 
                PREDICTION_ID, ASSET_ID, ASSET_TYPE, MATERIAL,
                ACTUAL_CONDITION_SCORE, PREDICTED_CONDITION_SCORE,
                ASSET_AGE_YEARS, PREDICTED_YEARS_TO_REPLACEMENT,
                REPLACEMENT_PRIORITY, PREDICTION_DATE, MODEL_VERSION
            FROM RISK_PLANNING_DB.ML.ASSET_HEALTH_PREDICTION
            ORDER BY PREDICTED_YEARS_TO_REPLACEMENT ASC
            LIMIT {limit}
        """)
        urgent = [r for r in results if r.get("PREDICTED_YEARS_TO_REPLACEMENT", 99) <= 2]
        return {
            "predictions": results,
            "summary": {
                "total_predictions": len(results),
                "urgent_replacements": len(urgent),
                "avg_years_to_replacement": sum(r.get("PREDICTED_YEARS_TO_REPLACEMENT", 0) for r in results) / max(len(results), 1)
            },
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"Asset health predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/vegetation-growth", tags=["ML Predictions"])
async def get_vegetation_growth_predictions(limit: int = Query(100, le=500)):
    """Get ML-predicted vegetation growth rates and trim timing."""
    try:
        results = snowflake_service.execute_query(f"""
            SELECT 
                PREDICTION_ID, ENCROACHMENT_ID, ASSET_ID, SPECIES,
                ACTUAL_GROWTH_RATE, PREDICTED_GROWTH_RATE,
                CURRENT_CLEARANCE_FT, PREDICTED_DAYS_TO_CONTACT,
                GROWTH_RISK, PREDICTION_DATE, MODEL_VERSION
            FROM RISK_PLANNING_DB.ML.VEGETATION_GROWTH_PREDICTION
            ORDER BY PREDICTED_GROWTH_RATE DESC
            LIMIT {limit}
        """)
        high_risk = [r for r in results if r.get("GROWTH_RISK") == "HIGH"]
        return {
            "predictions": results,
            "summary": {
                "total_predictions": len(results),
                "high_growth_risk": len(high_risk),
                "avg_growth_rate": sum(r.get("PREDICTED_GROWTH_RATE", 0) for r in results) / max(len(results), 1)
            },
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"Vegetation growth predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/ignition-risk", tags=["ML Predictions"])
async def get_ignition_risk_predictions(limit: int = Query(100, le=500)):
    """Get ML-predicted wildfire ignition risk classifications."""
    try:
        results = snowflake_service.execute_query(f"""
            SELECT 
                PREDICTION_ID, ASSET_ID, ASSET_TYPE,
                ACTUAL_RISK, PREDICTED_IGNITION_RISK,
                CONDITION_SCORE, AVG_CLEARANCE_DEFICIT,
                RISK_LEVEL, PREDICTION_DATE, MODEL_VERSION
            FROM RISK_PLANNING_DB.ML.IGNITION_RISK_PREDICTION
            WHERE PREDICTED_IGNITION_RISK = 1
            ORDER BY CONDITION_SCORE ASC
            LIMIT {limit}
        """)
        return {
            "predictions": results,
            "summary": {
                "high_risk_assets": len(results),
                "by_asset_type": {}
            },
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"Ignition risk predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/cable-failure", tags=["ML Predictions"])
async def get_cable_failure_predictions(limit: int = Query(100, le=500)):
    """
    🔍 HIDDEN DISCOVERY: Get ML-predicted water treeing risk in underground cables.
    
    Water treeing is detected by correlating AMI voltage dips with rainfall events,
    identifying invisible insulation degradation before catastrophic failure.
    """
    try:
        results = snowflake_service.execute_query(f"""
            SELECT 
                PREDICTION_ID, ASSET_ID, MATERIAL, ASSET_AGE_YEARS,
                MOISTURE_EXPOSURE, RAIN_CORRELATED_DIPS,
                RAIN_VOLTAGE_CORRELATION, ACTUAL_RISK,
                PREDICTED_WATER_TREEING, RISK_LEVEL,
                PREDICTION_DATE, MODEL_VERSION
            FROM RISK_PLANNING_DB.ML.CABLE_FAILURE_PREDICTION
            ORDER BY PREDICTED_WATER_TREEING DESC, RAIN_CORRELATED_DIPS DESC
            LIMIT {limit}
        """)
        at_risk = [r for r in results if r.get("PREDICTED_WATER_TREEING") == 1]
        return {
            "predictions": results,
            "summary": {
                "total_cables_analyzed": len(results),
                "at_risk_cables": len(at_risk),
                "avg_age_at_risk": sum(r.get("ASSET_AGE_YEARS", 0) for r in at_risk) / max(len(at_risk), 1) if at_risk else 0
            },
            "discovery_info": {
                "name": "Water Treeing Detection",
                "description": "Hidden pattern: Rain-correlated voltage dips indicate moisture intrusion",
                "business_value": "Predict failures 6-12 months early, prevent outages"
            },
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"Cable failure predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/summary", tags=["ML Predictions"])
async def get_ml_summary():
    """Get summary of all ML model predictions and insights."""
    try:
        asset_health = snowflake_service.execute_query("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN PREDICTED_YEARS_TO_REPLACEMENT <= 2 THEN 1 ELSE 0 END) as urgent
            FROM RISK_PLANNING_DB.ML.ASSET_HEALTH_PREDICTION
        """)[0]
        
        veg_growth = snowflake_service.execute_query("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN GROWTH_RISK = 'HIGH' THEN 1 ELSE 0 END) as high_risk
            FROM RISK_PLANNING_DB.ML.VEGETATION_GROWTH_PREDICTION
        """)[0]
        
        ignition = snowflake_service.execute_query("""
            SELECT COUNT(*) as total,
                   SUM(PREDICTED_IGNITION_RISK) as high_risk
            FROM RISK_PLANNING_DB.ML.IGNITION_RISK_PREDICTION
        """)[0]
        
        cable = snowflake_service.execute_query("""
            SELECT COUNT(*) as total,
                   SUM(PREDICTED_WATER_TREEING) as at_risk
            FROM RISK_PLANNING_DB.ML.CABLE_FAILURE_PREDICTION
        """)[0]
        
        return {
            "models": {
                "asset_health": {
                    "name": "Asset Health Predictor",
                    "total_predictions": asset_health.get("TOTAL", 0),
                    "urgent_replacements": asset_health.get("URGENT", 0),
                    "algorithm": "GradientBoostingRegressor"
                },
                "vegetation_growth": {
                    "name": "Vegetation Growth Predictor",
                    "total_predictions": veg_growth.get("TOTAL", 0),
                    "high_growth_risk": veg_growth.get("HIGH_RISK", 0),
                    "algorithm": "RandomForestRegressor"
                },
                "ignition_risk": {
                    "name": "Ignition Risk Predictor",
                    "total_predictions": ignition.get("TOTAL", 0),
                    "high_risk_assets": ignition.get("HIGH_RISK", 0),
                    "algorithm": "GradientBoostingClassifier"
                },
                "cable_failure": {
                    "name": "Cable Failure (Water Treeing)",
                    "total_predictions": cable.get("TOTAL", 0),
                    "at_risk_cables": cable.get("AT_RISK", 0),
                    "algorithm": "Rule-Based + GradientBoostingClassifier",
                    "hidden_discovery": True
                }
            },
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"ML summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================
# Cortex Search Endpoints
# ===================

@app.get("/search/go95", tags=["Search"])
async def search_go95(query: str = Query(..., description="Search query")):
    """Search GO95 regulations using Cortex Search."""
    try:
        return await cortex_client.search_go95(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/vegetation", tags=["Search"])
async def search_vegetation_docs(query: str = Query(..., description="Search query")):
    """Search vegetation management documentation."""
    try:
        return await cortex_client.search_vegetation_docs(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================
# Run server
# ===================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
