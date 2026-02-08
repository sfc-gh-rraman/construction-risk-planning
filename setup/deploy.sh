#!/bin/bash
#=============================================================================
# VIGIL Risk Planning - Complete Deployment Script
#=============================================================================
# Deploys the complete VIGIL platform to Snowflake
#
# Prerequisites:
# 1. Snowflake CLI (snow) installed and configured with connection 'demo'
# 2. Docker installed and running (for SPCS deployment)
# 3. Node.js 18+ (for local frontend development)
# 4. Python 3.10+ (for local backend development)
#=============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."
SQL_DIR="${SCRIPT_DIR}/sql"
SPCS_DIR="${SCRIPT_DIR}/spcs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🌲⚡🔥 VIGIL Risk Planning - Deployment Script 🔥⚡🌲        ║"
echo "║                                                                ║"
echo "║   Vegetation & Infrastructure Grid Intelligence Layer          ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse arguments
SKIP_SPCS=false
CONNECTION="demo"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-spcs) SKIP_SPCS=true ;;
        --connection) CONNECTION="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo -e "${YELLOW}Configuration:${NC}"
echo "  Connection: ${CONNECTION}"
echo "  Skip SPCS: ${SKIP_SPCS}"
echo ""

# Function to run SQL file
run_sql() {
    local file=$1
    local desc=$2
    echo -e "${BLUE}[SQL]${NC} ${desc}..."
    snow sql -f "${file}" -c "${CONNECTION}" --format json > /dev/null 2>&1 || {
        echo -e "${RED}  ERROR: Failed to execute ${file}${NC}"
        return 1
    }
    echo -e "${GREEN}  ✓ Complete${NC}"
}

#=============================================================================
# Step 1: Database Setup
#=============================================================================
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 1: Database Setup${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

run_sql "${SQL_DIR}/01_create_database.sql" "Creating database, schemas, and warehouses"
run_sql "${SQL_DIR}/02_create_tables.sql" "Creating tables"

#=============================================================================
# Step 2: Sample Data Generation
#=============================================================================
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 2: Sample Data Generation${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

run_sql "${SQL_DIR}/03_generate_sample_data.sql" "Generating locations, circuits, assets, vegetation (Part 1)"
run_sql "${SQL_DIR}/04_generate_sample_data_part2.sql" "Generating risk assessments, work orders, AMI data (Part 2)"

#=============================================================================
# Step 3: Cortex Setup
#=============================================================================
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 3: Cortex Search & Semantic Model Setup${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

run_sql "${SQL_DIR}/05_cortex_setup.sql" "Setting up Cortex Search services and documents"

# Upload semantic model
echo -e "${BLUE}[STAGE]${NC} Uploading semantic model..."
snow stage put "${SQL_DIR}/risk_semantic_model.yaml" \
    "@RISK_PLANNING_DB.CONSTRUCTION_RISK.SEMANTIC_MODELS" \
    -c "${CONNECTION}" --auto-compress false --overwrite > /dev/null 2>&1 || {
    echo -e "${YELLOW}  WARNING: Could not upload semantic model (may already exist)${NC}"
}
echo -e "${GREEN}  ✓ Complete${NC}"

#=============================================================================
# Step 4: Verify Data
#=============================================================================
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 4: Verify Data${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}[VERIFY]${NC} Checking data counts..."

snow sql -c "${CONNECTION}" -q "
SELECT 'Locations' as TABLE_NAME, COUNT(*) as ROW_COUNT FROM RISK_PLANNING_DB.ATOMIC.LOCATION
UNION ALL SELECT 'Circuits', COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.CIRCUIT
UNION ALL SELECT 'Assets', COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.ASSET
UNION ALL SELECT 'Vegetation', COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.VEGETATION_ENCROACHMENT
UNION ALL SELECT 'Risk Assessments', COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.RISK_ASSESSMENT
UNION ALL SELECT 'Work Orders', COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.WORK_ORDER
UNION ALL SELECT 'AMI Readings', COUNT(*) FROM RISK_PLANNING_DB.ATOMIC.AMI_READING
UNION ALL SELECT 'Cable Predictions', COUNT(*) FROM RISK_PLANNING_DB.ML.CABLE_FAILURE_PREDICTION;
" --format table

echo -e "${GREEN}  ✓ Data verification complete${NC}"

#=============================================================================
# Step 5: SPCS Deployment (Optional)
#=============================================================================
if [ "$SKIP_SPCS" = false ]; then
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Step 5: SPCS Deployment${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    echo -e "${BLUE}[SPCS]${NC} Creating compute pool and image repository..."
    run_sql "${SQL_DIR}/06_spcs_deployment.sql" "Setting up SPCS infrastructure"
    
    echo ""
    echo -e "${YELLOW}To complete SPCS deployment:${NC}"
    echo "  1. Build and push Docker images:"
    echo "     cd ${SPCS_DIR} && ./build_and_push.sh"
    echo ""
    echo "  2. Upload spec file:"
    echo "     snow stage put ${SPCS_DIR}/spec.yaml @RISK_PLANNING_DB.SPCS.APP_STAGE -c ${CONNECTION}"
    echo ""
    echo "  3. Create/start service (in Snowflake):"
    echo "     CREATE SERVICE SPCS.VIGIL_SERVICE ... (see 06_spcs_deployment.sql)"
    echo ""
    echo "  4. Get endpoint URL:"
    echo "     SHOW ENDPOINTS IN SERVICE SPCS.VIGIL_SERVICE;"
else
    echo ""
    echo -e "${YELLOW}Skipping SPCS deployment (--skip-spcs flag set)${NC}"
fi

#=============================================================================
# Complete
#=============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}║   ✅ VIGIL Deployment Complete!                                ║${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Database:${NC} RISK_PLANNING_DB"
echo -e "${YELLOW}Assets:${NC} ~5,000 across 5 regions (NorCal, SoCal, PNW, Southwest, Mountain)"
echo ""
echo -e "${YELLOW}For local development:${NC}"
echo "  Backend:  cd ${PROJECT_ROOT}/copilot/backend && pip install -r requirements.txt && python -m api.main"
echo "  Frontend: cd ${PROJECT_ROOT}/copilot/frontend && npm install && npm run dev"
echo ""
echo -e "${YELLOW}Hidden Discovery:${NC} Ask the copilot 'What's the hidden discovery?' to reveal Water Treeing detection!"
echo ""
