# VIGIL - Vegetation & Infrastructure Grid Intelligence Layer

A comprehensive risk-based planning platform for utility wildfire mitigation, built on Snowflake.

## Overview

VIGIL is a next-generation utility risk management system that combines:
- **GO95 Compliance**: CPUC General Order 95 vegetation clearance requirements
- **Fire Risk Assessment**: Multi-factor ignition probability modeling
- **Asset Health Prediction**: ML-powered degradation forecasting
- **Hidden Discovery**: Water Treeing detection in underground cables via AMI correlation

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     VIGIL Platform                               │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Frontend      │    Backend      │         Snowflake           │
│   React/Deck.gl │    FastAPI      │                             │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ • 3D Risk Map   │ • Orchestrator  │ • Cortex Analyst            │
│ • Fire Countdown│ • 4 Agent       │ • Cortex Search             │
│ • Copilot Chat  │   Personas      │ • Snowpark ML               │
│ • Dashboard     │ • Work Orders   │ • Native App (SPCS)         │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

## Key Features

### 🔥 Fire Season Countdown
Dynamic countdown to California fire season (June 1 - November 30) with enhanced protocols during active season.

### 🌳 Vegetation Management
- GO95 clearance requirements by voltage class and fire threat district
- Species-specific growth rate modeling
- Trim priority scoring with fire risk weighting
- Automated work order generation

### ⚡ Asset Health Prediction
- Gradient Boosting model for condition forecasting
- Days-to-critical estimation
- Replacement priority scoring
- Integration with inspection schedules

### 🔍 Hidden Discovery: Water Treeing
The platform's signature feature - detecting invisible underground cable degradation:
- Correlates AMI (smart meter) voltage dips with rainfall events
- Identifies XLPE cables at risk of catastrophic failure
- Key indicators: 15-25 year age, high moisture exposure, rain correlation >0.5

### 🤖 Multi-Agent Copilot
Four specialized AI agents with distinct personas:

| Agent | Emoji | Focus | Catchphrase |
|-------|-------|-------|-------------|
| Vegetation Guardian | 🌳 | GO95 Compliance | "Every clearance deficit is a potential ignition source" |
| Asset Inspector | ⚡ | Equipment Health | "A healthy grid starts with healthy assets" |
| Fire Risk Analyst | 🔥 | Ignition Risk | "Fire season waits for no one" |
| Water Treeing Detective | 🔍 | Hidden Patterns | "The data sees what inspectors can't" |

## Database Schema

### Schemas
- **RAW**: Landing zone for source data
- **ATOMIC**: Cleansed, typed data
- **CONSTRUCTION_RISK**: Materialized views and aggregations
- **ML**: Model predictions and features
- **DOCS**: Document storage for Cortex Search
- **SPCS**: Native App runtime artifacts

### Key Tables
- `ATOMIC.ASSET` - 5,000 utility assets across 5 regions
- `ATOMIC.CIRCUIT` - Circuit topology with fire threat districts
- `ATOMIC.VEGETATION_ENCROACHMENT` - Clearance measurements
- `ATOMIC.RISK_ASSESSMENT` - Composite risk scores
- `ATOMIC.WORK_ORDER` - Work order management
- `ATOMIC.AMI_READING` - Smart meter voltage data
- `ML.CABLE_FAILURE_PREDICTION` - Water Treeing predictions

## Regions

| Region | Area | Key Risk Factors |
|--------|------|------------------|
| NorCal | Northern California | High wind, eucalyptus, PSPS prone |
| SoCal | Southern California | Santa Ana winds, urban interface |
| PNW | Pacific Northwest | Conifer forests, moisture variation |
| Southwest | Arizona/Nevada | Desert vegetation, extreme heat |
| Mountain | Colorado/Utah | Elevation changes, winter storms |

## ML Models

### 1. Asset Health Predictor
- **Algorithm**: Gradient Boosting Regressor
- **Features**: Age, condition, material, inspection history
- **Output**: Predicted health score, days to critical

### 2. Vegetation Growth Predictor
- **Algorithm**: Random Forest Regressor
- **Features**: Species, clearance, season, weather
- **Output**: Growth rate, days to contact

### 3. Ignition Risk Predictor
- **Algorithm**: XGBoost Classifier
- **Features**: Asset condition, vegetation, weather, fire district
- **Output**: Ignition probability, risk tier

### 4. Cable Failure Predictor (Water Treeing)
- **Algorithm**: XGBoost Classifier
- **Features**: Material, age, moisture, AMI voltage patterns
- **Output**: Failure probability, rain correlation score

## Deployment

### Prerequisites
- Snowflake account with Cortex features enabled
- Python 3.10+
- Node.js 18+

### Backend Setup
```bash
cd copilot/backend
pip install -r requirements.txt
python -m api.main
```

### Frontend Setup
```bash
cd copilot/frontend
npm install
npm run dev
```

### SPCS Deployment
```sql
-- Create compute pool
CREATE COMPUTE POOL VIGIL_COMPUTE_POOL
    MIN_NODES = 1
    MAX_NODES = 3
    INSTANCE_FAMILY = CPU_X64_S;

-- Create service
CREATE SERVICE VIGIL_SERVICE
    IN COMPUTE POOL VIGIL_COMPUTE_POOL
    FROM SPECIFICATION_FILE = 'spec.yaml';
```

## API Endpoints

### Core
- `GET /` - API info with fire season status
- `GET /health` - Health check
- `GET /fire-season` - Current fire season countdown

### Chat/Copilot
- `POST /chat` - Send message to copilot
- `POST /chat/stream` - Stream response via SSE

### Dashboard
- `GET /dashboard/metrics` - All dashboard metrics
- `GET /dashboard/map` - GeoJSON for 3D map

### Assets
- `GET /assets` - Asset list with filtering
- `GET /assets/summary` - Summary by region/type
- `GET /assets/replacement-priorities` - Prioritized replacements

### Vegetation
- `GET /vegetation` - Encroachment data
- `GET /vegetation/compliance` - GO95 compliance summary
- `GET /vegetation/trim-priorities` - Trim priorities
- `GET /vegetation/clearance-requirement` - GO95 lookup

### Risk
- `GET /risk` - Risk assessments
- `GET /risk/summary` - Risk by region/tier
- `GET /risk/psps-candidates` - PSPS candidate circuits

### Work Orders
- `GET /work-orders` - Work order list
- `POST /work-orders` - Create work order

### Hidden Discovery
- `GET /discovery/water-treeing` - Water Treeing candidates
- `GET /discovery/ami-correlation` - AMI voltage analysis

## GO95 Clearance Requirements

| Fire District | Low Voltage | Medium Voltage | High Voltage | Transmission |
|---------------|-------------|----------------|--------------|--------------|
| Tier 3        | 4 ft        | 6 ft           | 12 ft        | 15 ft        |
| Tier 2        | 4 ft        | 4 ft           | 6 ft         | 10 ft        |
| Tier 1        | 2.5 ft      | 4 ft           | 6 ft         | 10 ft        |
| Non-HFTD      | 2.5 ft      | 4 ft           | 4 ft         | 10 ft        |

## Water Treeing Detection

Water Treeing is a degradation mechanism in XLPE-insulated underground cables where moisture creates tree-like structures in the insulation, eventually causing dielectric failure.

### Key Insight
**This failure mode is invisible to visual inspection.** We detect it by correlating AMI voltage anomalies with rainfall events.

### Detection Criteria
- Material: XLPE (Cross-linked Polyethylene)
- Age: 15-25 years (peak failure window)
- Moisture Exposure: HIGH
- Rain Correlation Score: >0.5

### How It Works
1. Analyze voltage readings from downstream smart meters
2. Identify voltage dip events (>3% deviation)
3. Correlate dip timing with rainfall in the area
4. Flag cables with >50% rain-correlated dips
5. XGBoost model predicts failure probability

## License

Proprietary - Snowflake Demo Application

## Contact

Built with ❤️ and ☕ by Snowflake Field Engineering
# construction-risk-planning
