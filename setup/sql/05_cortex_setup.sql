/*
=============================================================================
VIGIL Risk Planning - Cortex Search & Semantic Model Setup
=============================================================================
Script 5: Create Cortex Search services and deploy semantic model

Run after 04_generate_sample_data_part2.sql
Requires Cortex features enabled on the account
=============================================================================
*/

USE DATABASE RISK_PLANNING_DB;
USE WAREHOUSE RISK_COMPUTE_WH;

-- =====================
-- POPULATE GO95 DOCUMENTS
-- =====================
USE SCHEMA DOCS;

-- Insert GO95 Rule 35 clearance requirements
INSERT INTO GO95_DOCUMENTS (DOC_ID, DOCUMENT_NAME, SECTION_NUMBER, SECTION_TITLE, CONTENT, 
    VOLTAGE_CLASS, FIRE_THREAT_DISTRICT, CLEARANCE_REQUIREMENT_FT, EFFECTIVE_DATE)
VALUES
-- Tier 3 Requirements
('GO95-R35-T3-LV', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Tier 3 Low Voltage',
 'In Tier 3 High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 4 feet from low voltage conductors (750V or less) to vegetation at the time of trimming. This clearance must account for vegetation growth and conductor movement under wind conditions.',
 'LOW_VOLTAGE', 'TIER_3', 4.0, '2020-01-01'),

('GO95-R35-T3-MV', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Tier 3 Medium Voltage',
 'In Tier 3 High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 6 feet from medium voltage conductors (2.4kV to 35kV) to vegetation at the time of trimming. Enhanced clearances apply during fire season (June 1 - November 30).',
 'MEDIUM_VOLTAGE', 'TIER_3', 6.0, '2020-01-01'),

('GO95-R35-T3-HV', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Tier 3 High Voltage',
 'In Tier 3 High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 12 feet from high voltage conductors (35kV to 110kV) to vegetation at the time of trimming. This is the most stringent requirement for distribution-level voltages.',
 'HIGH_VOLTAGE', 'TIER_3', 12.0, '2020-01-01'),

('GO95-R35-T3-TR', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Tier 3 Transmission',
 'In Tier 3 High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 15 feet from transmission conductors (110kV and above) to vegetation. Additional clearances may be required based on conductor sag calculations.',
 'TRANSMISSION', 'TIER_3', 15.0, '2020-01-01'),

-- Tier 2 Requirements
('GO95-R35-T2-LV', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Tier 2 Low Voltage',
 'In Tier 2 High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 4 feet from low voltage conductors to vegetation at the time of trimming.',
 'LOW_VOLTAGE', 'TIER_2', 4.0, '2020-01-01'),

('GO95-R35-T2-MV', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Tier 2 Medium Voltage',
 'In Tier 2 High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 4 feet from medium voltage conductors to vegetation at the time of trimming.',
 'MEDIUM_VOLTAGE', 'TIER_2', 4.0, '2020-01-01'),

('GO95-R35-T2-HV', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Tier 2 High Voltage',
 'In Tier 2 High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 6 feet from high voltage conductors to vegetation at the time of trimming.',
 'HIGH_VOLTAGE', 'TIER_2', 6.0, '2020-01-01'),

('GO95-R35-T2-TR', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Tier 2 Transmission',
 'In Tier 2 High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 10 feet from transmission conductors to vegetation at the time of trimming.',
 'TRANSMISSION', 'TIER_2', 10.0, '2020-01-01'),

-- Non-HFTD Requirements
('GO95-R35-NH-LV', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Non-HFTD Low Voltage',
 'In non-High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 2.5 feet from low voltage conductors to vegetation.',
 'LOW_VOLTAGE', 'NON_HFTD', 2.5, '2020-01-01'),

('GO95-R35-NH-MV', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Non-HFTD Medium Voltage',
 'In non-High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 4 feet from medium voltage conductors to vegetation.',
 'MEDIUM_VOLTAGE', 'NON_HFTD', 4.0, '2020-01-01'),

('GO95-R35-NH-HV', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Non-HFTD High Voltage',
 'In non-High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 4 feet from high voltage conductors to vegetation.',
 'HIGH_VOLTAGE', 'NON_HFTD', 4.0, '2020-01-01'),

('GO95-R35-NH-TR', 'CPUC General Order 95', 'Rule 35', 'Vegetation Clearance - Non-HFTD Transmission',
 'In non-High Fire-Threat Districts, utilities must maintain a minimum radial clearance of 10 feet from transmission conductors to vegetation.',
 'TRANSMISSION', 'NON_HFTD', 10.0, '2020-01-01'),

-- General GO95 Information
('GO95-OVERVIEW', 'CPUC General Order 95', 'Overview', 'GO95 Overview',
 'CPUC General Order 95 establishes requirements for overhead electric line construction and vegetation management in California. The regulations are designed to ensure public safety and reduce wildfire risk from utility infrastructure. Fire-Threat Districts are classified as Tier 1, Tier 2, and Tier 3, with Tier 3 being the highest risk areas.',
 NULL, NULL, NULL, '2020-01-01'),

('GO95-FIRE-SEASON', 'CPUC General Order 95', 'Fire Season', 'California Fire Season Definition',
 'California fire season typically runs from June 1 through November 30, though it may be extended based on weather conditions. During fire season, utilities must implement enhanced vegetation management protocols, increase patrol frequency, and be prepared for Public Safety Power Shutoff (PSPS) events.',
 NULL, NULL, NULL, '2020-01-01'),

('GO95-PSPS', 'CPUC General Order 95', 'PSPS', 'Public Safety Power Shutoff Guidelines',
 'Public Safety Power Shutoff (PSPS) is a preventive measure where utilities de-energize power lines during extreme fire weather conditions. PSPS events are typically triggered by: Red Flag Warnings, wind speeds exceeding 25 mph with gusts over 45 mph, low humidity below 20%, and dry fuel conditions. Utilities must notify affected customers and coordinate with emergency services.',
 NULL, NULL, NULL, '2020-01-01');

-- Insert vegetation management procedures
INSERT INTO VEGETATION_PROCEDURES (DOC_ID, PROCEDURE_NAME, SPECIES, PROCEDURE_TYPE, CONTENT, 
    SAFETY_REQUIREMENTS, EQUIPMENT_NEEDED)
VALUES
('VP-EUC-001', 'Eucalyptus Management', 'EUCALYPTUS', 'TRIMMING',
 'Eucalyptus trees require aggressive management due to their rapid growth rate (up to 6 feet per year) and highly flammable bark. Crown reduction and directional pruning should be performed to maintain clearance. Remove dead branches and hanging bark which are extreme fire hazards.',
 'Use proper PPE including hard hat, safety glasses, and chainsaw chaps. Maintain minimum approach distance from energized conductors. Have fire suppression equipment on site.',
 'Bucket truck, chainsaw, pole pruner, chipper'),

('VP-OAK-001', 'Oak Tree Management', 'OAK', 'TRIMMING',
 'Oak trees are protected species in many California jurisdictions. Coordinate with certified arborist before trimming. Use natural pruning techniques that maintain tree health. Avoid removing more than 20% of canopy in a single year.',
 'Verify permits are in place for protected species. Standard electrical safety protocols apply.',
 'Bucket truck, hand saws, pole pruner'),

('VP-PALM-001', 'Palm Tree Management', 'PALM', 'TRIMMING',
 'Palm trees require regular removal of dead fronds which are extremely flammable. The 9 o''clock to 3 o''clock rule should be followed - remove fronds below the horizontal plane. Never skin palm trunks.',
 'Be aware of wildlife (rats, bees) in dead fronds. Use proper fall protection when working from bucket.',
 'Bucket truck, machete, hand saw'),

('VP-MANZ-001', 'Manzanita Management', 'MANZANITA', 'REMOVAL',
 'Manzanita is a highly flammable native shrub that should be removed or heavily reduced within clearance zones. Due to its fire-adapted nature, complete removal is often recommended in Tier 2 and Tier 3 fire districts.',
 'Be cautious of steep terrain where manzanita typically grows. Have fire suppression ready due to extreme flammability.',
 'Chainsaw, brush cutter, hand tools');

-- =====================
-- CREATE CORTEX SEARCH SERVICES
-- =====================

-- GO95 Search Service
CREATE OR REPLACE CORTEX SEARCH SERVICE GO95_SEARCH_SERVICE
  ON CONTENT
  ATTRIBUTES SECTION_NUMBER, VOLTAGE_CLASS, FIRE_THREAT_DISTRICT
  WAREHOUSE = RISK_COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT 
      DOC_ID,
      DOCUMENT_NAME,
      SECTION_NUMBER,
      SECTION_TITLE,
      CONTENT,
      VOLTAGE_CLASS,
      FIRE_THREAT_DISTRICT,
      CLEARANCE_REQUIREMENT_FT
    FROM GO95_DOCUMENTS
  );

-- Vegetation Procedures Search Service  
CREATE OR REPLACE CORTEX SEARCH SERVICE VEGETATION_SEARCH_SERVICE
  ON CONTENT
  ATTRIBUTES SPECIES, PROCEDURE_TYPE
  WAREHOUSE = RISK_COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT 
      DOC_ID,
      PROCEDURE_NAME,
      SPECIES,
      PROCEDURE_TYPE,
      CONTENT,
      SAFETY_REQUIREMENTS,
      EQUIPMENT_NEEDED
    FROM VEGETATION_PROCEDURES
  );

-- Work Order Search Service (for finding similar past work)
USE SCHEMA ATOMIC;

CREATE OR REPLACE CORTEX SEARCH SERVICE RISK_PLANNING_DB.DOCS.WORK_ORDER_SEARCH_SERVICE
  ON DESCRIPTION
  ATTRIBUTES WORK_ORDER_TYPE, PRIORITY, STATUS
  WAREHOUSE = RISK_COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT 
      WORK_ORDER_ID,
      WORK_ORDER_TYPE,
      PRIORITY,
      STATUS,
      DESCRIPTION,
      ESTIMATED_COST,
      SCHEDULED_DATE
    FROM WORK_ORDER
    WHERE STATUS = 'COMPLETED'
  );

-- =====================
-- CREATE SEMANTIC MODEL
-- =====================
-- First, upload the semantic model YAML to the stage
-- This is done via the PUT command or Snowsight UI

-- Create the semantic model file content
SELECT $$ 
name: risk_semantic_model
description: VIGIL Risk Planning Semantic Model for Cortex Analyst
tables:
  - name: ASSETS
    base_table: RISK_PLANNING_DB.ATOMIC.ASSET
    description: Utility assets including poles, transformers, conductors, and underground cables
    dimensions:
      - name: asset_id
        expr: ASSET_ID
        description: Unique identifier for the asset
      - name: asset_type
        expr: ASSET_TYPE
        description: Type of asset (POLE, TRANSFORMER, CONDUCTOR, UNDERGROUND_CABLE, SWITCH, FUSE, CAPACITOR)
      - name: material
        expr: MATERIAL
        description: Construction material
      - name: voltage_class
        expr: VOLTAGE_CLASS
        description: Voltage classification (LOW_VOLTAGE, MEDIUM_VOLTAGE, HIGH_VOLTAGE, TRANSMISSION)
      - name: moisture_exposure
        expr: MOISTURE_EXPOSURE
        description: Moisture exposure level (LOW, MEDIUM, HIGH)
      - name: wind_exposure
        expr: WIND_EXPOSURE
        description: Wind exposure level (LOW, MEDIUM, HIGH)
    measures:
      - name: asset_count
        expr: COUNT(*)
        description: Number of assets
      - name: avg_condition
        expr: AVG(CONDITION_SCORE)
        description: Average condition score (0-1)
      - name: avg_age
        expr: AVG(ASSET_AGE_YEARS)
        description: Average asset age in years
      - name: total_replacement_cost
        expr: SUM(REPLACEMENT_COST)
        description: Total replacement cost in dollars
        
  - name: CIRCUITS
    base_table: RISK_PLANNING_DB.ATOMIC.CIRCUIT
    description: Electrical circuits with fire threat district classification
    dimensions:
      - name: circuit_id
        expr: CIRCUIT_ID
        description: Unique circuit identifier
      - name: circuit_name
        expr: CIRCUIT_NAME
        description: Circuit name
      - name: fire_threat_district
        expr: FIRE_THREAT_DISTRICT
        description: CPUC fire threat classification (TIER_1, TIER_2, TIER_3, NON_HFTD)
      - name: psps_eligible
        expr: PSPS_ELIGIBLE
        description: Whether circuit is eligible for Public Safety Power Shutoff
    measures:
      - name: circuit_count
        expr: COUNT(*)
        description: Number of circuits
      - name: total_customers
        expr: SUM(TOTAL_CUSTOMERS)
        description: Total customers served
      - name: total_circuit_miles
        expr: SUM(CIRCUIT_MILES)
        description: Total circuit miles

  - name: VEGETATION
    base_table: RISK_PLANNING_DB.ATOMIC.VEGETATION_ENCROACHMENT
    description: Vegetation encroachment measurements and GO95 compliance
    dimensions:
      - name: species
        expr: SPECIES
        description: Tree species
      - name: trim_priority
        expr: TRIM_PRIORITY
        description: Trim priority (CRITICAL, HIGH, MEDIUM, LOW)
      - name: tree_health
        expr: TREE_HEALTH
        description: Tree health status
    measures:
      - name: encroachment_count
        expr: COUNT(*)
        description: Number of encroachments
      - name: avg_clearance
        expr: AVG(CURRENT_CLEARANCE_FT)
        description: Average current clearance in feet
      - name: avg_deficit
        expr: AVG(CASE WHEN CLEARANCE_DEFICIT_FT > 0 THEN CLEARANCE_DEFICIT_FT ELSE 0 END)
        description: Average clearance deficit for non-compliant spans
      - name: total_trim_cost
        expr: SUM(ESTIMATED_TRIM_COST)
        description: Total estimated trim cost

  - name: RISK
    base_table: RISK_PLANNING_DB.ATOMIC.RISK_ASSESSMENT
    description: Fire risk assessments with multi-factor scoring
    dimensions:
      - name: risk_tier
        expr: RISK_TIER
        description: Risk classification (CRITICAL, HIGH, MEDIUM, LOW)
      - name: assessment_method
        expr: ASSESSMENT_METHOD
        description: Assessment methodology
    measures:
      - name: avg_fire_risk
        expr: AVG(FIRE_RISK_SCORE)
        description: Average fire risk score
      - name: avg_ignition_probability
        expr: AVG(IGNITION_PROBABILITY)
        description: Average ignition probability
      - name: avg_composite_risk
        expr: AVG(COMPOSITE_RISK_SCORE)
        description: Average composite risk score

  - name: LOCATIONS
    base_table: RISK_PLANNING_DB.ATOMIC.LOCATION
    description: Geographic locations for assets and circuits
    dimensions:
      - name: region
        expr: REGION
        description: Geographic region (NorCal, SoCal, PNW, Southwest, Mountain)
      - name: county
        expr: COUNTY
        description: County name
      - name: terrain_type
        expr: TERRAIN_TYPE
        description: Terrain classification
      - name: land_use
        expr: LAND_USE
        description: Land use type

  - name: WORK_ORDERS
    base_table: RISK_PLANNING_DB.ATOMIC.WORK_ORDER
    description: Work orders for vegetation management, asset replacement, and maintenance
    dimensions:
      - name: work_order_type
        expr: WORK_ORDER_TYPE
        description: Type of work order
      - name: priority
        expr: PRIORITY
        description: Priority level (CRITICAL, HIGH, MEDIUM, LOW)
      - name: status
        expr: STATUS
        description: Current status
    measures:
      - name: work_order_count
        expr: COUNT(*)
        description: Number of work orders
      - name: total_estimated_cost
        expr: SUM(ESTIMATED_COST)
        description: Total estimated cost

relationships:
  - name: asset_to_circuit
    left_table: ASSETS
    right_table: CIRCUITS
    join_type: many_to_one
    relationship_columns:
      - left_column: CIRCUIT_ID
        right_column: CIRCUIT_ID
        
  - name: asset_to_location
    left_table: ASSETS
    right_table: LOCATIONS
    join_type: many_to_one
    relationship_columns:
      - left_column: LOCATION_ID
        right_column: LOCATION_ID

verified_queries:
  - name: assets_by_region
    question: How many assets are in each region?
    sql: |
      SELECT l.REGION, COUNT(*) as ASSET_COUNT
      FROM RISK_PLANNING_DB.ATOMIC.ASSET a
      JOIN RISK_PLANNING_DB.ATOMIC.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
      GROUP BY l.REGION
      ORDER BY ASSET_COUNT DESC
      
  - name: high_risk_assets
    question: What are the critical and high risk assets?
    sql: |
      SELECT r.RISK_TIER, a.ASSET_TYPE, COUNT(*) as COUNT
      FROM RISK_PLANNING_DB.ATOMIC.RISK_ASSESSMENT r
      JOIN RISK_PLANNING_DB.ATOMIC.ASSET a ON r.ASSET_ID = a.ASSET_ID
      WHERE r.RISK_TIER IN ('CRITICAL', 'HIGH')
      GROUP BY r.RISK_TIER, a.ASSET_TYPE
      ORDER BY r.RISK_TIER, COUNT DESC
      
  - name: compliance_by_fire_district
    question: What is the GO95 compliance status by fire threat district?
    sql: |
      SELECT c.FIRE_THREAT_DISTRICT,
             COUNT(*) as TOTAL_SPANS,
             SUM(CASE WHEN v.CURRENT_CLEARANCE_FT < v.REQUIRED_CLEARANCE_FT THEN 1 ELSE 0 END) as NON_COMPLIANT
      FROM RISK_PLANNING_DB.ATOMIC.VEGETATION_ENCROACHMENT v
      JOIN RISK_PLANNING_DB.ATOMIC.ASSET a ON v.ASSET_ID = a.ASSET_ID
      JOIN RISK_PLANNING_DB.ATOMIC.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
      GROUP BY c.FIRE_THREAT_DISTRICT
      ORDER BY c.FIRE_THREAT_DISTRICT
$$ AS SEMANTIC_MODEL_YAML;

-- NOTE: Save the above YAML to a file and upload using:
-- PUT file://risk_semantic_model.yaml @RISK_PLANNING_DB.CONSTRUCTION_RISK.SEMANTIC_MODELS AUTO_COMPRESS=FALSE;

SELECT 'Cortex Search and Semantic Model setup complete!' AS STATUS;
SELECT 'NOTE: Upload risk_semantic_model.yaml to @CONSTRUCTION_RISK.SEMANTIC_MODELS stage' AS REMINDER;
