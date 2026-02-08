-- ============================================================================
-- VIGIL Risk Planning - RBAC Access Grants for SPCS
-- Run this as ACCOUNTADMIN after deploying the service
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- 1. Create application role for VIGIL
-- ============================================================================
CREATE ROLE IF NOT EXISTS VIGIL_APP_ROLE;
COMMENT ON ROLE VIGIL_APP_ROLE IS 'Application role for VIGIL Risk Planning copilot';

-- ============================================================================
-- 2. Grant database access
-- ============================================================================
GRANT USAGE ON DATABASE RISK_PLANNING_DB TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON ALL SCHEMAS IN DATABASE RISK_PLANNING_DB TO ROLE VIGIL_APP_ROLE;

-- Schema-specific grants
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.RAW TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.ATOMIC TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.CONSTRUCTION_RISK TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.ML TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.DOCS TO ROLE VIGIL_APP_ROLE;
GRANT USAGE ON SCHEMA RISK_PLANNING_DB.SPCS TO ROLE VIGIL_APP_ROLE;

-- ============================================================================
-- 3. Grant table access
-- ============================================================================
-- ATOMIC schema tables (main data)
GRANT SELECT ON ALL TABLES IN SCHEMA RISK_PLANNING_DB.ATOMIC TO ROLE VIGIL_APP_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA RISK_PLANNING_DB.ATOMIC TO ROLE VIGIL_APP_ROLE;

-- Work order table needs INSERT/UPDATE for creating work orders
GRANT INSERT, UPDATE ON TABLE RISK_PLANNING_DB.ATOMIC.WORK_ORDER TO ROLE VIGIL_APP_ROLE;

-- ML schema tables (predictions)
GRANT SELECT ON ALL TABLES IN SCHEMA RISK_PLANNING_DB.ML TO ROLE VIGIL_APP_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA RISK_PLANNING_DB.ML TO ROLE VIGIL_APP_ROLE;

-- DOCS schema (for Cortex Search)
GRANT SELECT ON ALL TABLES IN SCHEMA RISK_PLANNING_DB.DOCS TO ROLE VIGIL_APP_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA RISK_PLANNING_DB.DOCS TO ROLE VIGIL_APP_ROLE;

-- ============================================================================
-- 4. Grant warehouse access
-- ============================================================================
GRANT USAGE ON WAREHOUSE RISK_COMPUTE_WH TO ROLE VIGIL_APP_ROLE;

-- ============================================================================
-- 5. Grant Cortex functions access
-- ============================================================================
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE VIGIL_APP_ROLE;

-- ============================================================================
-- 6. Grant Cortex Search service access (if exists)
-- ============================================================================
-- GRANT USAGE ON CORTEX SEARCH SERVICE RISK_PLANNING_DB.DOCS.VIGIL_SEARCH TO ROLE VIGIL_APP_ROLE;

-- ============================================================================
-- 7. Grant Cortex Analyst semantic model access (if exists)  
-- ============================================================================
-- GRANT USAGE ON SEMANTIC MODEL RISK_PLANNING_DB.DOCS.VIGIL_SEMANTIC_MODEL TO ROLE VIGIL_APP_ROLE;

-- ============================================================================
-- 8. Grant SPCS-specific permissions
-- ============================================================================
-- Stage access for image repository
GRANT READ ON STAGE RISK_PLANNING_DB.SPCS.VIGIL_STAGE TO ROLE VIGIL_APP_ROLE;
GRANT WRITE ON STAGE RISK_PLANNING_DB.SPCS.VIGIL_STAGE TO ROLE VIGIL_APP_ROLE;

-- Image repository access
GRANT READ ON IMAGE REPOSITORY RISK_PLANNING_DB.SPCS.VIGIL_IMAGES TO ROLE VIGIL_APP_ROLE;

-- ============================================================================
-- 9. Create service user and grant role
-- ============================================================================
-- The SPCS service runs under the owner's context, but for explicit control:
-- CREATE USER IF NOT EXISTS VIGIL_SERVICE_USER
--     TYPE = SERVICE;
-- GRANT ROLE VIGIL_APP_ROLE TO USER VIGIL_SERVICE_USER;

-- ============================================================================
-- 10. Grant role to deploying user
-- ============================================================================
-- Replace YOUR_USERNAME with the actual deploying user
-- GRANT ROLE VIGIL_APP_ROLE TO USER YOUR_USERNAME;

-- ============================================================================
-- 11. Verify grants
-- ============================================================================
SHOW GRANTS TO ROLE VIGIL_APP_ROLE;

-- ============================================================================
-- Usage: After creating the compute pool and service, run:
-- ============================================================================
/*
-- Create compute pool
CREATE COMPUTE POOL IF NOT EXISTS VIGIL_POOL
    MIN_NODES = 1
    MAX_NODES = 2
    INSTANCE_FAMILY = CPU_X64_XS
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 3600;

-- Create service
CREATE SERVICE RISK_PLANNING_DB.SPCS.VIGIL_SERVICE
    IN COMPUTE POOL VIGIL_POOL
    FROM @RISK_PLANNING_DB.SPCS.VIGIL_STAGE
    SPECIFICATION_FILE = 'service_spec.yaml'
    MIN_INSTANCES = 1
    MAX_INSTANCES = 1;

-- Get service URL
SHOW ENDPOINTS IN SERVICE RISK_PLANNING_DB.SPCS.VIGIL_SERVICE;
*/
