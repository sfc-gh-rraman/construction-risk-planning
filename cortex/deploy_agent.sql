-- =====================================================
-- VIGIL Risk Planning - Cortex Agent Deployment
-- =====================================================
-- 
-- IMPORTANT: Cortex Agents are deployed via the Snowsight UI or Python API.
-- This SQL file provides setup and verification steps.
--
-- To deploy the agent:
-- 1. Go to Snowsight → AI & ML → Cortex Agents
-- 2. Click "Create Agent"
-- 3. Configure with the settings from vigil_agent.json
-- 4. Or use the Python utility script (deploy_agent.py)
-- =====================================================

USE DATABASE RISK_PLANNING_DB;
USE SCHEMA CONSTRUCTION_RISK;
USE WAREHOUSE RISK_COMPUTE_WH;

-- =====================================================
-- Prerequisites Check
-- =====================================================

SELECT '🔍 Step 1: Checking semantic model stage...' as STEP;
LIST @RISK_PLANNING_DB.CONSTRUCTION_RISK.SEMANTIC_MODELS;

SELECT '🔍 Step 2: Checking Cortex Search services...' as STEP;
SHOW CORTEX SEARCH SERVICES IN DATABASE RISK_PLANNING_DB;

SELECT '🔍 Step 3: Verifying data exists...' as STEP;
SELECT 
    (SELECT COUNT(*) FROM ATOMIC.ASSET) as assets,
    (SELECT COUNT(*) FROM ATOMIC.VEGETATION_ENCROACHMENT) as encroachments,
    (SELECT COUNT(*) FROM ATOMIC.WORK_ORDER) as work_orders,
    (SELECT COUNT(*) FROM ATOMIC.AMI_READING) as ami_readings,
    (SELECT COUNT(*) FROM ML.CABLE_FAILURE_PREDICTION) as cable_predictions;

-- =====================================================
-- Fire Season Countdown
-- =====================================================

SELECT '🔥 Step 4: Fire Season Status...' as STEP;
SELECT 
    CURRENT_DATE() as today,
    DATE_FROM_PARTS(
        YEAR(CURRENT_DATE()) + CASE WHEN MONTH(CURRENT_DATE()) >= 6 THEN 1 ELSE 0 END, 
        6, 1
    ) as fire_season_start,
    DATEDIFF('day', CURRENT_DATE(), 
        DATE_FROM_PARTS(
            YEAR(CURRENT_DATE()) + CASE WHEN MONTH(CURRENT_DATE()) >= 6 THEN 1 ELSE 0 END, 
            6, 1
        )
    ) as days_to_fire_season,
    CASE 
        WHEN DATEDIFF('day', CURRENT_DATE(), DATE_FROM_PARTS(YEAR(CURRENT_DATE()) + CASE WHEN MONTH(CURRENT_DATE()) >= 6 THEN 1 ELSE 0 END, 6, 1)) > 90 
            THEN '🟢 Good preparation window'
        WHEN DATEDIFF('day', CURRENT_DATE(), DATE_FROM_PARTS(YEAR(CURRENT_DATE()) + CASE WHEN MONTH(CURRENT_DATE()) >= 6 THEN 1 ELSE 0 END, 6, 1)) > 30 
            THEN '🟡 Accelerate critical work'
        ELSE '🔴 URGENT - Fire season imminent'
    END as status;

-- =====================================================
-- Agent Configuration Summary (for UI deployment)
-- =====================================================

/*
Agent Name: VIGIL_RISK_AGENT

Description: 
AI agent for utility vegetation and infrastructure risk planning. Combines data 
queries with ML insights, compliance document search, and Water Treeing detection.

Model: mistral-large (or llama3.1-70b)

Tools:
1. data_analyst (Cortex Analyst)
   - Semantic Model: @CONSTRUCTION_RISK.SEMANTIC_MODELS/risk_semantic_model.yaml
   - Description: Query asset, vegetation, work order data

2. go95_search (Cortex Search)
   - Service: DOCS.GO95_SEARCH_SERVICE
   - Description: Search CPUC GO95 compliance documents

3. vegetation_search (Cortex Search)
   - Service: DOCS.VEGETATION_SEARCH_SERVICE
   - Description: Search vegetation management standards

4. work_order_search (Cortex Search)
   - Service: DOCS.WORK_ORDER_SEARCH_SERVICE
   - Description: Search work order narratives

5. ami_anomaly_search (Cortex Search)
   - Service: DOCS.AMI_ANOMALY_SEARCH_SERVICE
   - Description: Search AMI voltage anomalies - KEY FOR HIDDEN DISCOVERY

Sample Questions:
- What is the asset portfolio health summary?
- How many days until fire season?
- Show me high-risk assets in Tier 3 fire districts
- What is the GO95 vegetation compliance status?
- What is the Hidden Discovery pattern?
- Search for rain correlated voltage dips
*/

-- =====================================================
-- Python Deployment Script
-- =====================================================
-- 
-- Save this as deploy_agent.py and run with snowpark session:
--
-- ```python
-- from snowflake.core import Root
-- from snowflake.core.cortex.agent import CortexAgent, CortexAgentTool
-- 
-- def deploy_vigil_agent(session):
--     """Deploy VIGIL Risk Agent to Cortex."""
--     
--     agent = CortexAgent(
--         name="VIGIL_RISK_AGENT",
--         description="AI agent for utility vegetation and infrastructure risk planning with Water Treeing detection",
--         model="mistral-large",
--         instructions="""You are VIGIL, an AI assistant for utility vegetation and infrastructure risk planning.
-- You help vegetation managers, grid operators, and safety teams understand asset health and fire risk.
-- 
-- CRITICAL: For 'Hidden Discovery' or 'Water Treeing' questions, search for rain-correlated voltage dips 
-- in underground cables - there's a systemic issue with 150+ XLPE cables showing moisture degradation!
-- 
-- Always calculate days until fire season (June 1) for urgency context.
-- Highlight Tier 3 fire district risks. Format currency with $ and commas.""",
--         tools=[
--             CortexAgentTool(
--                 tool_type="cortex_analyst_text_to_sql",
--                 name="data_analyst",
--                 spec={
--                     "semantic_model": "@RISK_PLANNING_DB.CONSTRUCTION_RISK.SEMANTIC_MODELS/risk_semantic_model.yaml",
--                     "description": "Query asset, vegetation, work order, and ML prediction data"
--                 }
--             ),
--             CortexAgentTool(
--                 tool_type="cortex_search",
--                 name="go95_search",
--                 spec={
--                     "service": "RISK_PLANNING_DB.DOCS.GO95_SEARCH_SERVICE",
--                     "max_results": 10,
--                     "description": "Search CPUC GO95 compliance documents"
--                 }
--             ),
--             CortexAgentTool(
--                 tool_type="cortex_search",
--                 name="vegetation_search",
--                 spec={
--                     "service": "RISK_PLANNING_DB.DOCS.VEGETATION_SEARCH_SERVICE",
--                     "max_results": 10,
--                     "description": "Search vegetation management standards"
--                 }
--             ),
--             CortexAgentTool(
--                 tool_type="cortex_search",
--                 name="work_order_search",
--                 spec={
--                     "service": "RISK_PLANNING_DB.DOCS.WORK_ORDER_SEARCH_SERVICE",
--                     "max_results": 10,
--                     "description": "Search work order narratives"
--                 }
--             ),
--             CortexAgentTool(
--                 tool_type="cortex_search",
--                 name="ami_anomaly_search",
--                 spec={
--                     "service": "RISK_PLANNING_DB.DOCS.AMI_ANOMALY_SEARCH_SERVICE",
--                     "max_results": 15,
--                     "description": "Search AMI voltage anomalies - KEY FOR WATER TREEING DETECTION"
--                 }
--             )
--         ]
--     )
--     
--     root = Root(session)
--     agents = root.databases["RISK_PLANNING_DB"].schemas["CONSTRUCTION_RISK"].cortex_agents
--     agents.create(agent, mode="or_replace")
--     
--     print("✅ VIGIL_RISK_AGENT deployed successfully!")
--     return agent
-- 
-- # Usage:
-- # from snowflake.snowpark import Session
-- # session = Session.builder.configs({"connection_name": "demo"}).create()
-- # deploy_vigil_agent(session)
-- ```

-- =====================================================
-- Verification
-- =====================================================

SELECT '✅ Agent configuration ready!' as STATUS;
SELECT 'To deploy: Snowsight → AI & ML → Cortex Agents → Create Agent' as INSTRUCTIONS;
SELECT 'Or run: python deploy_agent.py --connection demo' as ALTERNATIVE;

-- =====================================================
-- Hidden Discovery Preview (Water Treeing)
-- =====================================================

SELECT 
    '⚡ HIDDEN DISCOVERY PREVIEW' as SECTION,
    'Water Treeing in Underground Cables' as PATTERN;

-- Show cables with rain-correlated voltage dips
SELECT 
    a.material,
    a.moisture_exposure,
    COUNT(DISTINCT a.asset_id) as cable_count,
    ROUND(AVG(a.asset_age_years), 1) as avg_age_years,
    SUM(CASE WHEN ami.rain_correlated_dip THEN 1 ELSE 0 END) as rain_correlated_dips
FROM ATOMIC.ASSET a
JOIN ATOMIC.AMI_READING ami ON a.asset_id = ami.asset_id
WHERE a.asset_type = 'UNDERGROUND_CABLE'
GROUP BY a.material, a.moisture_exposure
HAVING SUM(CASE WHEN ami.rain_correlated_dip THEN 1 ELSE 0 END) > 0
ORDER BY rain_correlated_dips DESC;

-- Summary of Hidden Discovery impact
SELECT 
    '🔍 WATER TREEING SUMMARY' as SECTION,
    COUNT(DISTINCT a.asset_id) as affected_cables,
    COUNT(*) as total_dip_events,
    '$' || TO_CHAR(ROUND(SUM(cfp.estimated_replacement_cost), 0), '999,999,999') as total_replacement_cost,
    SUM(cfp.customer_impact_count) as customers_at_risk
FROM ATOMIC.ASSET a
JOIN ATOMIC.AMI_READING ami ON a.asset_id = ami.asset_id
LEFT JOIN ML.CABLE_FAILURE_PREDICTION cfp ON a.asset_id = cfp.asset_id
WHERE a.asset_type = 'UNDERGROUND_CABLE'
  AND ami.rain_correlated_dip = TRUE;
