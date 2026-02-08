#!/bin/bash
# =============================================================================
# VIGIL Risk-Based Planning - Snowflake Deployment Script
# =============================================================================
set -e
set -o pipefail

# Configuration
CONNECTION="${SNOWFLAKE_CONNECTION:-demo}"
DATABASE="${SNOWFLAKE_DATABASE:-RISK_PLANNING_DB}"
WAREHOUSE="${SNOWFLAKE_WAREHOUSE:-COMPUTE_WH}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
DEPLOY_DDL=true
DEPLOY_DATA=true
DEPLOY_CORTEX=true
DEPLOY_NOTEBOOKS=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--connection) CONNECTION="$2"; shift 2 ;;
        --only-ddl) DEPLOY_DATA=false; DEPLOY_CORTEX=false; DEPLOY_NOTEBOOKS=false; shift ;;
        --only-data) DEPLOY_DDL=false; DEPLOY_CORTEX=false; DEPLOY_NOTEBOOKS=false; shift ;;
        --only-cortex) DEPLOY_DDL=false; DEPLOY_DATA=false; DEPLOY_NOTEBOOKS=false; shift ;;
        --only-notebooks) DEPLOY_DDL=false; DEPLOY_DATA=false; DEPLOY_CORTEX=false; shift ;;
        *) shift ;;
    esac
done

print_message "$CYAN" "
██╗   ██╗██╗ ██████╗ ██╗██╗     
██║   ██║██║██╔════╝ ██║██║     
██║   ██║██║██║  ███╗██║██║     
╚██╗ ██╔╝██║██║   ██║██║██║     
 ╚████╔╝ ██║╚██████╔╝██║███████╗
  ╚═══╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝
Risk-Based Planning Intelligence Platform
"

print_message "$BLUE" "=============================================="
print_message "$BLUE" "  Snowflake Deployment"
print_message "$BLUE" "=============================================="
print_message "$YELLOW" "Connection: $CONNECTION"
print_message "$YELLOW" "Database: $DATABASE"
echo ""

# =============================================================================
# STEP 1: Deploy DDL (Database, Schemas, Tables)
# =============================================================================
if [ "$DEPLOY_DDL" = true ]; then
    print_message "$BLUE" "📦 Step 1: Deploying DDL..."
    
    for sql_file in "$SCRIPT_DIR"/ddl/*.sql; do
        if [ -f "$sql_file" ]; then
            filename=$(basename "$sql_file")
            print_message "$GREEN" "  Executing: $filename"
            snow sql -f "$sql_file" -c "$CONNECTION" > /dev/null 2>&1 || {
                print_message "$YELLOW" "  Warning: Some statements in $filename may have failed (continuing...)"
            }
        fi
    done
    
    print_message "$GREEN" "✓ DDL deployment complete"
    echo ""
fi

# =============================================================================
# STEP 2: Generate and Load Synthetic Data
# =============================================================================
if [ "$DEPLOY_DATA" = true ]; then
    print_message "$BLUE" "📊 Step 2: Deploying Data..."
    
    # Create data directory
    mkdir -p "$SCRIPT_DIR/data/synthetic"
    
    # Generate synthetic data if not exists
    if [ ! -f "$SCRIPT_DIR/data/synthetic/assets.parquet" ]; then
        print_message "$GREEN" "  Generating synthetic data..."
        cd "$SCRIPT_DIR/scripts"
        python3 generate_synthetic_data.py
        cd "$SCRIPT_DIR"
    fi
    
    # Create stage
    print_message "$GREEN" "  Creating data stage..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    CREATE OR REPLACE STAGE RAW.DATA_STAGE 
        DIRECTORY = (ENABLE = TRUE);
    " > /dev/null
    
    # Upload parquet files
    print_message "$GREEN" "  Uploading locations.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/locations.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading circuits.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/circuits.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading assets.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/assets.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading vegetation.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/vegetation.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading ami_readings.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/ami_readings.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading work_orders.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/work_orders.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading weather.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/weather.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading risk_assessments.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/risk_assessments.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading cable_predictions.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/cable_predictions.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading compliance_docs.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/compliance_docs.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    print_message "$GREEN" "  Uploading monthly_snapshots.parquet..."
    snow stage copy "$SCRIPT_DIR/data/synthetic/monthly_snapshots.parquet" "@${DATABASE}.RAW.DATA_STAGE" --overwrite -c "$CONNECTION" > /dev/null
    
    # Refresh stage
    snow sql -c "$CONNECTION" -q "ALTER STAGE ${DATABASE}.RAW.DATA_STAGE REFRESH;" > /dev/null
    
    # Load LOCATION table
    print_message "$GREEN" "  Loading LOCATION table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO LOCATION (
        LOCATION_ID, ZONE_NAME, ZONE_TYPE, FIRE_THREAT_TIER, HFTD_FLAG,
        STATE, COUNTY, REGION, CENTER_LATITUDE, CENTER_LONGITUDE,
        H3_INDEX, AREA_SQUARE_MILES, AVG_WIND_SPEED_MPH, AVG_ANNUAL_RAINFALL_IN,
        VEGETATION_DENSITY, TERRAIN_TYPE
    )
    SELECT 
        \$1:LOCATION_ID::VARCHAR,
        \$1:ZONE_NAME::VARCHAR,
        \$1:ZONE_TYPE::VARCHAR,
        \$1:FIRE_THREAT_TIER::VARCHAR,
        \$1:HFTD_FLAG::BOOLEAN,
        \$1:STATE::VARCHAR,
        \$1:COUNTY::VARCHAR,
        \$1:REGION::VARCHAR,
        \$1:CENTER_LATITUDE::FLOAT,
        \$1:CENTER_LONGITUDE::FLOAT,
        \$1:H3_INDEX::VARCHAR,
        \$1:AREA_SQUARE_MILES::FLOAT,
        \$1:AVG_WIND_SPEED_MPH::FLOAT,
        \$1:AVG_ANNUAL_RAINFALL_IN::FLOAT,
        \$1:VEGETATION_DENSITY::VARCHAR,
        \$1:TERRAIN_TYPE::VARCHAR
    FROM @RAW.DATA_STAGE/locations.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load CIRCUIT table
    print_message "$GREEN" "  Loading CIRCUIT table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO CIRCUIT (
        CIRCUIT_ID, CIRCUIT_NAME, FEEDER_ID, SUBSTATION_NAME, SUBSTATION_ID,
        DISTRICT, DIVISION, VOLTAGE_CLASS, CIRCUIT_TYPE, CONSTRUCTION_TYPE,
        TOTAL_MILES, OVERHEAD_MILES, UNDERGROUND_MILES, POLE_COUNT, TRANSFORMER_COUNT,
        CUSTOMER_COUNT, LOCATION_ID, FIRE_THREAT_TIER, PRIORITY_TIER,
        SAIDI_MINUTES, SAIFI_COUNT, MAIFI_COUNT,
        LAST_PATROL_DATE, LAST_TRIM_DATE, TRIM_CYCLE_YEARS, NEXT_SCHEDULED_TRIM
    )
    SELECT 
        \$1:CIRCUIT_ID::VARCHAR,
        \$1:CIRCUIT_NAME::VARCHAR,
        \$1:FEEDER_ID::VARCHAR,
        \$1:SUBSTATION_NAME::VARCHAR,
        \$1:SUBSTATION_ID::VARCHAR,
        \$1:DISTRICT::VARCHAR,
        \$1:DIVISION::VARCHAR,
        \$1:VOLTAGE_CLASS::VARCHAR,
        \$1:CIRCUIT_TYPE::VARCHAR,
        \$1:CONSTRUCTION_TYPE::VARCHAR,
        \$1:TOTAL_MILES::FLOAT,
        \$1:OVERHEAD_MILES::FLOAT,
        \$1:UNDERGROUND_MILES::FLOAT,
        \$1:POLE_COUNT::INT,
        \$1:TRANSFORMER_COUNT::INT,
        \$1:CUSTOMER_COUNT::INT,
        \$1:LOCATION_ID::VARCHAR,
        \$1:FIRE_THREAT_TIER::VARCHAR,
        \$1:PRIORITY_TIER::VARCHAR,
        \$1:SAIDI_MINUTES::FLOAT,
        \$1:SAIFI_COUNT::FLOAT,
        \$1:MAIFI_COUNT::FLOAT,
        \$1:LAST_PATROL_DATE::DATE,
        \$1:LAST_TRIM_DATE::DATE,
        \$1:TRIM_CYCLE_YEARS::INT,
        \$1:NEXT_SCHEDULED_TRIM::DATE
    FROM @RAW.DATA_STAGE/circuits.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load ASSET table
    print_message "$GREEN" "  Loading ASSET table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO ASSET (
        ASSET_ID, ASSET_NAME, ASSET_TYPE, ASSET_SUBTYPE,
        CIRCUIT_ID, LOCATION_ID, PARENT_ASSET_ID,
        MANUFACTURER, MODEL, INSTALL_DATE, EXPECTED_LIFE_YEARS, AGE_YEARS,
        VOLTAGE_CLASS, PHASE, RATED_CAPACITY,
        LATITUDE, LONGITUDE, ELEVATION_FT, SPAN_LENGTH_FT, HEIGHT_FT, DEPTH_FT,
        CONDITION_SCORE, LAST_INSPECTION_DATE, LAST_INSPECTION_TYPE, REPLACEMENT_PRIORITY,
        INSULATION_TYPE, CABLE_JACKET, SOIL_TYPE, MOISTURE_EXPOSURE,
        FAILURE_PROBABILITY, IGNITION_RISK_SCORE, COMPOSITE_RISK_SCORE, RISK_SCORE_DATE,
        STATUS, OPERATIONAL_FLAG
    )
    SELECT 
        \$1:ASSET_ID::VARCHAR,
        \$1:ASSET_NAME::VARCHAR,
        \$1:ASSET_TYPE::VARCHAR,
        \$1:ASSET_SUBTYPE::VARCHAR,
        \$1:CIRCUIT_ID::VARCHAR,
        \$1:LOCATION_ID::VARCHAR,
        \$1:PARENT_ASSET_ID::VARCHAR,
        \$1:MANUFACTURER::VARCHAR,
        \$1:MODEL::VARCHAR,
        \$1:INSTALL_DATE::DATE,
        \$1:EXPECTED_LIFE_YEARS::INT,
        \$1:AGE_YEARS::INT,
        \$1:VOLTAGE_CLASS::VARCHAR,
        \$1:PHASE::VARCHAR,
        \$1:RATED_CAPACITY::FLOAT,
        \$1:LATITUDE::FLOAT,
        \$1:LONGITUDE::FLOAT,
        \$1:ELEVATION_FT::FLOAT,
        \$1:SPAN_LENGTH_FT::FLOAT,
        \$1:HEIGHT_FT::FLOAT,
        \$1:DEPTH_FT::FLOAT,
        \$1:CONDITION_SCORE::INT,
        \$1:LAST_INSPECTION_DATE::DATE,
        \$1:LAST_INSPECTION_TYPE::VARCHAR,
        \$1:REPLACEMENT_PRIORITY::VARCHAR,
        \$1:INSULATION_TYPE::VARCHAR,
        \$1:CABLE_JACKET::VARCHAR,
        \$1:SOIL_TYPE::VARCHAR,
        \$1:MOISTURE_EXPOSURE::VARCHAR,
        \$1:FAILURE_PROBABILITY::FLOAT,
        \$1:IGNITION_RISK_SCORE::FLOAT,
        \$1:COMPOSITE_RISK_SCORE::FLOAT,
        \$1:RISK_SCORE_DATE::DATE,
        \$1:STATUS::VARCHAR,
        \$1:OPERATIONAL_FLAG::BOOLEAN
    FROM @RAW.DATA_STAGE/assets.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load VEGETATION_ENCROACHMENT table
    print_message "$GREEN" "  Loading VEGETATION_ENCROACHMENT table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO VEGETATION_ENCROACHMENT (
        ENCROACHMENT_ID, ASSET_ID, MEASUREMENT_DATE, MEASUREMENT_SOURCE,
        TREE_SPECIES, TREE_HEIGHT_FT, TREE_CANOPY_DIAMETER_FT, TREE_HEALTH,
        DISTANCE_TO_CONDUCTOR_FT, HORIZONTAL_CLEARANCE_FT, VERTICAL_CLEARANCE_FT,
        GROWTH_RATE_ANNUAL_FT, GROWTH_RATE_CATEGORY,
        PREDICTED_ENCROACHMENT_30D_FT, PREDICTED_ENCROACHMENT_90D_FT, DAYS_TO_CRITICAL,
        REQUIRED_CLEARANCE_FT, CLEARANCE_STATUS, IN_VIOLATION,
        STRIKE_POTENTIAL, FALL_IN_POTENTIAL, BLOW_IN_POTENTIAL
    )
    SELECT 
        \$1:ENCROACHMENT_ID::VARCHAR,
        \$1:ASSET_ID::VARCHAR,
        \$1:MEASUREMENT_DATE::DATE,
        \$1:MEASUREMENT_SOURCE::VARCHAR,
        \$1:TREE_SPECIES::VARCHAR,
        \$1:TREE_HEIGHT_FT::FLOAT,
        \$1:TREE_CANOPY_DIAMETER_FT::FLOAT,
        \$1:TREE_HEALTH::VARCHAR,
        \$1:DISTANCE_TO_CONDUCTOR_FT::FLOAT,
        \$1:HORIZONTAL_CLEARANCE_FT::FLOAT,
        \$1:VERTICAL_CLEARANCE_FT::FLOAT,
        \$1:GROWTH_RATE_ANNUAL_FT::FLOAT,
        \$1:GROWTH_RATE_CATEGORY::VARCHAR,
        \$1:PREDICTED_ENCROACHMENT_30D_FT::FLOAT,
        \$1:PREDICTED_ENCROACHMENT_90D_FT::FLOAT,
        \$1:DAYS_TO_CRITICAL::INT,
        \$1:REQUIRED_CLEARANCE_FT::FLOAT,
        \$1:CLEARANCE_STATUS::VARCHAR,
        \$1:IN_VIOLATION::BOOLEAN,
        \$1:STRIKE_POTENTIAL::VARCHAR,
        \$1:FALL_IN_POTENTIAL::BOOLEAN,
        \$1:BLOW_IN_POTENTIAL::BOOLEAN
    FROM @RAW.DATA_STAGE/vegetation.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load AMI_READING table
    print_message "$GREEN" "  Loading AMI_READING table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO AMI_READING (
        READING_ID, ASSET_ID, READING_TIMESTAMP,
        VOLTAGE_A, VOLTAGE_B, VOLTAGE_C, VOLTAGE_AVG, VOLTAGE_NOMINAL,
        VOLTAGE_DIP_PCT, VOLTAGE_DIP_FLAG, DIP_DURATION_SECONDS,
        RAINFALL_MM, SOIL_MOISTURE_PCT, TEMPERATURE_F,
        RAIN_CORRELATED_DIP, CONSECUTIVE_DIP_COUNT,
        CURRENT_A, CURRENT_B, CURRENT_C, POWER_KW, POWER_FACTOR,
        READING_QUALITY
    )
    SELECT 
        \$1:READING_ID::VARCHAR,
        \$1:ASSET_ID::VARCHAR,
        \$1:READING_TIMESTAMP::TIMESTAMP_NTZ,
        \$1:VOLTAGE_A::FLOAT,
        \$1:VOLTAGE_B::FLOAT,
        \$1:VOLTAGE_C::FLOAT,
        \$1:VOLTAGE_AVG::FLOAT,
        \$1:VOLTAGE_NOMINAL::FLOAT,
        \$1:VOLTAGE_DIP_PCT::FLOAT,
        \$1:VOLTAGE_DIP_FLAG::BOOLEAN,
        \$1:DIP_DURATION_SECONDS::INT,
        \$1:RAINFALL_MM::FLOAT,
        \$1:SOIL_MOISTURE_PCT::FLOAT,
        \$1:TEMPERATURE_F::FLOAT,
        \$1:RAIN_CORRELATED_DIP::BOOLEAN,
        \$1:CONSECUTIVE_DIP_COUNT::INT,
        \$1:CURRENT_A::FLOAT,
        \$1:CURRENT_B::FLOAT,
        \$1:CURRENT_C::FLOAT,
        \$1:POWER_KW::FLOAT,
        \$1:POWER_FACTOR::FLOAT,
        \$1:READING_QUALITY::VARCHAR
    FROM @RAW.DATA_STAGE/ami_readings.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load WORK_ORDER table
    print_message "$GREEN" "  Loading WORK_ORDER table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO WORK_ORDER (
        WORK_ORDER_ID, WORK_ORDER_NUMBER, ASSET_ID, CIRCUIT_ID, LOCATION_ID,
        ACTIVITY_TYPE, WORK_TYPE, PRIORITY, DESCRIPTION, SCOPE_NOTES,
        ESTIMATED_HOURS, ESTIMATED_COST, TREES_TO_TRIM, ESTIMATED_MILES, SPECIES_TARGET,
        REQUESTED_DATE, SCHEDULED_DATE, DUE_DATE, COMPLETION_DATE, STATUS,
        ACTUAL_HOURS, ACTUAL_COST, MILES_TRIMMED, TREES_TRIMMED,
        ASSIGNED_CREW, CONTRACTOR,
        PRE_WORK_RISK_SCORE, POST_WORK_RISK_SCORE, RISK_REDUCTION_VALUE,
        CREATED_BY, CREATED_SOURCE
    )
    SELECT 
        \$1:WORK_ORDER_ID::VARCHAR,
        \$1:WORK_ORDER_NUMBER::VARCHAR,
        \$1:ASSET_ID::VARCHAR,
        \$1:CIRCUIT_ID::VARCHAR,
        \$1:LOCATION_ID::VARCHAR,
        \$1:ACTIVITY_TYPE::VARCHAR,
        \$1:WORK_TYPE::VARCHAR,
        \$1:PRIORITY::VARCHAR,
        \$1:DESCRIPTION::VARCHAR,
        \$1:SCOPE_NOTES::VARCHAR,
        \$1:ESTIMATED_HOURS::FLOAT,
        \$1:ESTIMATED_COST::FLOAT,
        \$1:TREES_TO_TRIM::INT,
        \$1:ESTIMATED_MILES::FLOAT,
        \$1:SPECIES_TARGET::VARCHAR,
        \$1:REQUESTED_DATE::DATE,
        \$1:SCHEDULED_DATE::DATE,
        \$1:DUE_DATE::DATE,
        \$1:COMPLETION_DATE::DATE,
        \$1:STATUS::VARCHAR,
        \$1:ACTUAL_HOURS::FLOAT,
        \$1:ACTUAL_COST::FLOAT,
        \$1:MILES_TRIMMED::FLOAT,
        \$1:TREES_TRIMMED::INT,
        \$1:ASSIGNED_CREW::VARCHAR,
        \$1:CONTRACTOR::VARCHAR,
        \$1:PRE_WORK_RISK_SCORE::FLOAT,
        \$1:POST_WORK_RISK_SCORE::FLOAT,
        \$1:RISK_REDUCTION_VALUE::FLOAT,
        \$1:CREATED_BY::VARCHAR,
        \$1:CREATED_SOURCE::VARCHAR
    FROM @RAW.DATA_STAGE/work_orders.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load WEATHER_FORECAST table
    print_message "$GREEN" "  Loading WEATHER_FORECAST table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO WEATHER_FORECAST (
        FORECAST_ID, LOCATION_ID, FORECAST_DATE, FORECAST_HOUR, SOURCE, ISSUED_AT,
        TEMPERATURE_F, TEMPERATURE_MAX_F, TEMPERATURE_MIN_F,
        WIND_SPEED_MPH, WIND_GUST_MPH, WIND_DIRECTION,
        HUMIDITY_PCT, PRECIPITATION_PROBABILITY, PRECIPITATION_AMOUNT_IN, PRECIPITATION_TYPE,
        RED_FLAG_WARNING, FIRE_WEATHER_WATCH, WIND_ADVISORY,
        FIRE_WEATHER_INDEX, PSPS_PROBABILITY
    )
    SELECT 
        \$1:FORECAST_ID::VARCHAR,
        \$1:LOCATION_ID::VARCHAR,
        \$1:FORECAST_DATE::DATE,
        \$1:FORECAST_HOUR::INT,
        \$1:SOURCE::VARCHAR,
        \$1:ISSUED_AT::TIMESTAMP_NTZ,
        \$1:TEMPERATURE_F::FLOAT,
        \$1:TEMPERATURE_MAX_F::FLOAT,
        \$1:TEMPERATURE_MIN_F::FLOAT,
        \$1:WIND_SPEED_MPH::FLOAT,
        \$1:WIND_GUST_MPH::FLOAT,
        \$1:WIND_DIRECTION::VARCHAR,
        \$1:HUMIDITY_PCT::FLOAT,
        \$1:PRECIPITATION_PROBABILITY::FLOAT,
        \$1:PRECIPITATION_AMOUNT_IN::FLOAT,
        \$1:PRECIPITATION_TYPE::VARCHAR,
        \$1:RED_FLAG_WARNING::BOOLEAN,
        \$1:FIRE_WEATHER_WATCH::BOOLEAN,
        \$1:WIND_ADVISORY::BOOLEAN,
        \$1:FIRE_WEATHER_INDEX::FLOAT,
        \$1:PSPS_PROBABILITY::FLOAT
    FROM @RAW.DATA_STAGE/weather.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load RISK_ASSESSMENT table
    print_message "$GREEN" "  Loading RISK_ASSESSMENT table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO RISK_ASSESSMENT (
        ASSESSMENT_ID, ASSET_ID, ASSESSMENT_DATE,
        COMPOSITE_RISK_SCORE, RISK_TIER, RISK_RANK,
        FAILURE_PROBABILITY, IGNITION_RISK, OUTAGE_IMPACT_SCORE, SAFETY_RISK_SCORE,
        AGE_FACTOR, CONDITION_FACTOR, VEGETATION_FACTOR, WEATHER_FACTOR, LOAD_FACTOR, HISTORICAL_FACTOR,
        MODEL_VERSION, MODEL_CONFIDENCE,
        RECOMMENDED_ACTION, RECOMMENDED_PRIORITY, ESTIMATED_RISK_REDUCTION
    )
    SELECT 
        \$1:ASSESSMENT_ID::VARCHAR,
        \$1:ASSET_ID::VARCHAR,
        \$1:ASSESSMENT_DATE::DATE,
        \$1:COMPOSITE_RISK_SCORE::FLOAT,
        \$1:RISK_TIER::VARCHAR,
        \$1:RISK_RANK::INT,
        \$1:FAILURE_PROBABILITY::FLOAT,
        \$1:IGNITION_RISK::FLOAT,
        \$1:OUTAGE_IMPACT_SCORE::FLOAT,
        \$1:SAFETY_RISK_SCORE::FLOAT,
        \$1:AGE_FACTOR::FLOAT,
        \$1:CONDITION_FACTOR::FLOAT,
        \$1:VEGETATION_FACTOR::FLOAT,
        \$1:WEATHER_FACTOR::FLOAT,
        \$1:LOAD_FACTOR::FLOAT,
        \$1:HISTORICAL_FACTOR::FLOAT,
        \$1:MODEL_VERSION::VARCHAR,
        \$1:MODEL_CONFIDENCE::FLOAT,
        \$1:RECOMMENDED_ACTION::VARCHAR,
        \$1:RECOMMENDED_PRIORITY::VARCHAR,
        \$1:ESTIMATED_RISK_REDUCTION::FLOAT
    FROM @RAW.DATA_STAGE/risk_assessments.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load CABLE_FAILURE_PREDICTION table (ML schema)
    print_message "$GREEN" "  Loading CABLE_FAILURE_PREDICTION table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ML;
    
    INSERT INTO CABLE_FAILURE_PREDICTION (
        PREDICTION_ID, ASSET_ID, PREDICTION_DATE, MODEL_ID,
        WATER_TREEING_PROBABILITY, WATER_TREEING_SEVERITY,
        FAILURE_PROBABILITY_30D, FAILURE_PROBABILITY_90D, FAILURE_PROBABILITY_1Y,
        VOLTAGE_DIP_FREQUENCY, RAIN_CORRELATION_SCORE, ANOMALY_SCORE,
        DIP_EVENTS_LAST_30D, DIP_EVENTS_LAST_90D, AVG_DIP_MAGNITUDE_PCT,
        RAIN_EVENTS_WITH_DIPS, RAIN_EVENTS_WITHOUT_DIPS,
        CABLE_AGE_YEARS, INSULATION_TYPE, MOISTURE_EXPOSURE,
        PROACTIVE_REPLACEMENT_COST, EMERGENCY_REPAIR_COST, REGULATORY_FINE_RISK,
        RECOMMENDED_ACTION, ACTION_URGENCY, PREDICTION_CONFIDENCE,
        TOP_ANOMALY_INDICATOR, DETECTION_METHOD
    )
    SELECT 
        \$1:PREDICTION_ID::VARCHAR,
        \$1:ASSET_ID::VARCHAR,
        \$1:PREDICTION_DATE::DATE,
        \$1:MODEL_ID::VARCHAR,
        \$1:WATER_TREEING_PROBABILITY::FLOAT,
        \$1:WATER_TREEING_SEVERITY::VARCHAR,
        \$1:FAILURE_PROBABILITY_30D::FLOAT,
        \$1:FAILURE_PROBABILITY_90D::FLOAT,
        \$1:FAILURE_PROBABILITY_1Y::FLOAT,
        \$1:VOLTAGE_DIP_FREQUENCY::FLOAT,
        \$1:RAIN_CORRELATION_SCORE::FLOAT,
        \$1:ANOMALY_SCORE::FLOAT,
        \$1:DIP_EVENTS_LAST_30D::INT,
        \$1:DIP_EVENTS_LAST_90D::INT,
        \$1:AVG_DIP_MAGNITUDE_PCT::FLOAT,
        \$1:RAIN_EVENTS_WITH_DIPS::INT,
        \$1:RAIN_EVENTS_WITHOUT_DIPS::INT,
        \$1:CABLE_AGE_YEARS::INT,
        \$1:INSULATION_TYPE::VARCHAR,
        \$1:MOISTURE_EXPOSURE::VARCHAR,
        \$1:PROACTIVE_REPLACEMENT_COST::FLOAT,
        \$1:EMERGENCY_REPAIR_COST::FLOAT,
        \$1:REGULATORY_FINE_RISK::FLOAT,
        \$1:RECOMMENDED_ACTION::VARCHAR,
        \$1:ACTION_URGENCY::VARCHAR,
        \$1:PREDICTION_CONFIDENCE::FLOAT,
        \$1:TOP_ANOMALY_INDICATOR::VARCHAR,
        \$1:DETECTION_METHOD::VARCHAR
    FROM @RAW.DATA_STAGE/cable_predictions.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load COMPLIANCE_DOCUMENT table
    print_message "$GREEN" "  Loading COMPLIANCE_DOCUMENT table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO COMPLIANCE_DOCUMENT (
        DOCUMENT_ID, DOCUMENT_TYPE, REGULATION_CODE, TITLE, SECTION, SUBSECTION,
        CONTENT, ASSET_TYPE, VOLTAGE_CLASS, FIRE_TIER,
        MIN_CLEARANCE_FT, RADIAL_CLEARANCE_FT, EFFECTIVE_DATE, LAST_UPDATED, SOURCE_URL
    )
    SELECT 
        \$1:DOCUMENT_ID::VARCHAR,
        \$1:DOCUMENT_TYPE::VARCHAR,
        \$1:REGULATION_CODE::VARCHAR,
        \$1:TITLE::VARCHAR,
        \$1:SECTION::VARCHAR,
        \$1:SUBSECTION::VARCHAR,
        \$1:CONTENT::VARCHAR,
        \$1:ASSET_TYPE::VARCHAR,
        \$1:VOLTAGE_CLASS::VARCHAR,
        \$1:FIRE_TIER::VARCHAR,
        \$1:MIN_CLEARANCE_FT::FLOAT,
        \$1:RADIAL_CLEARANCE_FT::FLOAT,
        \$1:EFFECTIVE_DATE::DATE,
        \$1:LAST_UPDATED::DATE,
        \$1:SOURCE_URL::VARCHAR
    FROM @RAW.DATA_STAGE/compliance_docs.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    # Load MONTHLY_SNAPSHOT table
    print_message "$GREEN" "  Loading MONTHLY_SNAPSHOT table..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ATOMIC;
    
    INSERT INTO MONTHLY_SNAPSHOT (
        SNAPSHOT_ID, CIRCUIT_ID, SNAPSHOT_DATE,
        HIGH_RISK_ASSET_COUNT, CRITICAL_RISK_ASSET_COUNT, AVG_RISK_SCORE, MAX_RISK_SCORE,
        TOTAL_SPANS, SPANS_REQUIRING_TRIM, SPANS_IN_VIOLATION,
        MILES_TRIMMED_MTD, MILES_TRIMMED_YTD,
        OPEN_WORK_ORDERS, COMPLETED_WORK_ORDERS_MTD, BACKLOG_DAYS,
        BUDGET_ALLOCATED, BUDGET_SPENT_MTD, BUDGET_SPENT_YTD, COST_PER_MILE,
        RISK_REDUCTION_VALUE_MTD, RISK_REDUCTION_VALUE_YTD, RISK_REDUCTION_PER_DOLLAR,
        OUTAGES_MTD, OUTAGE_MINUTES_MTD, VEG_CAUSED_OUTAGES_MTD,
        DAYS_TO_FIRE_SEASON, FIRE_SEASON_READINESS_PCT
    )
    SELECT 
        \$1:SNAPSHOT_ID::VARCHAR,
        \$1:CIRCUIT_ID::VARCHAR,
        \$1:SNAPSHOT_DATE::DATE,
        \$1:HIGH_RISK_ASSET_COUNT::INT,
        \$1:CRITICAL_RISK_ASSET_COUNT::INT,
        \$1:AVG_RISK_SCORE::FLOAT,
        \$1:MAX_RISK_SCORE::FLOAT,
        \$1:TOTAL_SPANS::INT,
        \$1:SPANS_REQUIRING_TRIM::INT,
        \$1:SPANS_IN_VIOLATION::INT,
        \$1:MILES_TRIMMED_MTD::FLOAT,
        \$1:MILES_TRIMMED_YTD::FLOAT,
        \$1:OPEN_WORK_ORDERS::INT,
        \$1:COMPLETED_WORK_ORDERS_MTD::INT,
        \$1:BACKLOG_DAYS::FLOAT,
        \$1:BUDGET_ALLOCATED::FLOAT,
        \$1:BUDGET_SPENT_MTD::FLOAT,
        \$1:BUDGET_SPENT_YTD::FLOAT,
        \$1:COST_PER_MILE::FLOAT,
        \$1:RISK_REDUCTION_VALUE_MTD::FLOAT,
        \$1:RISK_REDUCTION_VALUE_YTD::FLOAT,
        \$1:RISK_REDUCTION_PER_DOLLAR::FLOAT,
        \$1:OUTAGES_MTD::INT,
        \$1:OUTAGE_MINUTES_MTD::FLOAT,
        \$1:VEG_CAUSED_OUTAGES_MTD::INT,
        \$1:DAYS_TO_FIRE_SEASON::INT,
        \$1:FIRE_SEASON_READINESS_PCT::FLOAT
    FROM @RAW.DATA_STAGE/monthly_snapshots.parquet (FILE_FORMAT => 'RAW.PARQUET_FORMAT');
    " > /dev/null
    
    print_message "$GREEN" "✓ Data deployment complete"
    echo ""
fi

# =============================================================================
# STEP 3: Deploy Cortex (Semantic Model + Search Service)
# =============================================================================
if [ "$DEPLOY_CORTEX" = true ]; then
    print_message "$BLUE" "🧠 Step 3: Deploying Cortex..."
    
    # Create semantic models stage with DIRECTORY enabled
    print_message "$GREEN" "  Creating semantic models stage..."
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    CREATE STAGE IF NOT EXISTS CONSTRUCTION_RISK.SEMANTIC_MODELS
        DIRECTORY = (ENABLE = TRUE);
    " > /dev/null
    
    # Upload semantic model
    if [ -f "$SCRIPT_DIR/cortex/risk_semantic_model.yaml" ]; then
        print_message "$GREEN" "  Uploading semantic model..."
        snow stage copy "$SCRIPT_DIR/cortex/risk_semantic_model.yaml" "@${DATABASE}.CONSTRUCTION_RISK.SEMANTIC_MODELS" --overwrite -c "$CONNECTION" > /dev/null
        snow sql -c "$CONNECTION" -q "ALTER STAGE ${DATABASE}.CONSTRUCTION_RISK.SEMANTIC_MODELS REFRESH;" > /dev/null
    fi
    
    # Deploy Cortex Search
    print_message "$GREEN" "  Deploying Cortex Search service..."
    snow sql -f "$SCRIPT_DIR/cortex/deploy_search.sql" -c "$CONNECTION" > /dev/null 2>&1 || {
        print_message "$YELLOW" "  Note: Cortex Search may require additional setup"
    }
    
    print_message "$GREEN" "✓ Cortex deployment complete"
    echo ""
fi

# =============================================================================
# STEP 4: Deploy ML Notebooks
# =============================================================================
if [ "$DEPLOY_NOTEBOOKS" = true ]; then
    print_message "$BLUE" "📓 Step 4: Deploying ML Notebooks..."
    
    if [ -f "$SCRIPT_DIR/notebooks/deploy_notebooks.sh" ]; then
        cd "$SCRIPT_DIR/notebooks"
        bash deploy_notebooks.sh "$CONNECTION"
        cd "$SCRIPT_DIR"
    else
        print_message "$YELLOW" "  Note: Notebooks deployment script not found"
    fi
    
    print_message "$GREEN" "✓ Notebooks deployment complete"
    echo ""
fi

# =============================================================================
# SUMMARY
# =============================================================================
print_message "$CYAN" "=============================================="
print_message "$GREEN" "  🎉 Deployment Complete!"
print_message "$CYAN" "=============================================="

echo ""
print_message "$YELLOW" "📊 Data Summary:"
snow sql -c "$CONNECTION" -q "
SELECT 'LOCATION' as table_name, COUNT(*) as row_count FROM ${DATABASE}.ATOMIC.LOCATION
UNION ALL SELECT 'CIRCUIT', COUNT(*) FROM ${DATABASE}.ATOMIC.CIRCUIT
UNION ALL SELECT 'ASSET', COUNT(*) FROM ${DATABASE}.ATOMIC.ASSET
UNION ALL SELECT 'VEGETATION_ENCROACHMENT', COUNT(*) FROM ${DATABASE}.ATOMIC.VEGETATION_ENCROACHMENT
UNION ALL SELECT 'AMI_READING', COUNT(*) FROM ${DATABASE}.ATOMIC.AMI_READING
UNION ALL SELECT 'WORK_ORDER', COUNT(*) FROM ${DATABASE}.ATOMIC.WORK_ORDER
UNION ALL SELECT 'RISK_ASSESSMENT', COUNT(*) FROM ${DATABASE}.ATOMIC.RISK_ASSESSMENT
UNION ALL SELECT 'CABLE_FAILURE_PREDICTION', COUNT(*) FROM ${DATABASE}.ML.CABLE_FAILURE_PREDICTION
ORDER BY table_name;
"

echo ""
print_message "$YELLOW" "🔍 Hidden Discovery Check (Water Treeing):"
snow sql -c "$CONNECTION" -q "
SELECT 
    WATER_TREEING_SEVERITY,
    COUNT(*) as cable_count,
    ROUND(AVG(RAIN_CORRELATION_SCORE), 3) as avg_rain_correlation,
    ROUND(SUM(EMERGENCY_REPAIR_COST - PROACTIVE_REPLACEMENT_COST), 0) as potential_savings
FROM ${DATABASE}.ML.CABLE_FAILURE_PREDICTION
WHERE WATER_TREEING_SEVERITY IN ('MODERATE', 'SEVERE')
GROUP BY WATER_TREEING_SEVERITY
ORDER BY WATER_TREEING_SEVERITY;
"

echo ""
print_message "$YELLOW" "🔥 Fire Season Readiness:"
snow sql -c "$CONNECTION" -q "
SELECT 
    l.REGION,
    COUNT(DISTINCT a.ASSET_ID) as total_assets,
    SUM(CASE WHEN a.COMPOSITE_RISK_SCORE >= 60 THEN 1 ELSE 0 END) as high_risk_assets,
    SUM(CASE WHEN ve.CLEARANCE_STATUS IN ('VIOLATION', 'CRITICAL') THEN 1 ELSE 0 END) as veg_violations
FROM ${DATABASE}.ATOMIC.LOCATION l
LEFT JOIN ${DATABASE}.ATOMIC.ASSET a ON l.LOCATION_ID = a.LOCATION_ID
LEFT JOIN ${DATABASE}.ATOMIC.VEGETATION_ENCROACHMENT ve ON a.ASSET_ID = ve.ASSET_ID
GROUP BY l.REGION
ORDER BY l.REGION;
"

echo ""
print_message "$BLUE" "Next Steps:"
echo "  1. Open Snowsight and navigate to Notebooks"
echo "  2. Run the ML notebooks to generate predictions"
echo "  3. Check Cortex Analyst: SELECT * FROM TABLE(${DATABASE}.CONSTRUCTION_RISK.SEMANTIC_MODELS)"
echo "  4. Launch the VIGIL copilot application"
echo ""
