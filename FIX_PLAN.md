# VIGIL Risk Planning - Comprehensive Fix Plan

**Created:** 2026-02-07  
**Reference:** `construction/construction_capital_delivery` (ATLAS)  
**Status:** ✅ 14/15 COMPLETED - Ready for build and test

---

## Overview

This document outlines all identified gaps between the VIGIL (construction_risk_planning) work-in-progress and the reference ATLAS (construction_capital_delivery) implementation. All items are considered blockers for production deployment.

---

## Fix Items

### 1. SPCS Token Authentication Pattern

**Priority:** CRITICAL  
**Category:** Backend Infrastructure

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| Token Source | `/snowflake/session/token` file | `http://localhost:8080/oauth/token` endpoint |
| Detection | `os.path.exists("/snowflake/session/token")` | `os.getenv("SNOWFLAKE_HOST")` only |
| Reconnect | Auto-reconnect on error 390114 (token expired) | No reconnection logic |
| Session Type | Snowpark `Session.builder.getOrCreate()` | snowflake.connector only |

**Reference Files:**
- `construction_capital_delivery/copilot/backend/services/snowflake_service_spcs.py` lines 16-132

**Fix Required:**
```python
# Correct SPCS detection
def _detect_spcs() -> bool:
    if os.path.exists("/snowflake/session/token"):
        return True
    if os.environ.get("SNOWFLAKE_HOST"):
        return True
    return False

# Correct token reading
token_path = "/snowflake/session/token"
if os.path.exists(token_path):
    with open(token_path, "r") as f:
        token = f.read().strip()
```

---

### 2. Two-Tier Query Strategy

**Priority:** CRITICAL  
**Category:** Backend Query Logic

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| Direct SQL | `direct_sql_query()` with pattern matching | Missing entirely |
| Keywords | "list projects", "how many", "over budget", "behind schedule" | N/A |
| Fallback | `cortex_analyst()` for open-ended questions | Only orchestrator routing |
| Reliability | Deterministic SQL for common queries | All queries go through LLM |

**Reference Files:**
- `construction_capital_delivery/copilot/backend/services/snowflake_service_spcs.py` (method `direct_sql_query`)

**Fix Required:**
Add `direct_sql_query()` method with keyword detection:
- "list circuits" → pre-written SQL
- "fire risk" → pre-written SQL
- "vegetation compliance" → pre-written SQL
- "water treeing" → pre-written SQL for Hidden Discovery

---

### 3. Cortex Agent REST API Client

**Priority:** CRITICAL  
**Category:** AI Integration

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| Endpoint | `POST /api/v2/databases/{db}/schemas/{schema}/agents/{name}:run` | Uses `SNOWFLAKE.CORTEX.COMPLETE` SQL function |
| Message Format | `{"role": "user", "content": [{"type": "text", "text": "..."}]}` | Simple string content |
| SSE Events | `response.output_text.delta`, `response.thinking.delta`, `response.tool_result`, `response.chart` | Not implemented |
| Streaming | Full SSE event parsing | Chunked text only |

**Reference Files:**
- `construction_capital_delivery/copilot/backend/services/cortex_agent_client.py`

**Fix Required:**
Rewrite `cortex_agent_client.py` to use REST API:
```python
async def run_agent(self, message: str):
    endpoint = f"/api/v2/databases/{self.database}/schemas/{self.schema}/agents/{self.agent_name}:run"
    payload = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": message}]}
        ]
    }
    # SSE streaming implementation
```

---

### 4. Multi-Page Frontend Application

**Priority:** CRITICAL  
**Category:** Frontend Architecture

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| Pages | 8 pages | 1 page (App.tsx) |
| Navigation | Layout with sidebar/header | No navigation |
| State | `currentPage`, `selectedProjectId` | Limited state |
| Components | Reusable across pages | Single-use |

**Reference Pages (ATLAS):**
1. `Landing.tsx` - Hero with entry points
2. `MissionControl.tsx` - Main dashboard
3. `PortfolioMap.tsx` - Geographic view
4. `ProjectDeepDive.tsx` - Detail view
5. `ScopeForensics.tsx` - Hidden Discovery
6. `MorningBrief.tsx` - Daily summary
7. `KnowledgeBase.tsx` - Document search
8. `Architecture.tsx` - Technical docs

**Fix Required:**
Create equivalent pages for VIGIL:
1. `Landing.tsx` - Fire season hero
2. `RiskControlTower.tsx` - Main dashboard (exists as App.tsx)
3. `VegetationManagement.tsx` - GO95 compliance
4. `AssetReliability.tsx` - Asset health
5. `WaterTreeingDiscovery.tsx` - Hidden Discovery page
6. `MorningBrief.tsx` - Daily risk brief
7. `ComplianceDocs.tsx` - GO95 search
8. `Architecture.tsx` - Technical docs

---

### 5. Unified Dockerfile and Deploy Structure

**Priority:** CRITICAL  
**Category:** Deployment

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| Dockerfiles | 1 unified `Dockerfile` | 2 separate: `Dockerfile.frontend`, `Dockerfile.backend` |
| Process Manager | supervisord (nginx + uvicorn) | Unknown |
| Spec File | `service_spec.yaml` with token volume mount | `spec.yaml` in wrong location |
| Deploy Script | `copilot/deploy/deploy.sh` | `setup/spcs/build_and_push.sh` |
| Folder | `copilot/deploy/` | `setup/spcs/` |

**Reference Files:**
- `construction_capital_delivery/copilot/deploy/Dockerfile`
- `construction_capital_delivery/copilot/deploy/service_spec.yaml`
- `construction_capital_delivery/copilot/deploy/nginx.conf`
- `construction_capital_delivery/copilot/deploy/supervisord.conf`

**Fix Required:**
1. Create `copilot/deploy/` folder
2. Consolidate to single Dockerfile
3. Add supervisord.conf
4. Update nginx.conf for API proxy
5. Create proper service_spec.yaml with token volume:
```yaml
volumes:
  - name: token-vol
    source: "@RISK_PLANNING_DB.SPCS.VIGIL_STAGE/token"
```

---

### 6. Deploy Folder Structure

**Priority:** HIGH  
**Category:** Project Organization

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| Location | `copilot/deploy/` | `setup/spcs/` |
| Files | Dockerfile, nginx.conf, supervisord.conf, service_spec.yaml, deploy.sh, grant_access.sql, DEPLOYMENT_GUIDE.md | Split across setup/spcs/ |

**Fix Required:**
- Create `copilot/deploy/` folder
- Move/recreate all deployment files
- Delete or deprecate `setup/spcs/`

---

### 7. Cortex Agent JSON Configuration

**Priority:** HIGH  
**Category:** AI Configuration

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| File | `cortex/atlas_agent.json` | `cortex/vigil_agent.json` exists but unused |
| Tools | 3 tools: data_analyst, co_search, contract_search | Need: data_analyst, compliance_search, ami_search |
| Semantic Model Path | `@CAPITAL_PROJECTS_DB.CAPITAL_PROJECTS.SEMANTIC_MODELS/capital_semantic_model.yaml` | Need to verify path |

**Reference File:**
- `construction_capital_delivery/cortex/atlas_agent.json`

**Fix Required:**
Update `vigil_agent.json` with:
```json
{
  "name": "vigil_agent",
  "tools": [
    {"type": "cortex_analyst", "name": "data_analyst", "semantic_model": "@RISK_PLANNING_DB.CONSTRUCTION_RISK.SEMANTIC_MODELS/risk_semantic_model.yaml"},
    {"type": "cortex_search", "name": "compliance_search", "service": "RISK_PLANNING_DB.DOCS.GO95_SEARCH_SERVICE"},
    {"type": "cortex_search", "name": "ami_search", "service": "RISK_PLANNING_DB.DOCS.AMI_ANOMALY_SEARCH_SERVICE"}
  ]
}
```

---

### 8. SQL Column Name Mismatches

**Priority:** HIGH  
**Category:** Data Layer

| Query Location | Column Used | DDL Actual Column | Fix |
|----------------|-------------|-------------------|-----|
| `get_assets()` | `MATERIAL` | `INSULATION_TYPE` or not present | Update query |
| `get_assets()` | `ASSET_AGE_YEARS` | `AGE_YEARS` | Update query |
| `get_assets()` | `CONDITION_SCORE` | Present but 1-100 not 0-1 | Verify scale |
| `get_assets()` | `NEXT_INSPECTION_DUE` | Not in DDL | Remove or add to DDL |
| `get_water_treeing_candidates()` | `MATERIAL` | `INSULATION_TYPE` | Update query |
| `get_water_treeing_candidates()` | `CABLE_AGE_YEARS` | `CABLE_AGE_YEARS` in ML table | Verify |
| `get_vegetation_encroachments()` | `SPECIES` | `TREE_SPECIES` | Update query |
| `get_vegetation_encroachments()` | `CURRENT_CLEARANCE_FT` | `DISTANCE_TO_CONDUCTOR_FT` | Update query |
| `get_vegetation_encroachments()` | `CLEARANCE_DEFICIT_FT` | Computed, not stored | Add computation |
| `get_vegetation_encroachments()` | `DAYS_TO_CONTACT` | `DAYS_TO_CRITICAL` | Update query |
| `get_vegetation_encroachments()` | `ESTIMATED_TRIM_COST` | Not in DDL | Remove or add |

**Reference Files:**
- `construction_risk_planning/ddl/002_atomic_tables.sql`
- `construction_risk_planning/ddl/003_ml_tables.sql`

**Fix Required:**
Audit all queries in `snowflake_service_spcs.py` against DDL and update column names.

---

### 9. Missing Frontend Components

**Priority:** HIGH  
**Category:** Frontend Components

| Component | Reference (ATLAS) | Current (VIGIL) | Purpose |
|-----------|-------------------|-----------------|---------|
| `Layout.tsx` | Yes | No | Page wrapper with nav |
| `Chat.tsx` | Yes | `Copilot.tsx` (different) | SSE streaming chat |
| `VegaChart.tsx` | Yes | No | Vega-Lite visualizations |
| `MetricGauge.tsx` | Yes | `MetricGauge.tsx` in resource_workforce | Circular gauges |
| `AIThinking.tsx` | Yes | No | Agent reasoning display |
| `AlertCard.tsx` | Yes | Yes | Alert display |
| `LoadingSpinner.tsx` | Yes | No | Loading states |

**Reference Files:**
- `construction_capital_delivery/copilot/frontend/src/components/`

**Fix Required:**
Copy and adapt from reference:
- `Layout.tsx` with VIGIL branding
- `Chat.tsx` with SSE event handling
- `VegaChart.tsx` for risk visualizations
- `AIThinking.tsx` for agent transparency

---

### 10. Orchestrator Response Structure Mismatch

**Priority:** HIGH  
**Category:** Backend API

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| Return Key | `response["narrative"]` used correctly | Returns `narrative` but `main.py` expects different keys |
| Agent Key | `response["agent"]` | Missing in some handlers |
| Persona Key | `response["persona"]` | Missing |

**main.py line 195-209 expects:**
```python
ChatResponse(
    message=response["narrative"],  # OK
    agent=response["agent"],        # MISSING from handlers
    persona=response["persona"],    # MISSING from handlers
    data=response.get("data"),
    sources=response.get("sources"),
    ...
)
```

**Fix Required:**
Update all agent handlers to return consistent structure:
```python
return {
    "narrative": "...",
    "agent": "vegetation_guardian",
    "persona": {"name": "Vegetation Guardian", "emoji": "🌳"},
    "data": {...},
    "sources": [...]
}
```

---

### 11. SSE Streaming Implementation

**Priority:** HIGH  
**Category:** Real-time Communication

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| Event Types | text, thinking, status, tool_result, chart | message, complete only |
| Tool Results | Streamed separately | Not implemented |
| Thinking Steps | Shown in collapsible panel | Not implemented |
| Charts | Vega-Lite specs streamed | Not implemented |

**Reference Files:**
- `construction_capital_delivery/copilot/backend/api/main.py` (SSE endpoint)
- `construction_capital_delivery/copilot/frontend/src/components/Chat.tsx` (event parsing)

**Fix Required:**
Update `/chat/stream` endpoint to emit proper events:
```python
yield {"event": "thinking", "data": json.dumps({"step": "Analyzing..."})}
yield {"event": "tool_result", "data": json.dumps({"sql": "...", "rows": [...]})}
yield {"event": "chart", "data": json.dumps(vega_spec)}
yield {"event": "text", "data": json.dumps({"chunk": "...", "done": False})}
```

---

### 12. Hidden Discovery Query Corrections

**Priority:** HIGH  
**Category:** Core Feature

| Query | Issue | Fix |
|-------|-------|-----|
| `get_water_treeing_candidates()` | References `MATERIAL` | Change to `INSULATION_TYPE` |
| `get_water_treeing_candidates()` | References `p.CUSTOMER_IMPACT_COUNT` | Not in DDL - remove or add |
| `get_rain_correlated_dips()` | References `RAINFALL_24H_INCHES` | DDL has `RAINFALL_MM` |
| `get_rain_correlated_dips()` | References `VOLTAGE_READING` | DDL has `VOLTAGE_AVG` |

**Reference Pattern (ATLAS Hidden Discovery):**
```sql
SELECT ... FROM ML.CABLE_FAILURE_PREDICTION p
WHERE p.WATER_TREEING_PROBABILITY > 0.5
  AND p.RAIN_CORRELATION_SCORE > 0.3
```

**Fix Required:**
Rewrite Water Treeing queries to match actual DDL columns:
```sql
SELECT 
    p.ASSET_ID,
    p.WATER_TREEING_PROBABILITY,
    p.WATER_TREEING_SEVERITY,
    p.RAIN_CORRELATION_SCORE,
    p.FAILURE_PROBABILITY_30D,
    a.INSULATION_TYPE,
    a.MOISTURE_EXPOSURE
FROM ML.CABLE_FAILURE_PREDICTION p
JOIN ATOMIC.ASSET a ON p.ASSET_ID = a.ASSET_ID
WHERE p.WATER_TREEING_SEVERITY IN ('MODERATE', 'SEVERE')
ORDER BY p.FAILURE_PROBABILITY_30D DESC
```

---

### 13. Frontend Build Artifacts

**Priority:** HIGH  
**Category:** Deployment

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| `dist/` folder | Present with built assets | Missing |
| `index.html` | Built version | Source only |
| CSS/JS bundles | `index-*.css`, `index-*.js` | Not built |

**Fix Required:**
```bash
cd copilot/frontend
npm install
npm run build
```

Verify `dist/` contains:
- `index.html`
- `assets/index-*.js`
- `assets/index-*.css`

---

### 14. Missing grant_access.sql

**Priority:** HIGH  
**Category:** Security/RBAC

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| File | `copilot/deploy/grant_access.sql` | Missing |
| Grants | Service grants, role grants | None defined |

**Reference Content Pattern:**
```sql
-- Grant usage on warehouse
GRANT USAGE ON WAREHOUSE RISK_COMPUTE_WH TO APPLICATION ROLE VIGIL_APP_ROLE;

-- Grant access to database
GRANT USAGE ON DATABASE RISK_PLANNING_DB TO APPLICATION ROLE VIGIL_APP_ROLE;

-- Grant access to schemas
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.ATOMIC TO APPLICATION ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.ML TO APPLICATION ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.CONSTRUCTION_RISK TO APPLICATION ROLE VIGIL_APP_ROLE;

-- Grant SELECT on tables
GRANT SELECT ON ALL TABLES IN SCHEMA RISK_PLANNING_DB.ATOMIC TO APPLICATION ROLE VIGIL_APP_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA RISK_PLANNING_DB.ML TO APPLICATION ROLE VIGIL_APP_ROLE;
```

**Fix Required:**
Create `copilot/deploy/grant_access.sql` with appropriate RBAC grants.

---

### 15. Semantic Model Verified Queries

**Priority:** MEDIUM  
**Category:** AI Quality

| Aspect | Reference (ATLAS) | Current (VIGIL) |
|--------|-------------------|-----------------|
| verified_queries | Present with pre-tested SQL | Not visible (file truncated) |
| custom_instructions | Business context | Unknown |
| relationships | Table joins defined | Unknown |

**Reference Pattern:**
```yaml
verified_queries:
  - name: water_treeing_pattern
    question: "Show me cables at risk of water treeing"
    sql: |
      SELECT ... FROM __cable_failure_prediction p
      WHERE p.water_treeing_severity IN ('MODERATE', 'SEVERE')
      
  - name: vegetation_violations
    question: "Show vegetation clearance violations"
    sql: |
      SELECT ... FROM __vegetation_encroachment v
      WHERE v.in_violation = TRUE
```

**Fix Required:**
1. Read full `risk_semantic_model.yaml` 
2. Add verified_queries section if missing
3. Add custom_instructions for fire season context
4. Define table relationships

---

## Summary Table

| # | Item | Priority | Category | Status |
|---|------|----------|----------|--------|
| 1 | SPCS Token Auth | CRITICAL | Backend | ✅ COMPLETED |
| 2 | Two-Tier Query | CRITICAL | Backend | ✅ COMPLETED |
| 3 | Cortex Agent REST API | CRITICAL | AI | ✅ COMPLETED |
| 4 | Multi-Page Frontend | CRITICAL | Frontend | ✅ COMPLETED |
| 5 | Unified Dockerfile | CRITICAL | Deploy | ✅ COMPLETED |
| 6 | Deploy Folder Structure | HIGH | Organization | ✅ COMPLETED |
| 7 | Agent JSON Config | HIGH | AI | ✅ COMPLETED |
| 8 | SQL Column Mismatches | HIGH | Data | ✅ COMPLETED |
| 9 | Frontend Components | HIGH | Frontend | ✅ COMPLETED |
| 10 | Response Structure | HIGH | Backend | ✅ COMPLETED |
| 11 | SSE Streaming | HIGH | Backend | ✅ COMPLETED |
| 12 | Hidden Discovery Queries | HIGH | Feature | ✅ COMPLETED |
| 13 | Frontend Build | HIGH | Deploy | 🔄 PENDING (run npm build) |
| 14 | grant_access.sql | HIGH | Security | ✅ COMPLETED |
| 15 | Semantic Model VQRs | MEDIUM | AI | ✅ COMPLETED |

---

## Execution Order

1. **Phase 1 - Foundation** (Items 1, 5, 6, 14)
   - SPCS auth must work first
   - Deploy structure must be correct
   
2. **Phase 2 - Data Layer** (Items 8, 12)
   - Fix all SQL column mismatches
   - Hidden Discovery must query correctly
   
3. **Phase 3 - AI Integration** (Items 2, 3, 7, 15)
   - Two-tier query for reliability
   - Cortex Agent for intelligence
   
4. **Phase 4 - Frontend** (Items 4, 9, 11, 13)
   - Multi-page app
   - Streaming chat
   - Build artifacts
   
5. **Phase 5 - API Polish** (Item 10)
   - Consistent response structures

---

## Reference File Locations

### ATLAS (Reference)
```
construction/construction_capital_delivery/
├── copilot/
│   ├── backend/
│   │   ├── api/main.py
│   │   ├── agents/orchestrator.py
│   │   └── services/
│   │       ├── snowflake_service_spcs.py  ← SPCS auth pattern
│   │       └── cortex_agent_client.py     ← REST API pattern
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── pages/                     ← 8 pages
│   │   │   └── components/                ← Reusable components
│   │   └── dist/                          ← Built artifacts
│   └── deploy/
│       ├── Dockerfile                     ← Unified container
│       ├── service_spec.yaml
│       ├── nginx.conf
│       ├── supervisord.conf
│       └── grant_access.sql
├── cortex/
│   ├── atlas_agent.json
│   └── capital_semantic_model.yaml
└── ddl/
    └── *.sql
```

### VIGIL (Work in Progress)
```
construction/construction_risk_planning/
├── copilot/
│   ├── backend/                          ← Needs fixes
│   └── frontend/                         ← Needs pages/components
├── setup/spcs/                           ← WRONG location, move to copilot/deploy/
├── cortex/
│   ├── vigil_agent.json                  ← Needs update
│   └── risk_semantic_model.yaml          ← Needs VQRs
└── ddl/
    └── *.sql                             ← Source of truth for columns
```
