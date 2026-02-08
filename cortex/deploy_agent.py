#!/usr/bin/env python3
"""
VIGIL Risk Planning - Cortex Agent Deployment Script

Verifies prerequisites and provides deployment instructions.
The agent itself is deployed via Snowsight UI.

Usage:
    python deploy_agent.py [--connection demo]
"""

import argparse
import json


def verify_and_print_instructions(connection_name: str = "demo"):
    """Verify prerequisites and print deployment instructions."""
    
    from snowflake.snowpark import Session
    
    print("🌲 VIGIL Risk Planning - Agent Deployment")
    print("=" * 60)
    
    # Create session
    print(f"\n📡 Connecting to Snowflake ({connection_name})...")
    session = Session.builder.configs({"connection_name": connection_name}).create()
    print(f"   ✓ Connected to {session.get_current_account()}")
    
    # Verify prerequisites
    print("\n🔍 Verifying prerequisites...")
    
    # Check semantic model
    try:
        result = session.sql("""
            LIST @RISK_PLANNING_DB.CONSTRUCTION_RISK.SEMANTIC_MODELS 
            PATTERN = '.*risk_semantic_model.yaml'
        """).collect()
        if result:
            print("   ✓ Semantic model uploaded")
        else:
            print("   ⚠️  Semantic model not found - run deploy.sh first")
    except Exception as e:
        print(f"   ⚠️  Could not verify semantic model: {e}")
    
    # Check search services
    try:
        result = session.sql("""
            SHOW CORTEX SEARCH SERVICES IN DATABASE RISK_PLANNING_DB
        """).collect()
        services = [r['name'] for r in result]
        expected_services = [
            'GO95_SEARCH_SERVICE',
            'VEGETATION_SEARCH_SERVICE', 
            'WORK_ORDER_SEARCH_SERVICE',
            'AMI_ANOMALY_SEARCH_SERVICE'
        ]
        for svc in expected_services:
            if svc in services:
                print(f"   ✓ {svc} available")
            else:
                print(f"   ⚠️  {svc} not found")
    except Exception as e:
        print(f"   ⚠️  Could not verify search services: {e}")
    
    # Check data
    try:
        result = session.sql("""
            SELECT 
                (SELECT COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.ASSET) as assets,
                (SELECT COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.VEGETATION_ENCROACHMENT) as encroachments,
                (SELECT COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.WORK_ORDER) as work_orders,
                (SELECT COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.AMI_READING) as ami_readings
        """).collect()
        row = result[0]
        print(f"   ✓ Data loaded: {row['ASSETS']} assets, {row['ENCROACHMENTS']} encroachments")
        print(f"                  {row['WORK_ORDERS']} work orders, {row['AMI_READINGS']} AMI readings")
    except Exception as e:
        print(f"   ⚠️  Could not verify data: {e}")
    
    # Fire season countdown
    print("\n🔥 Fire Season Status:")
    try:
        result = session.sql("""
            SELECT 
                DATEDIFF('day', CURRENT_DATE(), 
                    DATE_FROM_PARTS(
                        YEAR(CURRENT_DATE()) + CASE WHEN MONTH(CURRENT_DATE()) >= 6 THEN 1 ELSE 0 END, 
                        6, 1
                    )
                ) as days_to_fire_season
        """).collect()
        days = result[0]['DAYS_TO_FIRE_SEASON']
        if days > 90:
            status = "🟢 Good preparation window"
        elif days > 30:
            status = "🟡 Accelerate critical work"
        else:
            status = "🔴 URGENT - Fire season imminent"
        print(f"   • Days until June 1: {days}")
        print(f"   • Status: {status}")
    except Exception as e:
        print(f"   ⚠️  Could not calculate fire season: {e}")
    
    # Hidden Discovery preview (Water Treeing)
    print("\n⚡ Hidden Discovery Pattern (Water Treeing):")
    try:
        result = session.sql("""
            SELECT 
                COUNT(DISTINCT a.asset_id) as cable_count,
                COUNT(*) as dip_events,
                ROUND(SUM(cfp.estimated_replacement_cost), 0) as replacement_cost,
                SUM(cfp.customer_impact_count) as customers_at_risk
            FROM RISK_PLANNING_DB.ATOMIC.ASSET a
            JOIN RISK_PLANNING_DB.ATOMIC.AMI_READING ami ON a.asset_id = ami.asset_id
            LEFT JOIN RISK_PLANNING_DB.ML.CABLE_FAILURE_PREDICTION cfp ON a.asset_id = cfp.asset_id
            WHERE a.asset_type = 'UNDERGROUND_CABLE'
              AND ami.rain_correlated_dip = TRUE
        """).collect()
        row = result[0]
        print(f"   • Pattern: XLPE cables with rain-correlated voltage dips")
        print(f"   • Cables affected: {row['CABLE_COUNT']}")
        print(f"   • Rain-correlated dip events: {row['DIP_EVENTS']}")
        print(f"   • Est. replacement cost: ${row['REPLACEMENT_COST']:,.0f}")
        print(f"   • Customers at risk: {row['CUSTOMERS_AT_RISK']:,}")
    except Exception as e:
        print(f"   ⚠️  Could not verify Hidden Discovery: {e}")
    
    # Load agent config
    print("\n📋 Agent Configuration:")
    try:
        with open("vigil_agent.json", "r") as f:
            config = json.load(f)
        print(f"   • Name: {config['name']}")
        print(f"   • Tools: {', '.join([t['tool_name'] for t in config['tools']])}")
        print(f"   • Sample questions: {len(config['sample_questions'])}")
        print(f"   • Agent personas: {len(config['agent_personas']['personas'])}")
    except Exception as e:
        print(f"   ⚠️  Could not load config: {e}")
    
    # Print deployment instructions
    print("\n" + "=" * 60)
    print("📝 DEPLOYMENT INSTRUCTIONS")
    print("=" * 60)
    
    print("""
1. Open Snowsight in your browser

2. Navigate to: AI & ML → Cortex Agents

3. Click "Create Agent" or "+" button

4. Configure the agent:

   Name: VIGIL_RISK_AGENT
   
   Description: 
   AI agent for utility vegetation and infrastructure risk planning.
   Combines data queries with ML insights and Water Treeing detection.
   
   Model: mistral-large (recommended) or llama3.1-70b
   
   Instructions:
   You are VIGIL, an AI assistant for utility vegetation and infrastructure 
   risk planning. You help vegetation managers, grid operators, and safety 
   teams understand asset health, vegetation compliance, and fire risk.
   
   CRITICAL: For 'Hidden Discovery' or 'Water Treeing' questions, search for 
   rain-correlated voltage dips in underground cables - there's a systemic 
   issue with 150+ XLPE cables showing moisture degradation!
   
   Always calculate days until fire season (June 1) for urgency context.
   Format currency with $ and commas. Highlight Tier 3 fire district risks.

5. Add Tools:

   Tool 1 - Data Analyst (Cortex Analyst):
   - Name: data_analyst
   - Semantic Model: @RISK_PLANNING_DB.CONSTRUCTION_RISK.SEMANTIC_MODELS/risk_semantic_model.yaml
   
   Tool 2 - GO95 Search (Cortex Search):
   - Name: go95_search  
   - Service: RISK_PLANNING_DB.DOCS.GO95_SEARCH_SERVICE
   - Max Results: 10
   
   Tool 3 - Vegetation Search (Cortex Search):
   - Name: vegetation_search
   - Service: RISK_PLANNING_DB.DOCS.VEGETATION_SEARCH_SERVICE
   - Max Results: 10
   
   Tool 4 - Work Order Search (Cortex Search):
   - Name: work_order_search
   - Service: RISK_PLANNING_DB.DOCS.WORK_ORDER_SEARCH_SERVICE
   - Max Results: 10
   
   Tool 5 - AMI Anomaly Search (Cortex Search):
   - Name: ami_anomaly_search
   - Service: RISK_PLANNING_DB.DOCS.AMI_ANOMALY_SEARCH_SERVICE
   - Max Results: 15
   - Description: KEY FOR HIDDEN DISCOVERY - search rain-correlated voltage dips

6. Test with these sample questions:
   - "What is the asset portfolio health summary?"
   - "How many days until fire season?"
   - "Show me GO95 compliance status by region"
   - "What is the Hidden Discovery pattern?"
   - "Search for rain correlated voltage dips"
   - "What underground cables need replacement?"

7. Click "Create" to deploy the agent
""")
    
    print("=" * 60)
    print("✅ Prerequisites verified! Ready for UI deployment.")
    print("=" * 60)
    
    session.close()


def main():
    parser = argparse.ArgumentParser(description="Deploy VIGIL Risk Agent")
    parser.add_argument("--connection", default="demo", help="Snowflake connection name")
    args = parser.parse_args()
    
    verify_and_print_instructions(args.connection)


if __name__ == "__main__":
    main()
