-- ============================================================================
-- VIGIL Risk-Based Planning Intelligence Platform
-- ATOMIC Schema - Normalized Entity Tables
-- ============================================================================

USE DATABASE RISK_PLANNING_DB;
USE SCHEMA ATOMIC;

-- ============================================================================
-- LOCATION - Fire threat zones and districts
-- ============================================================================
CREATE OR REPLACE TABLE LOCATION (
    LOCATION_ID VARCHAR(50) PRIMARY KEY,
    ZONE_NAME VARCHAR(255) NOT NULL,
    ZONE_TYPE VARCHAR(50),               -- 'FIRE_DISTRICT', 'SERVICE_TERRITORY', 'COUNTY'
    
    -- Fire Threat Classification (CPUC)
    FIRE_THREAT_TIER VARCHAR(10),        -- 'TIER_1', 'TIER_2', 'TIER_3', 'NON_HFTD'
    HFTD_FLAG BOOLEAN DEFAULT FALSE,     -- High Fire Threat District
    
    -- Geography
    STATE VARCHAR(2),
    COUNTY VARCHAR(100),
    REGION VARCHAR(50),                  -- 'NORCAL', 'SOCAL', 'PNW', 'SOUTHWEST', 'MOUNTAIN'
    
    -- Spatial (H3 index for efficient geo queries)
    CENTER_LATITUDE FLOAT,
    CENTER_LONGITUDE FLOAT,
    H3_INDEX VARCHAR(20),                -- H3 geospatial index
    AREA_SQUARE_MILES FLOAT,
    
    -- Risk Factors
    AVG_WIND_SPEED_MPH FLOAT,
    AVG_ANNUAL_RAINFALL_IN FLOAT,
    VEGETATION_DENSITY VARCHAR(20),      -- 'LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH'
    TERRAIN_TYPE VARCHAR(50),            -- 'FLAT', 'HILLY', 'MOUNTAINOUS', 'CANYON'
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE LOCATION IS 'Fire threat zones and geographic districts for risk stratification';

-- ============================================================================
-- CIRCUIT - Electrical circuits/feeders
-- ============================================================================
CREATE OR REPLACE TABLE CIRCUIT (
    CIRCUIT_ID VARCHAR(50) PRIMARY KEY,
    CIRCUIT_NAME VARCHAR(255) NOT NULL,
    FEEDER_ID VARCHAR(50),
    
    -- Hierarchy
    SUBSTATION_NAME VARCHAR(255),
    SUBSTATION_ID VARCHAR(50),
    DISTRICT VARCHAR(100),
    DIVISION VARCHAR(100),
    
    -- Classification
    VOLTAGE_CLASS VARCHAR(20),           -- '4KV', '12KV', '21KV', '33KV', '69KV'
    CIRCUIT_TYPE VARCHAR(50),            -- 'DISTRIBUTION', 'SUBTRANSMISSION', 'TRANSMISSION'
    CONSTRUCTION_TYPE VARCHAR(50),       -- 'OVERHEAD', 'UNDERGROUND', 'MIXED'
    
    -- Physical
    TOTAL_MILES FLOAT,
    OVERHEAD_MILES FLOAT,
    UNDERGROUND_MILES FLOAT,
    POLE_COUNT INT,
    TRANSFORMER_COUNT INT,
    CUSTOMER_COUNT INT,
    
    -- Risk Profile
    LOCATION_ID VARCHAR(50) REFERENCES LOCATION(LOCATION_ID),
    FIRE_THREAT_TIER VARCHAR(10),        -- Inherited or calculated
    PRIORITY_TIER VARCHAR(10),           -- 'P1', 'P2', 'P3', 'P4'
    
    -- Performance
    SAIDI_MINUTES FLOAT,                 -- System Average Interruption Duration Index
    SAIFI_COUNT FLOAT,                   -- System Average Interruption Frequency Index
    MAIFI_COUNT FLOAT,                   -- Momentary Average Interruption Frequency
    
    -- Vegetation Program
    LAST_PATROL_DATE DATE,
    LAST_TRIM_DATE DATE,
    TRIM_CYCLE_YEARS INT DEFAULT 3,
    NEXT_SCHEDULED_TRIM DATE,
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE CIRCUIT IS 'Electrical circuits/feeders with reliability metrics and trim schedules';

-- ============================================================================
-- ASSET - Poles, conductors, transformers, cables
-- ============================================================================
CREATE OR REPLACE TABLE ASSET (
    ASSET_ID VARCHAR(50) PRIMARY KEY,
    ASSET_NAME VARCHAR(255),
    ASSET_TYPE VARCHAR(50) NOT NULL,     -- 'POLE', 'CONDUCTOR', 'TRANSFORMER', 'SWITCH', 'CABLE_UNDERGROUND'
    ASSET_SUBTYPE VARCHAR(50),           -- 'WOOD_POLE', 'STEEL_POLE', 'PADMOUNT_TRANSFORMER', etc.
    
    -- Hierarchy
    CIRCUIT_ID VARCHAR(50) REFERENCES CIRCUIT(CIRCUIT_ID),
    LOCATION_ID VARCHAR(50) REFERENCES LOCATION(LOCATION_ID),
    PARENT_ASSET_ID VARCHAR(50),         -- For conductor spans attached to poles
    
    -- Physical Attributes
    MANUFACTURER VARCHAR(100),
    MODEL VARCHAR(100),
    INSTALL_DATE DATE,
    EXPECTED_LIFE_YEARS INT,
    AGE_YEARS INT,                       -- Calculated
    
    -- Electrical
    VOLTAGE_CLASS VARCHAR(20),
    PHASE VARCHAR(10),                   -- 'A', 'B', 'C', 'ABC', 'AB', 'BC', 'AC'
    RATED_CAPACITY FLOAT,
    
    -- Location
    LATITUDE FLOAT,
    LONGITUDE FLOAT,
    ELEVATION_FT FLOAT,
    SPAN_LENGTH_FT FLOAT,                -- For conductors
    HEIGHT_FT FLOAT,                     -- For poles
    DEPTH_FT FLOAT,                      -- For underground cables
    
    -- Condition
    CONDITION_SCORE INT,                 -- 1-5 scale from inspection
    LAST_INSPECTION_DATE DATE,
    LAST_INSPECTION_TYPE VARCHAR(50),    -- 'VISUAL', 'INTRUSIVE', 'DRONE', 'LIDAR'
    REPLACEMENT_PRIORITY VARCHAR(10),    -- 'IMMEDIATE', 'HIGH', 'MEDIUM', 'LOW'
    
    -- Underground Cable Specific (for Hidden Discovery)
    INSULATION_TYPE VARCHAR(50),         -- 'XLPE', 'EPR', 'PILC', 'TR-XLPE'
    CABLE_JACKET VARCHAR(50),
    SOIL_TYPE VARCHAR(50),               -- 'SANDY', 'CLAY', 'LOAM', 'ROCKY'
    MOISTURE_EXPOSURE VARCHAR(20),       -- 'LOW', 'MEDIUM', 'HIGH'
    
    -- Risk Scores (ML-populated)
    FAILURE_PROBABILITY FLOAT,           -- 0-1
    IGNITION_RISK_SCORE FLOAT,           -- 0-100
    COMPOSITE_RISK_SCORE FLOAT,          -- 0-100
    RISK_SCORE_DATE DATE,
    
    -- Status
    STATUS VARCHAR(30),                  -- 'IN_SERVICE', 'OUT_OF_SERVICE', 'PLANNED', 'RETIRED'
    OPERATIONAL_FLAG BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE ASSET IS 'Utility assets including poles, conductors, transformers, and underground cables';

-- ============================================================================
-- VEGETATION_ENCROACHMENT - LiDAR-derived vegetation proximity data
-- ============================================================================
CREATE OR REPLACE TABLE VEGETATION_ENCROACHMENT (
    ENCROACHMENT_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL REFERENCES ASSET(ASSET_ID),
    
    -- Measurement
    MEASUREMENT_DATE DATE NOT NULL,
    MEASUREMENT_SOURCE VARCHAR(50),      -- 'LIDAR', 'DRONE', 'FIELD_INSPECTION', 'SATELLITE'
    
    -- Tree/Vegetation Details
    TREE_SPECIES VARCHAR(100),           -- 'EUCALYPTUS', 'OAK', 'PINE', 'PALM', 'BRUSH'
    TREE_HEIGHT_FT FLOAT,
    TREE_CANOPY_DIAMETER_FT FLOAT,
    TREE_HEALTH VARCHAR(20),             -- 'HEALTHY', 'STRESSED', 'DEAD', 'HAZARD'
    
    -- Clearance Measurements
    DISTANCE_TO_CONDUCTOR_FT FLOAT,      -- Current distance
    HORIZONTAL_CLEARANCE_FT FLOAT,
    VERTICAL_CLEARANCE_FT FLOAT,
    
    -- Growth Modeling
    GROWTH_RATE_ANNUAL_FT FLOAT,         -- Feet per year
    GROWTH_RATE_CATEGORY VARCHAR(20),    -- 'SLOW', 'MEDIUM', 'FAST', 'VERY_FAST'
    PREDICTED_ENCROACHMENT_30D_FT FLOAT, -- ML predicted
    PREDICTED_ENCROACHMENT_90D_FT FLOAT,
    DAYS_TO_CRITICAL INT,                -- Days until clearance violation
    
    -- Compliance (CPUC GO95)
    REQUIRED_CLEARANCE_FT FLOAT,         -- Based on voltage and fire tier
    CLEARANCE_STATUS VARCHAR(30),        -- 'COMPLIANT', 'MARGINAL', 'VIOLATION', 'CRITICAL'
    IN_VIOLATION BOOLEAN DEFAULT FALSE,
    
    -- Risk
    STRIKE_POTENTIAL VARCHAR(20),        -- 'LOW', 'MEDIUM', 'HIGH', 'IMMINENT'
    FALL_IN_POTENTIAL BOOLEAN,           -- Tree could fall into line
    BLOW_IN_POTENTIAL BOOLEAN,           -- Wind could blow into line
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE VEGETATION_ENCROACHMENT IS 'LiDAR-derived vegetation proximity with growth predictions and compliance status';

-- ============================================================================
-- RISK_ASSESSMENT - ML-generated risk scores per asset
-- ============================================================================
CREATE OR REPLACE TABLE RISK_ASSESSMENT (
    ASSESSMENT_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL REFERENCES ASSET(ASSET_ID),
    ASSESSMENT_DATE DATE NOT NULL,
    
    -- Overall Scores
    COMPOSITE_RISK_SCORE FLOAT,          -- 0-100, weighted combination
    RISK_TIER VARCHAR(10),               -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    RISK_RANK INT,                       -- Rank within portfolio
    
    -- Component Scores
    FAILURE_PROBABILITY FLOAT,           -- 0-1, probability of failure in next year
    IGNITION_RISK FLOAT,                 -- 0-100, wildfire ignition potential
    OUTAGE_IMPACT_SCORE FLOAT,           -- 0-100, customer impact if fails
    SAFETY_RISK_SCORE FLOAT,             -- 0-100, public safety risk
    
    -- Contributing Factors (for explainability)
    AGE_FACTOR FLOAT,
    CONDITION_FACTOR FLOAT,
    VEGETATION_FACTOR FLOAT,
    WEATHER_FACTOR FLOAT,
    LOAD_FACTOR FLOAT,
    HISTORICAL_FACTOR FLOAT,
    
    -- Model Info
    MODEL_VERSION VARCHAR(50),
    MODEL_CONFIDENCE FLOAT,
    
    -- Recommendations
    RECOMMENDED_ACTION VARCHAR(100),     -- 'REPLACE', 'REPAIR', 'TRIM', 'INSPECT', 'MONITOR'
    RECOMMENDED_PRIORITY VARCHAR(20),
    ESTIMATED_RISK_REDUCTION FLOAT,      -- If action taken
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE RISK_ASSESSMENT IS 'ML-generated risk assessments with component scores and recommendations';

-- ============================================================================
-- WORK_ORDER - Maintenance work orders (trim, inspect, replace)
-- ============================================================================
CREATE OR REPLACE TABLE WORK_ORDER (
    WORK_ORDER_ID VARCHAR(50) PRIMARY KEY,
    WORK_ORDER_NUMBER VARCHAR(30),
    
    -- Association
    ASSET_ID VARCHAR(50) REFERENCES ASSET(ASSET_ID),
    CIRCUIT_ID VARCHAR(50) REFERENCES CIRCUIT(CIRCUIT_ID),
    LOCATION_ID VARCHAR(50) REFERENCES LOCATION(LOCATION_ID),
    
    -- Classification
    ACTIVITY_TYPE VARCHAR(50) NOT NULL,  -- 'TRIM', 'INSPECT', 'REPLACE', 'REPAIR', 'PATROL'
    WORK_TYPE VARCHAR(50),               -- 'ROUTINE', 'EMERGENCY', 'CORRECTIVE', 'PREVENTIVE'
    PRIORITY VARCHAR(20),                -- 'EMERGENCY', 'URGENT', 'HIGH', 'MEDIUM', 'LOW'
    
    -- Scope
    DESCRIPTION VARCHAR(1000),
    SCOPE_NOTES VARCHAR(2000),
    ESTIMATED_HOURS FLOAT,
    ESTIMATED_COST FLOAT,
    
    -- Vegetation Specific
    TREES_TO_TRIM INT,
    ESTIMATED_MILES FLOAT,
    SPECIES_TARGET VARCHAR(255),
    
    -- Schedule
    REQUESTED_DATE DATE,
    SCHEDULED_DATE DATE,
    DUE_DATE DATE,
    COMPLETION_DATE DATE,
    
    -- Status
    STATUS VARCHAR(30),                  -- 'DRAFT', 'SUBMITTED', 'APPROVED', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'
    
    -- Actuals
    ACTUAL_HOURS FLOAT,
    ACTUAL_COST FLOAT,
    MILES_TRIMMED FLOAT,
    TREES_TRIMMED INT,
    
    -- Crew
    ASSIGNED_CREW VARCHAR(100),
    CONTRACTOR VARCHAR(255),
    
    -- Risk Reduction
    PRE_WORK_RISK_SCORE FLOAT,
    POST_WORK_RISK_SCORE FLOAT,
    RISK_REDUCTION_VALUE FLOAT,
    
    -- Source
    CREATED_BY VARCHAR(100),
    CREATED_SOURCE VARCHAR(50),          -- 'VIGIL_AI', 'MANUAL', 'PATROL', 'INSPECTION'
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE WORK_ORDER IS 'Maintenance work orders for vegetation management and asset repairs';

-- ============================================================================
-- WEATHER_FORECAST - Hyper-local weather data
-- ============================================================================
CREATE OR REPLACE TABLE WEATHER_FORECAST (
    FORECAST_ID VARCHAR(50) PRIMARY KEY,
    LOCATION_ID VARCHAR(50) NOT NULL REFERENCES LOCATION(LOCATION_ID),
    FORECAST_DATE DATE NOT NULL,
    FORECAST_HOUR INT,                   -- 0-23
    
    -- Source
    SOURCE VARCHAR(50),                  -- 'NWS', 'DARKSKY', 'TOMORROW_IO'
    ISSUED_AT TIMESTAMP_NTZ,
    
    -- Temperature
    TEMPERATURE_F FLOAT,
    TEMPERATURE_MAX_F FLOAT,
    TEMPERATURE_MIN_F FLOAT,
    
    -- Wind
    WIND_SPEED_MPH FLOAT,
    WIND_GUST_MPH FLOAT,
    WIND_DIRECTION VARCHAR(10),          -- 'N', 'NE', 'E', etc.
    
    -- Humidity & Precipitation
    HUMIDITY_PCT FLOAT,
    PRECIPITATION_PROBABILITY FLOAT,
    PRECIPITATION_AMOUNT_IN FLOAT,
    PRECIPITATION_TYPE VARCHAR(20),      -- 'RAIN', 'SNOW', 'SLEET', 'NONE'
    
    -- Fire Weather
    RED_FLAG_WARNING BOOLEAN DEFAULT FALSE,
    FIRE_WEATHER_WATCH BOOLEAN DEFAULT FALSE,
    WIND_ADVISORY BOOLEAN DEFAULT FALSE,
    
    -- Calculated Risk
    FIRE_WEATHER_INDEX FLOAT,            -- 0-100
    PSPS_PROBABILITY FLOAT,              -- Public Safety Power Shutoff probability
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE WEATHER_FORECAST IS 'Hyper-local weather forecasts with fire weather indicators';

-- ============================================================================
-- AMI_READING - Smart meter data for Hidden Discovery (Water Treeing)
-- ============================================================================
CREATE OR REPLACE TABLE AMI_READING (
    READING_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL REFERENCES ASSET(ASSET_ID),
    READING_TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    
    -- Voltage Readings
    VOLTAGE_A FLOAT,
    VOLTAGE_B FLOAT,
    VOLTAGE_C FLOAT,
    VOLTAGE_AVG FLOAT,
    VOLTAGE_NOMINAL FLOAT,
    
    -- Anomaly Detection (THE HIDDEN DISCOVERY)
    VOLTAGE_DIP_PCT FLOAT,               -- Percentage dip from nominal
    VOLTAGE_DIP_FLAG BOOLEAN DEFAULT FALSE,
    DIP_DURATION_SECONDS INT,
    
    -- Environmental Correlation
    RAINFALL_MM FLOAT,                   -- From weather station
    SOIL_MOISTURE_PCT FLOAT,             -- From soil sensors or estimate
    TEMPERATURE_F FLOAT,
    
    -- Pattern Flags
    RAIN_CORRELATED_DIP BOOLEAN DEFAULT FALSE,  -- Key for Water Treeing detection
    CONSECUTIVE_DIP_COUNT INT DEFAULT 0,
    
    -- Current/Power
    CURRENT_A FLOAT,
    CURRENT_B FLOAT,
    CURRENT_C FLOAT,
    POWER_KW FLOAT,
    POWER_FACTOR FLOAT,
    
    -- Quality
    READING_QUALITY VARCHAR(20),         -- 'VALID', 'ESTIMATED', 'MISSING'
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE AMI_READING IS 'Smart meter readings with voltage anomalies for underground cable health monitoring';

-- Create index for efficient Water Treeing queries
-- ALTER TABLE AMI_READING ADD SEARCH OPTIMIZATION ON EQUALITY(ASSET_ID, VOLTAGE_DIP_FLAG, RAIN_CORRELATED_DIP);

-- ============================================================================
-- MONTHLY_SNAPSHOT - Point-in-time snapshots for trending
-- ============================================================================
CREATE OR REPLACE TABLE MONTHLY_SNAPSHOT (
    SNAPSHOT_ID VARCHAR(50) PRIMARY KEY,
    CIRCUIT_ID VARCHAR(50) NOT NULL REFERENCES CIRCUIT(CIRCUIT_ID),
    SNAPSHOT_DATE DATE NOT NULL,
    
    -- Risk Metrics
    HIGH_RISK_ASSET_COUNT INT,
    CRITICAL_RISK_ASSET_COUNT INT,
    AVG_RISK_SCORE FLOAT,
    MAX_RISK_SCORE FLOAT,
    
    -- Vegetation Metrics
    TOTAL_SPANS INT,
    SPANS_REQUIRING_TRIM INT,
    SPANS_IN_VIOLATION INT,
    MILES_TRIMMED_MTD FLOAT,
    MILES_TRIMMED_YTD FLOAT,
    
    -- Work Order Metrics
    OPEN_WORK_ORDERS INT,
    COMPLETED_WORK_ORDERS_MTD INT,
    BACKLOG_DAYS FLOAT,
    
    -- Budget
    BUDGET_ALLOCATED FLOAT,
    BUDGET_SPENT_MTD FLOAT,
    BUDGET_SPENT_YTD FLOAT,
    COST_PER_MILE FLOAT,
    
    -- Risk Reduction
    RISK_REDUCTION_VALUE_MTD FLOAT,
    RISK_REDUCTION_VALUE_YTD FLOAT,
    RISK_REDUCTION_PER_DOLLAR FLOAT,
    
    -- Reliability
    OUTAGES_MTD INT,
    OUTAGE_MINUTES_MTD FLOAT,
    VEG_CAUSED_OUTAGES_MTD INT,
    
    -- Fire Season Readiness
    DAYS_TO_FIRE_SEASON INT,
    FIRE_SEASON_READINESS_PCT FLOAT,
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE MONTHLY_SNAPSHOT IS 'Monthly circuit-level snapshots for trend analysis and reporting';

-- ============================================================================
-- COMPLIANCE_DOCUMENT - CPUC GO95 and vegetation standards
-- ============================================================================
CREATE OR REPLACE TABLE COMPLIANCE_DOCUMENT (
    DOCUMENT_ID VARCHAR(50) PRIMARY KEY,
    
    -- Classification
    DOCUMENT_TYPE VARCHAR(50),           -- 'REGULATION', 'STANDARD', 'GUIDELINE', 'PROCEDURE'
    REGULATION_CODE VARCHAR(50),         -- 'GO95', 'GO165', 'NERC_FAC_003'
    
    -- Content
    TITLE VARCHAR(500),
    SECTION VARCHAR(100),
    SUBSECTION VARCHAR(100),
    CONTENT TEXT,
    
    -- Applicability
    ASSET_TYPE VARCHAR(50),              -- Which assets this applies to
    VOLTAGE_CLASS VARCHAR(20),
    FIRE_TIER VARCHAR(10),
    
    -- Clearance Values (for GO95)
    MIN_CLEARANCE_FT FLOAT,
    RADIAL_CLEARANCE_FT FLOAT,
    
    -- Metadata
    EFFECTIVE_DATE DATE,
    LAST_UPDATED DATE,
    SOURCE_URL VARCHAR(500),
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE COMPLIANCE_DOCUMENT IS 'CPUC GO95 and vegetation management regulatory documents for Cortex Search';

-- ============================================================================
-- SEQUENCES for ID generation
-- ============================================================================
CREATE OR REPLACE SEQUENCE WORK_ORDER_SEQ START = 1 INCREMENT = 1;

-- ============================================================================
-- INDEXES / CLUSTERING (Snowflake optimization)
-- ============================================================================
-- Note: Clustering is automatically managed in Snowflake
-- For large tables, consider adding clustering keys:
-- ALTER TABLE ASSET CLUSTER BY (CIRCUIT_ID, ASSET_TYPE, STATUS);
-- ALTER TABLE VEGETATION_ENCROACHMENT CLUSTER BY (ASSET_ID, CLEARANCE_STATUS);
-- ALTER TABLE AMI_READING CLUSTER BY (ASSET_ID, READING_TIMESTAMP);
-- ALTER TABLE RISK_ASSESSMENT CLUSTER BY (ASSET_ID, ASSESSMENT_DATE);
