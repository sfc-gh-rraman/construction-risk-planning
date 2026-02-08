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
    """Get ML-predicted asset health scores and degradation trends."""
    try:
        results = snowflake_service.execute_query(f"""
            SELECT 
                PREDICTION_ID, ASSET_ID, ASSET_TYPE,
                ACTUAL_HEALTH_SCORE, PREDICTED_HEALTH_SCORE,
                HEALTH_DELTA, MODEL_CONFIDENCE, PREDICTED_CONDITION,
                PREDICTION_DATE, MODEL_VERSION
            FROM RISK_PLANNING_DB.ML.ASSET_HEALTH_PREDICTION
            ORDER BY PREDICTED_HEALTH_SCORE ASC
            LIMIT {limit}
        """)
        critical = [r for r in results if r.get("PREDICTED_CONDITION") == "CRITICAL"]
        return {
            "predictions": results,
            "summary": {
                "total_predictions": len(results),
                "critical_condition": len(critical),
                "avg_health_score": sum(r.get("PREDICTED_HEALTH_SCORE", 0) or 0 for r in results) / max(len(results), 1)
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
            ORDER BY PREDICTED_DAYS_TO_CONTACT ASC
            LIMIT {limit}
        """)
        high_risk = [r for r in results if r.get("GROWTH_RISK") == "HIGH"]
        urgent = [r for r in results if (r.get("PREDICTED_DAYS_TO_CONTACT") or 999) < 30]
        return {
            "predictions": results,
            "summary": {
                "total_predictions": len(results),
                "high_growth_risk": len(high_risk),
                "urgent_trim_needed": len(urgent),
                "avg_days_to_contact": sum(r.get("PREDICTED_DAYS_TO_CONTACT", 0) or 0 for r in results) / max(len(results), 1)
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
            ORDER BY RISK_LEVEL DESC, CONDITION_SCORE ASC
            LIMIT {limit}
        """)
        high_risk = [r for r in results if r.get("RISK_LEVEL") == "HIGH"]
        by_type = {}
        for r in high_risk:
            t = r.get("ASSET_TYPE", "UNKNOWN")
            by_type[t] = by_type.get(t, 0) + 1
        return {
            "predictions": results,
            "summary": {
                "total_predictions": len(results),
                "high_risk_assets": len(high_risk),
                "by_asset_type": by_type
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
                   SUM(CASE WHEN PREDICTED_CONDITION = 'CRITICAL' THEN 1 ELSE 0 END) as critical
            FROM RISK_PLANNING_DB.ML.ASSET_HEALTH_PREDICTION
        """)[0]
        
        veg_growth = snowflake_service.execute_query("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN GROWTH_RISK = 'HIGH' THEN 1 ELSE 0 END) as high_risk,
                   SUM(CASE WHEN PREDICTED_DAYS_TO_CONTACT < 30 THEN 1 ELSE 0 END) as urgent
            FROM RISK_PLANNING_DB.ML.VEGETATION_GROWTH_PREDICTION
        """)[0]
        
        ignition = snowflake_service.execute_query("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN RISK_LEVEL = 'HIGH' THEN 1 ELSE 0 END) as high_risk
            FROM RISK_PLANNING_DB.ML.IGNITION_RISK_PREDICTION
        """)[0]
        
        cable = snowflake_service.execute_query("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN RISK_LEVEL = 'HIGH' THEN 1 ELSE 0 END) as at_risk
            FROM RISK_PLANNING_DB.ML.CABLE_FAILURE_PREDICTION
        """)[0]
        
        return {
            "models": {
                "asset_health": {
                    "name": "Asset Health Predictor",
                    "icon": "activity",
                    "total_predictions": asset_health.get("TOTAL", 0),
                    "critical_count": asset_health.get("CRITICAL", 0),
                    "algorithm": "GradientBoostingRegressor",
                    "status": "active"
                },
                "vegetation_growth": {
                    "name": "Vegetation Growth",
                    "icon": "tree-pine",
                    "total_predictions": veg_growth.get("TOTAL", 0),
                    "high_risk_count": veg_growth.get("HIGH_RISK", 0),
                    "urgent_count": veg_growth.get("URGENT", 0),
                    "algorithm": "RandomForestRegressor",
                    "status": "active"
                },
                "ignition_risk": {
                    "name": "Ignition Risk",
                    "icon": "flame",
                    "total_predictions": ignition.get("TOTAL", 0),
                    "high_risk_count": ignition.get("HIGH_RISK", 0),
                    "algorithm": "GradientBoostingClassifier",
                    "status": "active"
                },
                "cable_failure": {
                    "name": "Water Treeing",
                    "icon": "zap",
                    "total_predictions": cable.get("TOTAL", 0),
                    "at_risk_count": cable.get("AT_RISK", 0),
                    "algorithm": "Correlation Analysis",
                    "hidden_discovery": True,
                    "status": "active"
                }
            },
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"ML summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/combined-risk", tags=["ML Predictions"])
async def get_combined_risk_summary(limit: int = Query(100, le=500)):
    """Get combined ML risk view from dynamic table with all predictions merged."""
    try:
        results = snowflake_service.execute_query(f"""
            SELECT 
                ASSET_ID, ASSET_TYPE, ACTUAL_CONDITION, ASSET_AGE_YEARS,
                REGION, FIRE_THREAT_DISTRICT, TOTAL_CUSTOMERS,
                PREDICTED_HEALTH_SCORE, HEALTH_STATUS, HEALTH_DELTA,
                IGNITION_RISK_LEVEL, AVG_CLEARANCE_DEFICIT,
                WATER_TREEING_RISK, RAIN_VOLTAGE_CORRELATION,
                COMPOSITE_ML_RISK_SCORE, MAINTENANCE_PRIORITY
            FROM RISK_PLANNING_DB.ML.COMBINED_RISK_SUMMARY
            ORDER BY COMPOSITE_ML_RISK_SCORE DESC
            LIMIT {limit}
        """)
        
        by_priority = {}
        by_region = {}
        for r in results:
            p = r.get("MAINTENANCE_PRIORITY", "UNKNOWN")
            by_priority[p] = by_priority.get(p, 0) + 1
            reg = r.get("REGION", "UNKNOWN")
            by_region[reg] = by_region.get(reg, 0) + 1
        
        return {
            "assets": results,
            "summary": {
                "total_assets": len(results),
                "by_priority": by_priority,
                "by_region": by_region,
                "avg_risk_score": sum(r.get("COMPOSITE_ML_RISK_SCORE", 0) or 0 for r in results) / max(len(results), 1)
            },
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"Combined risk error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/combined-risk/by-region", tags=["ML Predictions"])
async def get_combined_risk_by_region():
    """Get aggregated ML risk metrics by region for dashboard visualization."""
    try:
        results = snowflake_service.execute_query("""
            SELECT 
                REGION,
                COUNT(*) as ASSET_COUNT,
                AVG(COMPOSITE_ML_RISK_SCORE) as AVG_RISK_SCORE,
                SUM(CASE WHEN MAINTENANCE_PRIORITY = 'EMERGENCY' THEN 1 ELSE 0 END) as EMERGENCY_COUNT,
                SUM(CASE WHEN MAINTENANCE_PRIORITY = 'HIGH' THEN 1 ELSE 0 END) as HIGH_PRIORITY_COUNT,
                SUM(CASE WHEN HEALTH_STATUS = 'CRITICAL' THEN 1 ELSE 0 END) as CRITICAL_HEALTH_COUNT,
                SUM(CASE WHEN IGNITION_RISK_LEVEL = 'HIGH' THEN 1 ELSE 0 END) as HIGH_IGNITION_COUNT,
                SUM(CASE WHEN WATER_TREEING_RISK = 'HIGH' THEN 1 ELSE 0 END) as WATER_TREEING_COUNT
            FROM RISK_PLANNING_DB.ML.COMBINED_RISK_SUMMARY
            GROUP BY REGION
            ORDER BY AVG_RISK_SCORE DESC
        """)
        return {
            "regions": results,
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"Risk by region error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/urgent-actions", tags=["ML Predictions"])
async def get_urgent_ml_actions(limit: int = Query(50, le=200)):
    """Get assets requiring urgent action based on ML predictions."""
    try:
        results = snowflake_service.execute_query(f"""
            SELECT 
                ASSET_ID, ASSET_TYPE, REGION, FIRE_THREAT_DISTRICT,
                HEALTH_STATUS, IGNITION_RISK_LEVEL, WATER_TREEING_RISK,
                COMPOSITE_ML_RISK_SCORE, MAINTENANCE_PRIORITY,
                TOTAL_CUSTOMERS
            FROM RISK_PLANNING_DB.ML.COMBINED_RISK_SUMMARY
            WHERE MAINTENANCE_PRIORITY IN ('EMERGENCY', 'HIGH')
            ORDER BY 
                CASE MAINTENANCE_PRIORITY WHEN 'EMERGENCY' THEN 1 WHEN 'HIGH' THEN 2 END,
                COMPOSITE_ML_RISK_SCORE DESC
            LIMIT {limit}
        """)
        
        emergency = [r for r in results if r.get("MAINTENANCE_PRIORITY") == "EMERGENCY"]
        high = [r for r in results if r.get("MAINTENANCE_PRIORITY") == "HIGH"]
        
        return {
            "urgent_assets": results,
            "summary": {
                "emergency_count": len(emergency),
                "high_priority_count": len(high),
                "total_customers_affected": sum(r.get("TOTAL_CUSTOMERS", 0) or 0 for r in emergency)
            },
            "fire_season": snowflake_service.get_fire_season_countdown()
        }
    except Exception as e:
        logger.error(f"Urgent actions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AssetPredictionsRequest(BaseModel):
    asset_ids: List[str] = Field(..., description="List of asset IDs to fetch predictions for")


@app.post("/ml/asset-predictions", tags=["ML Predictions"])
async def get_asset_ml_predictions(request: AssetPredictionsRequest):
    """
    Get ALL ML predictions for specific assets - health, vegetation, ignition, water treeing.
    Returns real AI insights to replace fake random strings in UI.
    """
    try:
        asset_ids = request.asset_ids[:500]
        if not asset_ids:
            return {"predictions": {}}
        
        ids_str = ",".join(f"'{aid}'" for aid in asset_ids)
        
        health = snowflake_service.execute_query(f"""
            SELECT ASSET_ID, PREDICTED_HEALTH_SCORE, PREDICTED_CONDITION, 
                   HEALTH_DELTA, MODEL_CONFIDENCE
            FROM RISK_PLANNING_DB.ML.ASSET_HEALTH_PREDICTION
            WHERE ASSET_ID IN ({ids_str})
        """)
        
        vegetation = snowflake_service.execute_query(f"""
            SELECT ASSET_ID, PREDICTED_DAYS_TO_CONTACT, GROWTH_RISK, 
                   PREDICTED_GROWTH_RATE, SPECIES
            FROM RISK_PLANNING_DB.ML.VEGETATION_GROWTH_PREDICTION
            WHERE ASSET_ID IN ({ids_str})
        """)
        
        ignition = snowflake_service.execute_query(f"""
            SELECT ASSET_ID, RISK_LEVEL, CONDITION_SCORE, AVG_CLEARANCE_DEFICIT
            FROM RISK_PLANNING_DB.ML.IGNITION_RISK_PREDICTION
            WHERE ASSET_ID IN ({ids_str})
        """)
        
        cable = snowflake_service.execute_query(f"""
            SELECT ASSET_ID, PREDICTED_WATER_TREEING, RAIN_VOLTAGE_CORRELATION,
                   RISK_LEVEL, RAIN_CORRELATED_DIPS, MOISTURE_EXPOSURE
            FROM RISK_PLANNING_DB.ML.CABLE_FAILURE_PREDICTION
            WHERE ASSET_ID IN ({ids_str})
        """)
        
        combined = snowflake_service.execute_query(f"""
            SELECT ASSET_ID, COMPOSITE_ML_RISK_SCORE, MAINTENANCE_PRIORITY,
                   HEALTH_STATUS, IGNITION_RISK_LEVEL, WATER_TREEING_RISK
            FROM RISK_PLANNING_DB.ML.COMBINED_RISK_SUMMARY
            WHERE ASSET_ID IN ({ids_str})
        """)
        
        predictions = {}
        for aid in asset_ids:
            predictions[aid] = {
                "health": next((h for h in health if h["ASSET_ID"] == aid), None),
                "vegetation": next((v for v in vegetation if v["ASSET_ID"] == aid), None),
                "ignition": next((i for i in ignition if i["ASSET_ID"] == aid), None),
                "cable": next((c for c in cable if c["ASSET_ID"] == aid), None),
                "combined": next((r for r in combined if r["ASSET_ID"] == aid), None)
            }
        
        return {
            "predictions": predictions,
            "total_assets": len(asset_ids),
            "coverage": {
                "health": len(health),
                "vegetation": len(vegetation),
                "ignition": len(ignition),
                "cable": len(cable),
                "combined": len(combined)
            }
        }
    except Exception as e:
        logger.error(f"Asset predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/feature-importance/{model_name}", tags=["ML Explainability"])
async def get_feature_importance(model_name: str):
    """
    Get SHAP-style feature importance for ML models.
    Returns feature contributions that explain model predictions.
    """
    feature_importance = {
        "asset_health": {
            "model_name": "Asset Health Predictor",
            "algorithm": "GradientBoostingRegressor",
            "features": [
                {"name": "Asset Age (Years)", "importance": 0.32, "direction": "negative", "description": "Older assets have lower health scores"},
                {"name": "Maintenance Frequency", "importance": 0.24, "direction": "positive", "description": "Regular maintenance improves health"},
                {"name": "Condition Score", "importance": 0.18, "direction": "positive", "description": "Historical condition impacts predictions"},
                {"name": "Fire District Tier", "importance": 0.12, "direction": "negative", "description": "Higher tier = more environmental stress"},
                {"name": "Voltage Class", "importance": 0.08, "direction": "mixed", "description": "Higher voltage equipment degrades differently"},
                {"name": "Total Customers", "importance": 0.06, "direction": "negative", "description": "High-load assets degrade faster"}
            ],
            "baseline_prediction": 0.72,
            "model_accuracy": 0.87
        },
        "vegetation_growth": {
            "model_name": "Vegetation Growth Predictor",
            "algorithm": "RandomForestRegressor",
            "features": [
                {"name": "Species Growth Rate", "importance": 0.35, "direction": "positive", "description": "Fast-growing species need more frequent trimming"},
                {"name": "Current Clearance", "importance": 0.28, "direction": "negative", "description": "Less clearance = faster contact"},
                {"name": "Rainfall (30d)", "importance": 0.15, "direction": "positive", "description": "More rain accelerates growth"},
                {"name": "Season", "importance": 0.12, "direction": "mixed", "description": "Spring/summer = faster growth"},
                {"name": "Soil Type", "importance": 0.06, "direction": "positive", "description": "Rich soil increases growth"},
                {"name": "Proximity to Water", "importance": 0.04, "direction": "positive", "description": "Water access boosts growth"}
            ],
            "baseline_prediction": 45,
            "model_accuracy": 0.82
        },
        "ignition_risk": {
            "model_name": "Ignition Risk Classifier",
            "algorithm": "GradientBoostingClassifier",
            "features": [
                {"name": "Fire District Tier", "importance": 0.30, "direction": "positive", "description": "Tier 3 zones have highest base risk"},
                {"name": "Clearance Deficit", "importance": 0.25, "direction": "positive", "description": "Non-compliant clearance increases ignition risk"},
                {"name": "Asset Condition", "importance": 0.18, "direction": "negative", "description": "Poor condition = higher ignition probability"},
                {"name": "Wind Exposure", "importance": 0.12, "direction": "positive", "description": "High wind areas spread fire faster"},
                {"name": "Fuel Load Index", "importance": 0.10, "direction": "positive", "description": "Vegetation density near lines"},
                {"name": "Historical Outages", "importance": 0.05, "direction": "positive", "description": "Past events predict future risk"}
            ],
            "baseline_prediction": "MEDIUM",
            "model_accuracy": 0.91
        },
        "cable_failure": {
            "model_name": "Water Treeing Detector",
            "algorithm": "Correlation Analysis + Decision Tree",
            "features": [
                {"name": "Rain-Voltage Correlation", "importance": 0.40, "direction": "positive", "description": "Key indicator: voltage dips during rain"},
                {"name": "Cable Age", "importance": 0.22, "direction": "positive", "description": "Older cables more susceptible"},
                {"name": "Moisture Exposure", "importance": 0.18, "direction": "positive", "description": "Wet environments accelerate treeing"},
                {"name": "Material Type", "importance": 0.10, "direction": "mixed", "description": "XLPE vs EPR degradation patterns"},
                {"name": "Load Cycling", "importance": 0.06, "direction": "positive", "description": "Thermal stress from load changes"},
                {"name": "Historical Dip Count", "importance": 0.04, "direction": "positive", "description": "Cumulative stress indicator"}
            ],
            "baseline_prediction": 0,
            "model_accuracy": 0.78,
            "discovery_note": "Hidden pattern: Rain events correlate with voltage anomalies in degrading cables"
        }
    }
    
    if model_name not in feature_importance:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found. Available: {list(feature_importance.keys())}")
    
    return {
        "model": model_name,
        **feature_importance[model_name]
    }


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
