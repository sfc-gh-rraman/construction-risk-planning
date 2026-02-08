-- ============================================================================
-- VIGIL Risk-Based Planning Intelligence Platform
-- ML Schema - Model Artifacts, Predictions, and Explainability
-- ============================================================================

USE DATABASE RISK_PLANNING_DB;
USE SCHEMA ML;

-- ============================================================================
-- MODEL_REGISTRY - Track deployed ML models
-- ============================================================================
CREATE OR REPLACE TABLE MODEL_REGISTRY (
    MODEL_ID VARCHAR(50) PRIMARY KEY,
    MODEL_NAME VARCHAR(255) NOT NULL,
    MODEL_TYPE VARCHAR(100),             -- 'ASSET_HEALTH', 'VEG_GROWTH', 'IGNITION_RISK', 'CABLE_FAILURE'
    
    -- Version Info
    VERSION VARCHAR(50),
    IS_ACTIVE BOOLEAN DEFAULT FALSE,
    PROMOTED_AT TIMESTAMP_NTZ,
    
    -- Training Info
    TRAINING_DATE DATE,
    TRAINING_ROWS INT,
    FEATURE_COUNT INT,
    
    -- Performance Metrics
    ACCURACY FLOAT,
    PRECISION_SCORE FLOAT,
    RECALL_SCORE FLOAT,
    F1_SCORE FLOAT,
    AUC_ROC FLOAT,
    MAE FLOAT,                           -- For regression models
    RMSE FLOAT,
    
    -- Model Details
    ALGORITHM VARCHAR(100),              -- 'XGBOOST', 'RANDOM_FOREST', 'GRADIENT_BOOSTING'
    HYPERPARAMETERS VARIANT,
    FEATURE_NAMES VARIANT,
    
    -- Storage
    MODEL_STAGE_PATH VARCHAR(500),
    MODEL_SIZE_MB FLOAT,
    
    -- Metadata
    CREATED_BY VARCHAR(100),
    DESCRIPTION VARCHAR(1000),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE MODEL_REGISTRY IS 'Registry of deployed ML models with performance metrics';

-- ============================================================================
-- ASSET_HEALTH_PREDICTION - Output from Asset Health Scorer model
-- ============================================================================
CREATE OR REPLACE TABLE ASSET_HEALTH_PREDICTION (
    PREDICTION_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    PREDICTION_DATE DATE NOT NULL,
    MODEL_ID VARCHAR(50) REFERENCES MODEL_REGISTRY(MODEL_ID),
    
    -- Predictions
    HEALTH_SCORE FLOAT,                  -- 0-100 (100 = perfect health)
    FAILURE_PROBABILITY_1Y FLOAT,        -- Probability of failure in 1 year
    FAILURE_PROBABILITY_5Y FLOAT,        -- Probability of failure in 5 years
    REMAINING_USEFUL_LIFE_YEARS FLOAT,
    
    -- Risk Classification
    RISK_CATEGORY VARCHAR(20),           -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    REPLACEMENT_RECOMMENDED BOOLEAN,
    
    -- Confidence
    PREDICTION_CONFIDENCE FLOAT,
    UNCERTAINTY_LOWER FLOAT,
    UNCERTAINTY_UPPER FLOAT,
    
    -- Top Features (for explainability)
    TOP_FEATURE_1 VARCHAR(100),
    TOP_FEATURE_1_IMPACT FLOAT,
    TOP_FEATURE_2 VARCHAR(100),
    TOP_FEATURE_2_IMPACT FLOAT,
    TOP_FEATURE_3 VARCHAR(100),
    TOP_FEATURE_3_IMPACT FLOAT,
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE ASSET_HEALTH_PREDICTION IS 'Asset health scores and failure predictions from ML model';

-- ============================================================================
-- VEGETATION_GROWTH_PREDICTION - Output from Vegetation Growth Predictor
-- ============================================================================
CREATE OR REPLACE TABLE VEGETATION_GROWTH_PREDICTION (
    PREDICTION_ID VARCHAR(50) PRIMARY KEY,
    ENCROACHMENT_ID VARCHAR(50) NOT NULL,
    ASSET_ID VARCHAR(50) NOT NULL,
    PREDICTION_DATE DATE NOT NULL,
    MODEL_ID VARCHAR(50) REFERENCES MODEL_REGISTRY(MODEL_ID),
    
    -- Current State
    CURRENT_DISTANCE_FT FLOAT,
    REQUIRED_CLEARANCE_FT FLOAT,
    
    -- Growth Predictions
    PREDICTED_GROWTH_30D_FT FLOAT,
    PREDICTED_GROWTH_60D_FT FLOAT,
    PREDICTED_GROWTH_90D_FT FLOAT,
    PREDICTED_DISTANCE_30D_FT FLOAT,
    PREDICTED_DISTANCE_60D_FT FLOAT,
    PREDICTED_DISTANCE_90D_FT FLOAT,
    
    -- Time to Action
    DAYS_TO_VIOLATION INT,               -- Days until clearance violation
    DAYS_TO_CRITICAL INT,                -- Days until critical (<2ft)
    TRIM_URGENCY VARCHAR(20),            -- 'IMMEDIATE', 'URGENT', 'SCHEDULED', 'ROUTINE'
    
    -- Confidence
    PREDICTION_CONFIDENCE FLOAT,
    
    -- Contributing Factors
    SPECIES_GROWTH_FACTOR FLOAT,
    SEASON_FACTOR FLOAT,
    WEATHER_FACTOR FLOAT,
    HISTORICAL_FACTOR FLOAT,
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE VEGETATION_GROWTH_PREDICTION IS 'Vegetation growth predictions for proactive trimming';

-- ============================================================================
-- IGNITION_RISK_PREDICTION - Output from Ignition Risk Model
-- ============================================================================
CREATE OR REPLACE TABLE IGNITION_RISK_PREDICTION (
    PREDICTION_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    PREDICTION_DATE DATE NOT NULL,
    MODEL_ID VARCHAR(50) REFERENCES MODEL_REGISTRY(MODEL_ID),
    
    -- Risk Scores (by scenario)
    BASE_IGNITION_RISK FLOAT,            -- Normal conditions
    ELEVATED_IGNITION_RISK FLOAT,        -- Elevated fire weather
    EXTREME_IGNITION_RISK FLOAT,         -- Red flag conditions
    
    -- Probability
    IGNITION_PROBABILITY_BASE FLOAT,
    IGNITION_PROBABILITY_ELEVATED FLOAT,
    IGNITION_PROBABILITY_EXTREME FLOAT,
    
    -- Consequence
    ESTIMATED_ACRES_AT_RISK FLOAT,
    STRUCTURES_AT_RISK INT,
    POPULATION_AT_RISK INT,
    
    -- Risk Drivers
    VEGETATION_CONTRIBUTION FLOAT,
    EQUIPMENT_CONTRIBUTION FLOAT,
    WEATHER_CONTRIBUTION FLOAT,
    TERRAIN_CONTRIBUTION FLOAT,
    
    -- Recommendations
    PSPS_CANDIDATE BOOLEAN,              -- Public Safety Power Shutoff candidate
    ENHANCED_PATROL_RECOMMENDED BOOLEAN,
    SECTIONALIZING_RECOMMENDED BOOLEAN,
    
    -- Confidence
    PREDICTION_CONFIDENCE FLOAT,
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE IGNITION_RISK_PREDICTION IS 'Wildfire ignition risk predictions under various weather scenarios';

-- ============================================================================
-- CABLE_FAILURE_PREDICTION - Output from Cable Failure Detector (Water Treeing)
-- ============================================================================
CREATE OR REPLACE TABLE CABLE_FAILURE_PREDICTION (
    PREDICTION_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    PREDICTION_DATE DATE NOT NULL,
    MODEL_ID VARCHAR(50) REFERENCES MODEL_REGISTRY(MODEL_ID),
    
    -- THE HIDDEN DISCOVERY: Water Treeing Detection
    WATER_TREEING_PROBABILITY FLOAT,     -- 0-1, key metric
    WATER_TREEING_SEVERITY VARCHAR(20),  -- 'NONE', 'EARLY', 'MODERATE', 'SEVERE'
    
    -- Failure Predictions
    FAILURE_PROBABILITY_30D FLOAT,
    FAILURE_PROBABILITY_90D FLOAT,
    FAILURE_PROBABILITY_1Y FLOAT,
    
    -- Anomaly Metrics
    VOLTAGE_DIP_FREQUENCY FLOAT,         -- Dips per rain event
    RAIN_CORRELATION_SCORE FLOAT,        -- How correlated are dips with rain
    ANOMALY_SCORE FLOAT,                 -- Overall anomaly score
    
    -- Pattern Analysis
    DIP_EVENTS_LAST_30D INT,
    DIP_EVENTS_LAST_90D INT,
    AVG_DIP_MAGNITUDE_PCT FLOAT,
    RAIN_EVENTS_WITH_DIPS INT,
    RAIN_EVENTS_WITHOUT_DIPS INT,
    
    -- Cable Characteristics
    CABLE_AGE_YEARS INT,
    INSULATION_TYPE VARCHAR(50),
    MOISTURE_EXPOSURE VARCHAR(20),
    
    -- Cost Analysis
    PROACTIVE_REPLACEMENT_COST FLOAT,    -- ~$10K
    EMERGENCY_REPAIR_COST FLOAT,         -- ~$100K
    REGULATORY_FINE_RISK FLOAT,
    
    -- Recommendations
    RECOMMENDED_ACTION VARCHAR(100),     -- 'REPLACE', 'MONITOR', 'TEST', 'NO_ACTION'
    ACTION_URGENCY VARCHAR(20),
    
    -- Confidence
    PREDICTION_CONFIDENCE FLOAT,
    
    -- Explainability
    TOP_ANOMALY_INDICATOR VARCHAR(100),
    DETECTION_METHOD VARCHAR(100),       -- 'RAIN_CORRELATION', 'VOLTAGE_PATTERN', 'COMBINED'
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE CABLE_FAILURE_PREDICTION IS 'Underground cable failure predictions including Water Treeing detection';

-- ============================================================================
-- SHAP_VALUES - Feature importance for model explainability
-- ============================================================================
CREATE OR REPLACE TABLE SHAP_VALUES (
    SHAP_ID VARCHAR(50) PRIMARY KEY,
    PREDICTION_ID VARCHAR(50) NOT NULL,
    MODEL_ID VARCHAR(50) REFERENCES MODEL_REGISTRY(MODEL_ID),
    ASSET_ID VARCHAR(50) NOT NULL,
    
    -- Feature Values
    FEATURE_NAME VARCHAR(100),
    FEATURE_VALUE FLOAT,
    SHAP_VALUE FLOAT,
    
    -- Ranking
    FEATURE_RANK INT,
    CONTRIBUTION_PCT FLOAT,
    
    -- Direction
    IMPACT_DIRECTION VARCHAR(10),        -- 'POSITIVE', 'NEGATIVE'
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE SHAP_VALUES IS 'SHAP values for individual prediction explainability';

-- ============================================================================
-- PDP_CURVES - Partial Dependence Plots for global model interpretation
-- ============================================================================
CREATE OR REPLACE TABLE PDP_CURVES (
    PDP_ID VARCHAR(50) PRIMARY KEY,
    MODEL_ID VARCHAR(50) REFERENCES MODEL_REGISTRY(MODEL_ID),
    
    -- Feature
    FEATURE_NAME VARCHAR(100),
    FEATURE_VALUE FLOAT,
    
    -- PDP Value
    PDP_VALUE FLOAT,
    PDP_STD FLOAT,
    
    -- ICE Values (Individual Conditional Expectation)
    ICE_MIN FLOAT,
    ICE_MAX FLOAT,
    ICE_PERCENTILE_25 FLOAT,
    ICE_PERCENTILE_75 FLOAT,
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE PDP_CURVES IS 'Partial Dependence Plot data for global model interpretation';

-- ============================================================================
-- MODEL_FEATURE_IMPORTANCE - Global feature importance per model
-- ============================================================================
CREATE OR REPLACE TABLE MODEL_FEATURE_IMPORTANCE (
    IMPORTANCE_ID VARCHAR(50) PRIMARY KEY,
    MODEL_ID VARCHAR(50) REFERENCES MODEL_REGISTRY(MODEL_ID),
    
    FEATURE_NAME VARCHAR(100),
    IMPORTANCE_SCORE FLOAT,
    IMPORTANCE_RANK INT,
    IMPORTANCE_TYPE VARCHAR(50),         -- 'GAIN', 'WEIGHT', 'COVER', 'PERMUTATION'
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE MODEL_FEATURE_IMPORTANCE IS 'Global feature importance scores for each model';

-- ============================================================================
-- PREDICTION_AUDIT - Track all predictions for monitoring/drift detection
-- ============================================================================
CREATE OR REPLACE TABLE PREDICTION_AUDIT (
    AUDIT_ID VARCHAR(50) PRIMARY KEY,
    MODEL_ID VARCHAR(50) REFERENCES MODEL_REGISTRY(MODEL_ID),
    PREDICTION_DATE DATE,
    
    -- Volume
    PREDICTION_COUNT INT,
    
    -- Distribution Stats
    MEAN_PREDICTION FLOAT,
    STD_PREDICTION FLOAT,
    MIN_PREDICTION FLOAT,
    MAX_PREDICTION FLOAT,
    PERCENTILE_25 FLOAT,
    PERCENTILE_50 FLOAT,
    PERCENTILE_75 FLOAT,
    
    -- Class Distribution (for classifiers)
    CLASS_CRITICAL_COUNT INT,
    CLASS_HIGH_COUNT INT,
    CLASS_MEDIUM_COUNT INT,
    CLASS_LOW_COUNT INT,
    
    -- Drift Detection
    PSI_SCORE FLOAT,                     -- Population Stability Index
    DRIFT_DETECTED BOOLEAN DEFAULT FALSE,
    
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

COMMENT ON TABLE PREDICTION_AUDIT IS 'Audit trail for model predictions and drift monitoring';
