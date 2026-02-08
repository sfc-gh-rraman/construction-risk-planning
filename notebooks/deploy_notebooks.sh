#!/bin/bash
###############################################################################
# VIGIL Risk Planning - Deploy ML Notebooks to Snowflake
###############################################################################

set -e

CONNECTION="${1:-demo}"
DATABASE="RISK_PLANNING_DB"
SCHEMA="ML"
WAREHOUSE="RISK_ML_WH"
STAGE="${DATABASE}.${SCHEMA}.NOTEBOOKS_STAGE"

echo ""
echo "=============================================="
echo "  Deploying VIGIL ML Notebooks to Snowflake"
echo "=============================================="
echo "Connection: $CONNECTION"
echo "Database: $DATABASE"
echo "Schema: $SCHEMA"
echo ""

# Create stage for notebooks
echo "Creating notebooks stage..."
snow sql -c "$CONNECTION" -q "
USE DATABASE ${DATABASE};
USE SCHEMA ${SCHEMA};

CREATE STAGE IF NOT EXISTS NOTEBOOKS_STAGE
    DIRECTORY = (ENABLE = TRUE);
"

# Upload notebooks and environment file
echo ""
echo "Uploading notebooks..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${SCRIPT_DIR}/01_asset_health_predictor.ipynb" ]; then
    snow stage copy "${SCRIPT_DIR}/01_asset_health_predictor.ipynb" "@${STAGE}/" --overwrite -c "$CONNECTION"
    echo "  ✓ 01_asset_health_predictor.ipynb"
fi

if [ -f "${SCRIPT_DIR}/02_vegetation_growth_predictor.ipynb" ]; then
    snow stage copy "${SCRIPT_DIR}/02_vegetation_growth_predictor.ipynb" "@${STAGE}/" --overwrite -c "$CONNECTION"
    echo "  ✓ 02_vegetation_growth_predictor.ipynb"
fi

if [ -f "${SCRIPT_DIR}/03_ignition_risk_predictor.ipynb" ]; then
    snow stage copy "${SCRIPT_DIR}/03_ignition_risk_predictor.ipynb" "@${STAGE}/" --overwrite -c "$CONNECTION"
    echo "  ✓ 03_ignition_risk_predictor.ipynb"
fi

if [ -f "${SCRIPT_DIR}/04_cable_failure_predictor.ipynb" ]; then
    snow stage copy "${SCRIPT_DIR}/04_cable_failure_predictor.ipynb" "@${STAGE}/" --overwrite -c "$CONNECTION"
    echo "  ✓ 04_cable_failure_predictor.ipynb (HIDDEN DISCOVERY)"
fi

if [ -f "${SCRIPT_DIR}/environment.yml" ]; then
    snow stage copy "${SCRIPT_DIR}/environment.yml" "@${STAGE}/" --overwrite -c "$CONNECTION"
    echo "  ✓ environment.yml"
fi

# Refresh stage
snow sql -c "$CONNECTION" -q "ALTER STAGE ${STAGE} REFRESH;" > /dev/null

# Create notebooks in Snowflake
echo ""
echo "Creating Snowflake notebooks..."
snow sql -c "$CONNECTION" -q "
USE DATABASE ${DATABASE};
USE SCHEMA ${SCHEMA};

-- Asset Health Predictor Notebook
CREATE OR REPLACE NOTEBOOK ASSET_HEALTH_PREDICTOR_NB
  FROM '@${STAGE}/'
  MAIN_FILE = '01_asset_health_predictor.ipynb'
  QUERY_WAREHOUSE = '${WAREHOUSE}'
  COMMENT = 'Gradient Boosting model to predict asset health scores';

-- Vegetation Growth Predictor Notebook
CREATE OR REPLACE NOTEBOOK VEGETATION_GROWTH_PREDICTOR_NB
  FROM '@${STAGE}/'
  MAIN_FILE = '02_vegetation_growth_predictor.ipynb'
  QUERY_WAREHOUSE = '${WAREHOUSE}'
  COMMENT = 'Random Forest model for vegetation growth prediction with seasonal adjustment';

-- Ignition Risk Predictor Notebook
CREATE OR REPLACE NOTEBOOK IGNITION_RISK_PREDICTOR_NB
  FROM '@${STAGE}/'
  MAIN_FILE = '03_ignition_risk_predictor.ipynb'
  QUERY_WAREHOUSE = '${WAREHOUSE}'
  COMMENT = 'XGBoost classifier for wildfire ignition risk prediction';

-- Cable Failure Predictor Notebook (HIDDEN DISCOVERY)
CREATE OR REPLACE NOTEBOOK CABLE_FAILURE_PREDICTOR_NB
  FROM '@${STAGE}/'
  MAIN_FILE = '04_cable_failure_predictor.ipynb'
  QUERY_WAREHOUSE = '${WAREHOUSE}'
  COMMENT = 'XGBoost model for Water Treeing detection - THE HIDDEN DISCOVERY';

SELECT 'Notebooks created successfully' as status;
"

echo ""
echo "=============================================="
echo "✅ Notebook deployment complete!"
echo "=============================================="
echo ""
echo "📓 Notebooks available in Snowsight:"
echo "  - ${DATABASE}.${SCHEMA}.ASSET_HEALTH_PREDICTOR_NB"
echo "  - ${DATABASE}.${SCHEMA}.VEGETATION_GROWTH_PREDICTOR_NB"
echo "  - ${DATABASE}.${SCHEMA}.IGNITION_RISK_PREDICTOR_NB"
echo "  - ${DATABASE}.${SCHEMA}.CABLE_FAILURE_PREDICTOR_NB  ⚡ HIDDEN DISCOVERY"
echo ""
echo "To run in Snowsight:"
echo "  1. Go to Snowsight > Projects > Notebooks"
echo "  2. Select a notebook and click 'Run All'"
echo "  3. Predictions will be saved to ML.* tables"
echo ""
echo "ML Models:"
echo "  1. Asset Health Predictor    → ML.ASSET_HEALTH_PREDICTION"
echo "  2. Vegetation Growth         → ML.VEGETATION_GROWTH_PREDICTION"
echo "  3. Ignition Risk             → ML.IGNITION_RISK_PREDICTION"
echo "  4. Cable Failure (Water Treeing) → ML.CABLE_FAILURE_PREDICTION"
echo ""
echo "🔍 HIDDEN DISCOVERY: Run notebook 04 to detect Water Treeing"
echo "   in underground cables - invisible to visual inspection!"
echo ""
