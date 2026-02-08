/*
=============================================================================
VIGIL Risk Planning - SPCS Deployment
=============================================================================
Script 6: Deploy VIGIL to Snowpark Container Services

Prerequisites:
1. Run all previous SQL scripts (01-05)
2. Build and push Docker images to repository
3. Ensure ACCOUNTADMIN or appropriate role with SPCS privileges
=============================================================================
*/

USE ROLE ACCOUNTADMIN;
USE DATABASE RISK_PLANNING_DB;
USE WAREHOUSE RISK_COMPUTE_WH;

-- =====================
-- CREATE IMAGE REPOSITORY
-- =====================
CREATE IMAGE REPOSITORY IF NOT EXISTS SPCS.APP_REPO
    COMMENT = 'Container images for VIGIL Risk Planning';

-- Show repository URL for pushing images
SHOW IMAGE REPOSITORIES IN SCHEMA SPCS;
-- Note the repository URL: <org>-<account>.registry.snowflakecomputing.com/risk_planning_db/spcs/app_repo

-- =====================
-- CREATE COMPUTE POOL
-- =====================
CREATE COMPUTE POOL IF NOT EXISTS VIGIL_COMPUTE_POOL
    MIN_NODES = 1
    MAX_NODES = 3
    INSTANCE_FAMILY = CPU_X64_S
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 300
    COMMENT = 'Compute pool for VIGIL Risk Planning application';

-- Check compute pool status
DESCRIBE COMPUTE POOL VIGIL_COMPUTE_POOL;

-- =====================
-- CREATE NETWORK RULE (for external access if needed)
-- =====================
CREATE OR REPLACE NETWORK RULE VIGIL_EGRESS_RULE
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('0.0.0.0:443', '0.0.0.0:80')
    COMMENT = 'Allow outbound HTTPS/HTTP for VIGIL';

-- =====================
-- CREATE EXTERNAL ACCESS INTEGRATION
-- =====================
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION VIGIL_EXTERNAL_ACCESS
    ALLOWED_NETWORK_RULES = (VIGIL_EGRESS_RULE)
    ENABLED = TRUE
    COMMENT = 'External access for VIGIL services';

-- =====================
-- UPLOAD SPEC FILE
-- =====================
-- First, upload spec.yaml to the stage:
-- PUT file://spec.yaml @RISK_PLANNING_DB.SPCS.APP_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- =====================
-- CREATE SERVICE
-- =====================
CREATE SERVICE IF NOT EXISTS SPCS.VIGIL_SERVICE
    IN COMPUTE POOL VIGIL_COMPUTE_POOL
    FROM @SPCS.APP_STAGE
    SPECIFICATION_FILE = 'spec.yaml'
    MIN_INSTANCES = 1
    MAX_INSTANCES = 2
    EXTERNAL_ACCESS_INTEGRATIONS = (VIGIL_EXTERNAL_ACCESS)
    COMMENT = 'VIGIL Risk Planning Application Service';

-- Alternative: Create service from inline spec
/*
CREATE SERVICE IF NOT EXISTS SPCS.VIGIL_SERVICE
    IN COMPUTE POOL VIGIL_COMPUTE_POOL
    FROM SPECIFICATION $$
spec:
  containers:
    - name: vigil-backend
      image: /RISK_PLANNING_DB/SPCS/APP_REPO/vigil-backend:latest
      env:
        SNOWFLAKE_DATABASE: RISK_PLANNING_DB
        SNOWFLAKE_SCHEMA: CONSTRUCTION_RISK
        SNOWFLAKE_WAREHOUSE: RISK_COMPUTE_WH
        PORT: "8000"
        HOST: "0.0.0.0"
      resources:
        requests:
          memory: "1Gi"
          cpu: "0.5"
        limits:
          memory: "2Gi"
          cpu: "1"
      readinessProbe:
        port: 8000
        path: /health
    - name: vigil-frontend
      image: /RISK_PLANNING_DB/SPCS/APP_REPO/vigil-frontend:latest
      resources:
        requests:
          memory: "256Mi"
          cpu: "0.25"
        limits:
          memory: "512Mi"
          cpu: "0.5"
      readinessProbe:
        port: 80
        path: /health
  endpoints:
    - name: vigil-ui
      port: 80
      public: true
      protocol: HTTPS
    - name: vigil-api
      port: 8000
      public: true
      protocol: HTTPS
  networkPolicyConfig:
    allowInternetEgress: true
$$
    MIN_INSTANCES = 1
    MAX_INSTANCES = 2
    EXTERNAL_ACCESS_INTEGRATIONS = (VIGIL_EXTERNAL_ACCESS);
*/

-- =====================
-- CHECK SERVICE STATUS
-- =====================
SHOW SERVICES IN SCHEMA SPCS;

-- Get service status
SELECT SYSTEM$GET_SERVICE_STATUS('SPCS.VIGIL_SERVICE');

-- Get service logs
SELECT SYSTEM$GET_SERVICE_LOGS('SPCS.VIGIL_SERVICE', '0', 'vigil-backend', 100);
SELECT SYSTEM$GET_SERVICE_LOGS('SPCS.VIGIL_SERVICE', '0', 'vigil-frontend', 100);

-- =====================
-- GET PUBLIC ENDPOINTS
-- =====================
SHOW ENDPOINTS IN SERVICE SPCS.VIGIL_SERVICE;

-- The output will show URLs like:
-- vigil-ui: https://<random>-<account>.snowflakecomputing.app
-- vigil-api: https://<random>-<account>.snowflakecomputing.app

-- =====================
-- GRANT ACCESS TO USERS
-- =====================
GRANT USAGE ON SERVICE SPCS.VIGIL_SERVICE TO ROLE VIGIL_USER;

-- =====================
-- MANAGEMENT COMMANDS
-- =====================

-- Suspend service (to save costs)
-- ALTER SERVICE SPCS.VIGIL_SERVICE SUSPEND;

-- Resume service
-- ALTER SERVICE SPCS.VIGIL_SERVICE RESUME;

-- Update service (after pushing new images)
-- ALTER SERVICE SPCS.VIGIL_SERVICE 
--     FROM @SPCS.APP_STAGE
--     SPECIFICATION_FILE = 'spec.yaml';

-- Drop service (cleanup)
-- DROP SERVICE IF EXISTS SPCS.VIGIL_SERVICE;

-- Suspend compute pool
-- ALTER COMPUTE POOL VIGIL_COMPUTE_POOL SUSPEND;

SELECT 'SPCS deployment script complete!' AS STATUS;
SELECT 'Run SHOW ENDPOINTS IN SERVICE SPCS.VIGIL_SERVICE to get application URL' AS NEXT_STEP;
