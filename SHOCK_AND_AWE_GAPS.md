# You Built Ferrari Internals But Put Them in a Camry Body

## VIGIL Risk Planning App - Shock & Awe Gap Analysis

**Date**: February 8, 2026  
**Status**: Handoff Documentation

---

## Executive Summary

The app has solid **backend plumbing** (4 ML models, Dynamic Tables, Cortex Agent) but the **UI completely fails to showcase the AI/ML sophistication**. It's a functional dashboard, not a "wow" demo.

**The ML models, Dynamic Tables, and Cortex Agent are sophisticated - but the UI presents them as simple cards and tables. The "shock and awe" comes from visualizing the intelligence, not hiding it behind plain text.**

---

## CRITICAL GAPS

### 1. AI Insights are FAKE

**File**: `copilot/frontend/src/pages/AssetMap.tsx` (lines 32-69)

```tsx
const generateAIInsight = (asset) => {
  const insights = ["Water treeing detected - ${Math.floor(Math.random() * 15 + 10)}% degradation"...]
  return insights[Math.floor(Math.random() * insights.length)] // <-- RANDOM!
}
```

**Problem**: Shows random strings, not actual ML predictions.

**Fix**: Query actual `ML.CABLE_FAILURE_PREDICTION` data with real degradation percentages.

---

### 2. No ML Explainability

You have 4 trained models but show **ZERO**:
- Feature importance charts (SHAP)
- Prediction confidence intervals
- "Why did ML flag this?" explanations
- Model calibration/accuracy metrics

**ML Assets Exist But Are Hidden**:
- `ASSET_HEALTH_PREDICTION` - GradientBoostingRegressor
- `VEGETATION_GROWTH_PREDICTION` - RandomForestRegressor
- `IGNITION_RISK_PREDICTION` - GradientBoostingClassifier
- `CABLE_FAILURE_PREDICTION` - Water Treeing Detection

---

### 3. Landing Page Stats are Hardcoded

**File**: `copilot/frontend/src/pages/Landing.tsx` (lines 46-51)

```tsx
const stats = [
  { value: '5,000', label: 'Grid Assets' },  // STATIC!
  { value: '945', label: 'Vegetation Points' },
  { value: '901', label: 'Active Work Orders' },
  { value: '3', label: 'Fire Districts' },
]
```

**Fix**: Fetch live counts from `/api/dashboard-metrics`.

---

### 4. No 3D Visualization Magic

**File**: `copilot/frontend/src/components/RiskMap3D.tsx`

Current implementation renders **flat 2D circles**. Missing:
- Deck.gl hexbin heatmaps
- 3D extrusions showing risk height
- Animated risk propagation
- Terrain contours for fire threat zones

---

### 5. Vegetation Page is a Basic Table

**File**: `copilot/frontend/src/pages/Vegetation.tsx`

Current: A filterable list with cards.

Missing:
- Growth trajectory sparklines per tree
- Days-to-contact countdown timers
- Risk heatmap by circuit
- Drag-to-reorder prioritization

---

### 6. Architecture Page is Static Boxes

**File**: `copilot/frontend/src/pages/Architecture.tsx`

Shows 4 columns of static text. Should have:
- Animated data flow paths
- Live query counts pulsing
- Click-to-zoom into each layer

---

## Feature-by-Feature Gap Matrix

| Feature | Current State | Shock & Awe Target |
|---------|---------------|-------------------|
| **Landing** | Typing animation + static stats | Hero video, live risk ticker, dramatic PSPS warning |
| **Dashboard** | Gauges + region bars + alert cards | Real-time risk pulse, animated transitions, live agent status |
| **Asset Map** | 2D Leaflet circles | deck.gl 3D hexbins, terrain overlay, animated fire spread |
| **Vegetation** | Filterable table | Interactive Gantt chart, growth projections, auto-scheduler |
| **ML Panel** | 4 model cards | SHAP waterfalls, prediction explanations, confidence bars |
| **Copilot** | Chat + thinking steps | Voice input, suggested follow-ups, inline charts |
| **Hidden Discovery** | Text response | Dramatic reveal animation, evidence chain visualization |

---

## Top 5 Missing "WOW Moments"

### 1. Water Treeing Discovery Animation
When VIGIL detects cable degradation, show:
- Rain-voltage correlation graph zooming in
- Cables pulsing red
- "Pattern discovered" confetti effect

### 2. Fire Season Hero Alert
Full-screen takeover when PSPS threshold met:
- Countdown timer
- Affected customer count ticking up
- Regional map highlighting danger zones

### 3. ML Confidence Visualization
When showing predictions, display:
- Probability distribution curves
- Confidence intervals
- Not just "HIGH RISK" text labels

### 4. 3D Risk Terrain
Fly-through of California with:
- Risk-colored extrusions rising from asset locations
- Terrain topography
- Fire threat district overlays

### 5. Real-time Agent Orchestration
Show 4 agent icons actively "thinking":
- Data flowing between agents during copilot queries
- Visual representation of multi-agent coordination
- Processing indicators per agent specialty

---

## Files Requiring Major Work

| File | Issue | Priority |
|------|-------|----------|
| `Landing.tsx:46-51` | Hardcoded stats | HIGH |
| `AssetMap.tsx:32-69` | Random fake AI insights | CRITICAL |
| `RiskMap3D.tsx` | 2D markers, not 3D viz | HIGH |
| `Vegetation.tsx` | Basic table, no charts | MEDIUM |
| `MLInsightsPanel.tsx` | No SHAP/explainability | HIGH |
| `Architecture.tsx` | Static diagram | LOW |

---

## What's Working Well

- **Copilot streaming** with thinking steps visualization
- **MLInsightsPanel** queries real data from Dynamic Tables
- **FireSeasonBanner** component exists and shows status
- **Agent personas** display in chat (Vegetation Guardian, Fire Risk Analyst, etc.)
- **Region/Risk filtering** works across pages

---

## Recommended Implementation Order

1. **Connect real ML predictions to Asset Map** - Replace `generateAIInsight()` with actual API calls
2. **Make Landing stats dynamic** - Simple API fetch
3. **Add SHAP feature importance** - Create `/api/ml/feature-importance/{model}` endpoint
4. **Upgrade to deck.gl 3D** - Replace Leaflet circles with HexagonLayer
5. **Add growth sparklines to Vegetation** - Use recharts mini charts
6. **Animate Architecture diagram** - Framer Motion data flow

---

## Summary

The backend infrastructure is enterprise-grade:
- 4 ML models trained and deployed
- Dynamic Tables aggregating predictions
- Cortex Agent with multi-persona routing
- Semantic model with verified queries

But the frontend presents this as:
- Static numbers
- Random text strings
- 2D circle markers
- Basic tables

**Fix the presentation layer to match the sophistication of the data layer.**
