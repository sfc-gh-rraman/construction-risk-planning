/*
=============================================================================
VIGIL Risk Planning - Database Setup
=============================================================================
Script 1: Create Database, Schemas, Warehouses, and Roles

Run as ACCOUNTADMIN or role with CREATE DATABASE privileges
=============================================================================
*/

-- Use accountadmin for initial setup
USE ROLE ACCOUNTADMIN;

-- =====================
-- CREATE DATABASE
-- =====================
CREATE DATABASE IF NOT EXISTS RISK_PLANNING_DB
    COMMENT = 'VIGIL - Vegetation & Infrastructure Grid Intelligence Layer';

-- =====================
-- CREATE WAREHOUSES
-- =====================
CREATE WAREHOUSE IF NOT EXISTS RISK_COMPUTE_WH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'General compute for VIGIL Risk Planning';

CREATE WAREHOUSE IF NOT EXISTS RISK_ML_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 120
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'ML training and inference for VIGIL';

-- =====================
-- CREATE SCHEMAS
-- =====================
USE DATABASE RISK_PLANNING_DB;

CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Landing zone for raw source data';

CREATE SCHEMA IF NOT EXISTS ATOMIC
    COMMENT = 'Cleansed, typed, and validated data';

CREATE SCHEMA IF NOT EXISTS CONSTRUCTION_RISK
    COMMENT = 'Materialized views, aggregations, and semantic models';

CREATE SCHEMA IF NOT EXISTS ML
    COMMENT = 'ML model predictions, features, and artifacts';

CREATE SCHEMA IF NOT EXISTS DOCS
    COMMENT = 'Documents for Cortex Search (GO95, procedures, etc.)';

CREATE SCHEMA IF NOT EXISTS SPCS
    COMMENT = 'Snowpark Container Services artifacts';

-- =====================
-- CREATE STAGES
-- =====================
CREATE STAGE IF NOT EXISTS CONSTRUCTION_RISK.SEMANTIC_MODELS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Semantic models for Cortex Analyst';

CREATE STAGE IF NOT EXISTS ML.MODEL_ARTIFACTS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Trained model artifacts';

CREATE STAGE IF NOT EXISTS SPCS.APP_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Container images and specs for SPCS';

-- =====================
-- CREATE ROLES (Optional)
-- =====================
CREATE ROLE IF NOT EXISTS VIGIL_ADMIN
    COMMENT = 'Admin role for VIGIL platform';

CREATE ROLE IF NOT EXISTS VIGIL_USER
    COMMENT = 'Standard user role for VIGIL platform';

-- Grant privileges
GRANT USAGE ON DATABASE RISK_PLANNING_DB TO ROLE VIGIL_ADMIN;
GRANT USAGE ON DATABASE RISK_PLANNING_DB TO ROLE VIGIL_USER;

GRANT USAGE ON ALL SCHEMAS IN DATABASE RISK_PLANNING_DB TO ROLE VIGIL_ADMIN;
GRANT USAGE ON ALL SCHEMAS IN DATABASE RISK_PLANNING_DB TO ROLE VIGIL_USER;

GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE RISK_PLANNING_DB TO ROLE VIGIL_ADMIN;

GRANT SELECT ON FUTURE TABLES IN DATABASE RISK_PLANNING_DB TO ROLE VIGIL_USER;
GRANT SELECT ON FUTURE VIEWS IN DATABASE RISK_PLANNING_DB TO ROLE VIGIL_USER;

GRANT USAGE ON WAREHOUSE RISK_COMPUTE_WH TO ROLE VIGIL_ADMIN;
GRANT USAGE ON WAREHOUSE RISK_COMPUTE_WH TO ROLE VIGIL_USER;
GRANT USAGE ON WAREHOUSE RISK_ML_WH TO ROLE VIGIL_ADMIN;

-- =====================
-- SET CONTEXT
-- =====================
USE WAREHOUSE RISK_COMPUTE_WH;
USE SCHEMA ATOMIC;

SELECT 'Database setup complete!' AS STATUS;
