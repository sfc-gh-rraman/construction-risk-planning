# Demo Requirements Document (DRD): Risk-Based Planning & Vegetation Management

## 1. Strategic Overview

*   **Problem Statement:** Utilities manage millions of assets across vast territories where risks are dynamic (e.g., wildfire, vegetation growth). Traditional "Cycle-Based" maintenance (trimming every 3 years) ignores actual risk, leading to over-spending on safe circuits while high-risk zones go unaddressed until a failure starts a fire.
*   **Target Business Goals (KPIs):**
    *   **Safety:** Reduce Wildfire Ignition Risk by 20%.
    *   **Reliability:** Decrease SAIDI (Outage Duration) by 15%.
    *   **Cost:** Optimize Vegetation Management budget by 10% (trimming only where needed).
*   **The "Wow" Moment:** A Program Manager asks, "Where is our highest wildfire risk next month?" Cortex displays a 3D map of the network, highlighting a specific span where LiDAR data shows a tree growing faster than expected into a conductor, combined with a "High Wind" forecast. The system recommends an immediate "Hot Spot" trim.
*   **Hidden Discovery:**
    *   **Discovery Statement:** "A 'Silent Failure' mode in underground cables is predicted 30 days in advance by correlating micro-outage blips (Smart Meter data) with soil moisture saturation levels, preventing catastrophic failure."
    *   **Surface Appearance:** Cable passes VLF tests; no customer complaints.
    *   **Revealed Reality:** AMI data shows momentary voltage dips during rain events—a signature of "Water Treeing" insulation breakdown.
    *   **Business Impact:** Replacing the cable section proactively costs $10k vs. $100k emergency repair + regulatory fines.

## 2. User Personas & Stories

| Persona Level | Role | User Story | Key Visuals |
| :--- | :--- | :--- | :--- |
| **Strategic** | **VP Grid Operations** | "As a VP, I want to justify our rate case to the PUC by showing how our risk-based investment plan reduces public safety danger." | System-Wide Risk Heatmap, Risk Reduction vs. Spend Curve, Regulatory Compliance Dashboard. |
| **Operational** | **Veg Program Manager** | "As a Manager, I want to deploy crews to the circuits with the highest 'Grow-in' probability before fire season starts." | Prioritized Trim List, Vegetation Growth Rate Map, Crew Dispatch Status. |
| **Technical** | **Reliability Engineer** | "As an Engineer, I want to train models on LiDAR point clouds to distinguish between 'Fast Growing' and 'Slow Growing' tree species." | LiDAR Classification Viewer, Species Distribution Chart, Model Confusion Matrix. |

## 3. Data Architecture

### 3.1 Schema Structure
All data resides in `RISK_PLANNING_DB` with the following schemas:

*   **`RAW`**: Landing zone for GIS Shapefiles, LiDAR Point Clouds, and Outage Logs.
*   **`ATOMIC`**: Normalized Enterprise Data Model.
*   **`CONSTRUCTION_RISK`**: Data Mart for consumption.

### 3.2 RAW Layer
*   `RAW.ASSET_GIS`: Spatial data for poles, wires, transformers.
*   `RAW.LIDAR_DATA`: Processed vegetation intrusion rasters.
*   `RAW.WEATHER_FORECAST`: Hyper-local wind/temp/humidity.

### 3.3 ATOMIC Layer (Core & Extensions)
*   **Core Entities** (Mapped from Data Dictionary):
    *   `ATOMIC.ASSET`:
        *   *Columns*: `ASSET_ID`, `ASSET_TYPE`, `INSTALL_DATE`, `MANUFACTURER`.
    *   `ATOMIC.LOCATION` (Risk Zones):
        *   *Columns*: `LOCATION_ID`, `ZONE_NAME` (e.g., High Fire Threat District), `GEOMETRY`.
    *   `ATOMIC.MAINTENANCE_WORK_ORDER`:
        *   *Columns*: `WORK_ORDER_ID`, `ASSET_ID`, `ACTIVITY_TYPE` (Trim/Inspect), `COMPLETION_DATE`.
*   **Extension Entities** (Project Specific):
    *   `ATOMIC.RISK_ASSESSMENT` (Extension):
        *   *Columns*: `ASSESSMENT_ID`, `ASSET_ID`, `DATE`, `RISK_SCORE`, `FAILURE_PROBABILITY`, `IGNITION_RISK`.
    *   `ATOMIC.VEGETATION_ENCROACHMENT` (Extension):
        *   *Columns*: `ENCROACHMENT_ID`, `ASSET_ID`, `DISTANCE_TO_CONDUCTOR`, `TREE_SPECIES`, `GROWTH_RATE`.

### 3.4 Data Mart Layer (`CONSTRUCTION_RISK`)
*   `CONSTRUCTION_RISK.CIRCUIT_RISK_PROFILE` (View): Aggregated risk per feeder.
*   `CONSTRUCTION_RISK.OPTIMIZED_WORK_PLAN` (Table): Recommended actions (Trim/Replace).
*   `CONSTRUCTION_RISK.ASSET_HEALTH_SCORE` (Table): Composite ML score.

## 4. Cortex Intelligence Specifications

### 4.1 Cortex Analyst (Structured)
*   **Semantic Model Scope**:
    *   **Measures**: `Miles_Trimmed`, `Risk_Reduction_Value`, `Estimated_Outage_Hours`, `Budget_Variance`.
    *   **Dimensions**: `Circuit`, `District`, `Risk_Tier`, `Vegetation_Type`.
*   **Golden Query**: "List the top 10 circuits with the highest projected wildfire risk for August."

### 4.2 Cortex Search (Unstructured)
*   **Service Name**: `COMPLIANCE_DOCS_SEARCH`
*   **Source Data**: CPUC General Order 95, Vegetation Management Standards, Forestry Guides.
*   **Indexing Strategy**: Index by `Regulation_Code` and `Asset_Type`.
*   **Sample Prompt**: "What is the minimum radial clearance required for 12kV conductors in Tier 3 Fire Zones?"

## 5. Streamlit Application UX/UI

### Page 1: Risk Control Tower (Strategic)
*   **Situation**: "Fire Season starts in 2 weeks. Are we ready?"
*   **Visuals**:
    *   **3D Risk Map**: Assets extruded by Risk Score.
    *   **Burn-down Chart**: "High Risk Spans" remaining to be trimmed.

### Page 2: Veg Management (Operational)
*   **Task**: "Plan next week's trimming."
*   **Visuals**:
    *   **LiDAR Overlay**: Point cloud showing tree proximity to wire.
    *   **Growth Simulator**: "Predicted Encroachment in 30 Days".
    *   **Action**: "Issue Work Order".

### Page 3: Asset Reliability (Technical)
*   **Action**: "Investigate underground cable failures."
*   **Visuals**:
    *   **Micro-Outage Plot**: Voltage sags correlated with rainfall.
    *   **Hidden Discovery**: The "Water Treeing" signature.

## 6. Success Criteria

*   **Technical**:
    *   Process 100 miles of LiDAR data into risk scores in < 1 hour.
    *   Predict vegetation encroachment with 90% accuracy (verified by field audit).
*   **Business**:
    *   Shift 10% of budget from "Cycle-Based" to "Risk-Based" work (saving $5M).
    *   Zero ignitions in High Fire Threat Districts.
