-- ============================================================================
-- VIGIL Risk-Based Planning Intelligence Platform
-- Database and Schema Setup
-- ============================================================================

-- Create the main database
CREATE DATABASE IF NOT EXISTS RISK_PLANNING_DB;

USE DATABASE RISK_PLANNING_DB;

-- ============================================================================
-- SCHEMAS
-- ============================================================================

-- RAW: Landing zone for source system data
CREATE SCHEMA IF NOT EXISTS RAW;
COMMENT ON SCHEMA RAW IS 'Landing zone for GIS, LiDAR, AMI, and weather data ingestion';

-- ATOMIC: Normalized enterprise data model
CREATE SCHEMA IF NOT EXISTS ATOMIC;
COMMENT ON SCHEMA ATOMIC IS 'Normalized entities following utility data dictionary standards';

-- CONSTRUCTION_RISK: Data mart for analytics and reporting
CREATE SCHEMA IF NOT EXISTS CONSTRUCTION_RISK;
COMMENT ON SCHEMA CONSTRUCTION_RISK IS 'Analytics-ready data mart with risk KPIs and work planning';

-- ML: Machine learning models, predictions, and explainability
CREATE SCHEMA IF NOT EXISTS ML;
COMMENT ON SCHEMA ML IS 'ML model artifacts, predictions, and SHAP/PDP explainability data';

-- DOCS: Document storage for Cortex Search
CREATE SCHEMA IF NOT EXISTS DOCS;
COMMENT ON SCHEMA DOCS IS 'CPUC GO95, vegetation standards, and compliance documents for Cortex Search';

-- SPCS: Snowpark Container Services
CREATE SCHEMA IF NOT EXISTS SPCS;
COMMENT ON SCHEMA SPCS IS 'Container services, image repositories, and compute pools';

-- ============================================================================
-- WAREHOUSES
-- ============================================================================

-- Compute warehouse for general queries
CREATE WAREHOUSE IF NOT EXISTS RISK_COMPUTE_WH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    COMMENT = 'General compute for VIGIL queries';

-- ML warehouse for model training
CREATE WAREHOUSE IF NOT EXISTS RISK_ML_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 120
    AUTO_RESUME = TRUE
    COMMENT = 'ML training and inference workloads';

-- ============================================================================
-- STAGES
-- ============================================================================

USE SCHEMA RAW;

-- Stage for data file uploads
CREATE STAGE IF NOT EXISTS DATA_STAGE
    COMMENT = 'Stage for uploading parquet and CSV files';

-- Stage for document uploads
CREATE STAGE IF NOT EXISTS DOCS_STAGE
    COMMENT = 'Stage for CPUC regulations and vegetation standards';

-- Stage for LiDAR data
CREATE STAGE IF NOT EXISTS LIDAR_STAGE
    COMMENT = 'Stage for LiDAR point cloud data';

-- ============================================================================
-- FILE FORMATS
-- ============================================================================

CREATE FILE FORMAT IF NOT EXISTS PARQUET_FORMAT
    TYPE = 'PARQUET'
    COMPRESSION = 'SNAPPY';

CREATE FILE FORMAT IF NOT EXISTS CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('NULL', 'null', '');

CREATE FILE FORMAT IF NOT EXISTS JSON_FORMAT
    TYPE = 'JSON'
    STRIP_OUTER_ARRAY = TRUE;

-- ============================================================================
-- GRANTS (for SPCS service role)
-- ============================================================================

-- Create role for VIGIL application
CREATE ROLE IF NOT EXISTS VIGIL_APP_ROLE;

-- Grant database access
GRANT USAGE ON DATABASE RISK_PLANNING_DB TO ROLE VIGIL_APP_ROLE;

-- Grant schema access
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.RAW TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.ATOMIC TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.CONSTRUCTION_RISK TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.ML TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.DOCS TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.SPCS TO ROLE VIGIL_APP_ROLE;

-- Grant warehouse access
GRANT USAGE ON WAREHOUSE RISK_COMPUTE_WH TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON WAREHOUSE RISK_ML_WH TO ROLE VIGIL_APP_ROLE;

-- Grant table permissions for work order creation
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA RISK_PLANNING_DB.ATOMIC TO ROLE VIGIL_APP_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA RISK_PLANNING_DB.CONSTRUCTION_RISK TO ROLE VIGIL_APP_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA RISK_PLANNING_DB.ML TO ROLE VIGIL_APP_ROLE;

COMMENT ON DATABASE RISK_PLANNING_DB IS 
'VIGIL Risk-Based Planning Intelligence Platform - Utility asset risk management and vegetation control with ML-powered insights';
