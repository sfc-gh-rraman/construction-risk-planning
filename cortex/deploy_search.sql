-- =====================================================
-- VIGIL Risk Planning - Cortex Search Deployment
-- =====================================================
-- 
-- This script creates Cortex Search services for:
-- 1. CPUC GO95 compliance document search
-- 2. Vegetation management standards search
-- 3. Work order narrative search
--
-- Prerequisites:
-- - RISK_PLANNING_DB database exists
-- - DOCS schema exists with COMPLIANCE_DOCUMENT table
-- - Data has been loaded into COMPLIANCE_DOCUMENT table
-- =====================================================

USE DATABASE RISK_PLANNING_DB;
USE SCHEMA DOCS;
USE WAREHOUSE RISK_COMPUTE_WH;

-- =====================================================
-- Step 1: Verify prerequisite data exists
-- =====================================================

SELECT '🔍 Step 1: Verifying compliance document data...' as STEP;

SELECT 
    document_type,
    COUNT(*) as doc_count
FROM DOCS.COMPLIANCE_DOCUMENT
GROUP BY document_type
ORDER BY doc_count DESC;

-- =====================================================
-- Step 2: Create Cortex Search Service for GO95 Compliance
-- =====================================================

SELECT '📚 Step 2: Creating GO95 Compliance Search Service...' as STEP;

-- Drop existing service if it exists
DROP CORTEX SEARCH SERVICE IF EXISTS DOCS.GO95_SEARCH_SERVICE;

-- Create the search service on compliance documents
CREATE CORTEX SEARCH SERVICE DOCS.GO95_SEARCH_SERVICE
ON COMPLIANCE_DOCUMENT
WAREHOUSE = RISK_COMPUTE_WH
TARGET_LAG = '1 hour'
AS (
    SELECT 
        document_id,
        document_type,
        title,
        section_number,
        content,
        effective_date,
        regulatory_body,
        -- Create a combined searchable field
        CONCAT(
            'Document: ', title, '. ',
            'Section: ', COALESCE(section_number, 'N/A'), '. ',
            'Content: ', content
        ) as search_text
    FROM DOCS.COMPLIANCE_DOCUMENT
    WHERE document_type IN ('CPUC_GO95', 'CPUC_GO165', 'NERC_FAC', 'IEEE_STANDARD')
);

-- =====================================================
-- Step 3: Create Cortex Search Service for Vegetation Standards
-- =====================================================

SELECT '🌲 Step 3: Creating Vegetation Standards Search Service...' as STEP;

DROP CORTEX SEARCH SERVICE IF EXISTS DOCS.VEGETATION_SEARCH_SERVICE;

CREATE CORTEX SEARCH SERVICE DOCS.VEGETATION_SEARCH_SERVICE
ON COMPLIANCE_DOCUMENT
WAREHOUSE = RISK_COMPUTE_WH
TARGET_LAG = '1 hour'
AS (
    SELECT 
        document_id,
        document_type,
        title,
        section_number,
        content,
        -- Extract vegetation-specific metadata
        CASE 
            WHEN LOWER(content) LIKE '%clearance%' THEN 'CLEARANCE_REQUIREMENT'
            WHEN LOWER(content) LIKE '%trim%' OR LOWER(content) LIKE '%prune%' THEN 'TRIMMING_STANDARD'
            WHEN LOWER(content) LIKE '%species%' THEN 'SPECIES_GUIDANCE'
            WHEN LOWER(content) LIKE '%fire%' OR LOWER(content) LIKE '%hftd%' THEN 'FIRE_SAFETY'
            ELSE 'GENERAL'
        END as content_category,
        CONCAT(
            title, ': ', 
            COALESCE(section_number, ''), ' - ',
            content
        ) as search_text
    FROM DOCS.COMPLIANCE_DOCUMENT
    WHERE document_type IN ('CPUC_GO95', 'VEGETATION_MANUAL', 'FIRE_SAFETY')
        OR LOWER(content) LIKE '%vegetation%'
        OR LOWER(content) LIKE '%clearance%'
        OR LOWER(content) LIKE '%tree%'
);

-- =====================================================
-- Step 4: Create Work Order Narrative Search
-- =====================================================

SELECT '📋 Step 4: Creating Work Order Search Service...' as STEP;

DROP CORTEX SEARCH SERVICE IF EXISTS DOCS.WORK_ORDER_SEARCH_SERVICE;

-- First, create a view that combines work order data with searchable narratives
CREATE OR REPLACE VIEW DOCS.WORK_ORDER_NARRATIVES AS
SELECT 
    wo.work_order_id,
    wo.asset_id,
    wo.work_type,
    wo.priority,
    wo.status,
    wo.region,
    wo.created_date,
    wo.scheduled_date,
    wo.notes as narrative,
    a.asset_type,
    a.fire_threat_district,
    CONCAT(
        'Work Order ', wo.work_order_id, ': ',
        wo.work_type, ' - Priority: ', wo.priority, '. ',
        'Asset: ', a.asset_type, ' in ', wo.region, '. ',
        'Fire District: ', COALESCE(a.fire_threat_district, 'N/A'), '. ',
        'Notes: ', COALESCE(wo.notes, 'No additional notes')
    ) as search_text
FROM ATOMIC.WORK_ORDER wo
JOIN ATOMIC.ASSET a ON wo.asset_id = a.asset_id;

CREATE CORTEX SEARCH SERVICE DOCS.WORK_ORDER_SEARCH_SERVICE
ON WORK_ORDER_NARRATIVES
WAREHOUSE = RISK_COMPUTE_WH
TARGET_LAG = '1 hour'
AS (
    SELECT 
        work_order_id,
        asset_id,
        work_type,
        priority,
        status,
        region,
        asset_type,
        fire_threat_district,
        narrative,
        search_text
    FROM DOCS.WORK_ORDER_NARRATIVES
);

-- =====================================================
-- Step 5: Create AMI Anomaly Search for Water Treeing Discovery
-- =====================================================

SELECT '⚡ Step 5: Creating AMI Anomaly Search Service...' as STEP;

DROP CORTEX SEARCH SERVICE IF EXISTS DOCS.AMI_ANOMALY_SEARCH_SERVICE;

-- Create a view for AMI anomaly narratives
CREATE OR REPLACE VIEW DOCS.AMI_ANOMALY_NARRATIVES AS
SELECT 
    ami.reading_id,
    ami.asset_id,
    ami.meter_id,
    ami.reading_timestamp,
    ami.voltage_reading,
    ami.voltage_deviation_pct,
    ami.voltage_dip_flag,
    ami.rain_correlated_dip,
    ami.rainfall_24h_inches,
    a.asset_type,
    a.material,
    a.asset_age_years,
    a.moisture_exposure,
    CONCAT(
        'AMI Reading ', ami.reading_id, ': ',
        'Asset ', ami.asset_id, ' (', a.asset_type, ', ', COALESCE(a.material, 'Unknown'), '). ',
        'Voltage: ', ROUND(ami.voltage_reading, 1), 'V, Deviation: ', ROUND(ami.voltage_deviation_pct, 2), '%. ',
        CASE WHEN ami.voltage_dip_flag THEN 'VOLTAGE DIP DETECTED. ' ELSE '' END,
        CASE WHEN ami.rain_correlated_dip THEN 'RAIN-CORRELATED DIP - WATER TREEING INDICATOR. ' ELSE '' END,
        'Rainfall 24h: ', COALESCE(ROUND(ami.rainfall_24h_inches, 2), 0), ' inches. ',
        'Cable Age: ', COALESCE(a.asset_age_years, 0), ' years. ',
        'Moisture Exposure: ', COALESCE(a.moisture_exposure, 'Unknown')
    ) as search_text
FROM ATOMIC.AMI_READING ami
JOIN ATOMIC.ASSET a ON ami.asset_id = a.asset_id
WHERE ami.voltage_dip_flag = TRUE
   OR ami.rain_correlated_dip = TRUE
   OR ami.voltage_deviation_pct > 3;

CREATE CORTEX SEARCH SERVICE DOCS.AMI_ANOMALY_SEARCH_SERVICE
ON AMI_ANOMALY_NARRATIVES
WAREHOUSE = RISK_COMPUTE_WH
TARGET_LAG = '1 hour'
AS (
    SELECT 
        reading_id,
        asset_id,
        meter_id,
        reading_timestamp,
        voltage_reading,
        voltage_deviation_pct,
        voltage_dip_flag,
        rain_correlated_dip,
        rainfall_24h_inches,
        asset_type,
        material,
        asset_age_years,
        moisture_exposure,
        search_text
    FROM DOCS.AMI_ANOMALY_NARRATIVES
);

-- =====================================================
-- Step 6: Verify Search Services
-- =====================================================

SELECT '✅ Step 6: Verifying Cortex Search Services...' as STEP;

SHOW CORTEX SEARCH SERVICES IN DATABASE RISK_PLANNING_DB;

-- =====================================================
-- Step 7: Test Queries
-- =====================================================

SELECT '🧪 Step 7: Running test queries...' as STEP;

-- Test GO95 search
SELECT '--- Testing GO95 Search ---' as TEST;
-- SELECT * FROM TABLE(
--     RISK_PLANNING_DB.DOCS.GO95_SEARCH_SERVICE(
--         QUERY => 'vegetation clearance requirements for 12kV lines',
--         LIMIT => 5
--     )
-- );

-- Test Vegetation search  
SELECT '--- Testing Vegetation Search ---' as TEST;
-- SELECT * FROM TABLE(
--     RISK_PLANNING_DB.DOCS.VEGETATION_SEARCH_SERVICE(
--         QUERY => 'eucalyptus tree trimming fire district tier 3',
--         LIMIT => 5
--     )
-- );

-- Test Work Order search
SELECT '--- Testing Work Order Search ---' as TEST;
-- SELECT * FROM TABLE(
--     RISK_PLANNING_DB.DOCS.WORK_ORDER_SEARCH_SERVICE(
--         QUERY => 'emergency vegetation trim high fire risk',
--         LIMIT => 5
--     )
-- );

-- Test AMI Anomaly search (Water Treeing)
SELECT '--- Testing AMI Anomaly Search (Water Treeing) ---' as TEST;
-- SELECT * FROM TABLE(
--     RISK_PLANNING_DB.DOCS.AMI_ANOMALY_SEARCH_SERVICE(
--         QUERY => 'rain correlated voltage dip water treeing XLPE cable',
--         LIMIT => 10
--     )
-- );

-- =====================================================
-- Summary
-- =====================================================

SELECT '🎉 Cortex Search Deployment Complete!' as STATUS;

SELECT 
    'GO95_SEARCH_SERVICE' as SERVICE_NAME,
    'CPUC GO95 and regulatory compliance documents' as DESCRIPTION,
    'Search for clearance requirements, fire district regulations' as USE_CASE
UNION ALL
SELECT 
    'VEGETATION_SEARCH_SERVICE',
    'Vegetation management standards and species guidance',
    'Search for trimming standards, species-specific guidance'
UNION ALL
SELECT 
    'WORK_ORDER_SEARCH_SERVICE',
    'Work order narratives and field notes',
    'Search for similar work orders, field conditions'
UNION ALL
SELECT 
    'AMI_ANOMALY_SEARCH_SERVICE',
    'AMI voltage anomalies and Water Treeing indicators',
    'KEY FOR HIDDEN DISCOVERY: Search for rain-correlated voltage dips';

-- =====================================================
-- Hidden Discovery Preview
-- =====================================================

SELECT '🔍 HIDDEN DISCOVERY: Water Treeing Pattern Preview' as SECTION;

SELECT 
    a.material,
    a.moisture_exposure,
    COUNT(DISTINCT a.asset_id) as cable_count,
    AVG(a.asset_age_years) as avg_age_years,
    SUM(CASE WHEN ami.rain_correlated_dip THEN 1 ELSE 0 END) as rain_correlated_dips,
    ROUND(SUM(CASE WHEN ami.rain_correlated_dip THEN 1 ELSE 0 END)::FLOAT / 
          NULLIF(COUNT(*), 0) * 100, 2) as dip_rate_pct
FROM ATOMIC.ASSET a
JOIN ATOMIC.AMI_READING ami ON a.asset_id = ami.asset_id
WHERE a.asset_type = 'UNDERGROUND_CABLE'
GROUP BY a.material, a.moisture_exposure
HAVING SUM(CASE WHEN ami.rain_correlated_dip THEN 1 ELSE 0 END) > 0
ORDER BY rain_correlated_dips DESC;
