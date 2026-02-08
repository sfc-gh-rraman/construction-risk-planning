"""
VIGIL Risk-Based Planning - Synthetic Data Generator

Generates realistic synthetic data for utility risk management with:
- 5,000 assets across 5 regions (NorCal, SoCal, PNW, Southwest, Mountain)
- Real latitude/longitude for 3D map visualization
- ML-friendly patterns for the "Hidden Discovery" feature (Water Treeing)
- Dynamic fire season calculations
- Vegetation encroachment with species-based growth rates
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import uuid
from typing import List, Dict, Tuple

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# =============================================================================
# GEOGRAPHIC CONFIGURATION - Real utility territories
# =============================================================================

REGIONS = {
    "NORCAL": {
        "name": "Northern California",
        "utility_model": "PG&E-style",
        "fire_season_start_month": 5,
        "fire_season_start_day": 15,
        "fire_season_end_month": 11,
        "fire_season_end_day": 15,
        "asset_count": 1500,
        "fire_threat_distribution": {"TIER_3": 0.25, "TIER_2": 0.35, "TIER_1": 0.25, "NON_HFTD": 0.15},
        "avg_rainfall_in": 22,
        "locations": [
            {"name": "Santa Rosa District", "lat": 38.4404, "lon": -122.7141, "terrain": "HILLY", "veg_density": "HIGH"},
            {"name": "Napa Valley", "lat": 38.2975, "lon": -122.2869, "terrain": "HILLY", "veg_density": "HIGH"},
            {"name": "Paradise Zone", "lat": 39.7596, "lon": -121.6219, "terrain": "MOUNTAINOUS", "veg_density": "VERY_HIGH"},
            {"name": "Sacramento Valley", "lat": 38.5816, "lon": -121.4944, "terrain": "FLAT", "veg_density": "MEDIUM"},
            {"name": "Redding District", "lat": 40.5865, "lon": -122.3917, "terrain": "MOUNTAINOUS", "veg_density": "HIGH"},
        ]
    },
    "SOCAL": {
        "name": "Southern California",
        "utility_model": "SCE-style",
        "fire_season_start_month": 5,
        "fire_season_start_day": 1,
        "fire_season_end_month": 12,
        "fire_season_end_day": 15,
        "asset_count": 1200,
        "fire_threat_distribution": {"TIER_3": 0.30, "TIER_2": 0.30, "TIER_1": 0.25, "NON_HFTD": 0.15},
        "avg_rainfall_in": 15,
        "locations": [
            {"name": "Malibu Canyon", "lat": 34.0259, "lon": -118.7798, "terrain": "CANYON", "veg_density": "HIGH"},
            {"name": "San Bernardino Mountains", "lat": 34.2439, "lon": -117.1858, "terrain": "MOUNTAINOUS", "veg_density": "HIGH"},
            {"name": "Orange County Hills", "lat": 33.7175, "lon": -117.8311, "terrain": "HILLY", "veg_density": "MEDIUM"},
            {"name": "Riverside District", "lat": 33.9806, "lon": -117.3755, "terrain": "FLAT", "veg_density": "LOW"},
            {"name": "Ventura County", "lat": 34.3705, "lon": -119.1391, "terrain": "HILLY", "veg_density": "HIGH"},
        ]
    },
    "PNW": {
        "name": "Pacific Northwest",
        "utility_model": "PacifiCorp-style",
        "fire_season_start_month": 7,
        "fire_season_start_day": 1,
        "fire_season_end_month": 10,
        "fire_season_end_day": 1,
        "asset_count": 800,
        "fire_threat_distribution": {"TIER_3": 0.10, "TIER_2": 0.25, "TIER_1": 0.35, "NON_HFTD": 0.30},
        "avg_rainfall_in": 45,
        "locations": [
            {"name": "Portland Metro", "lat": 45.5152, "lon": -122.6784, "terrain": "FLAT", "veg_density": "HIGH"},
            {"name": "Columbia Gorge", "lat": 45.7054, "lon": -121.5215, "terrain": "CANYON", "veg_density": "HIGH"},
            {"name": "Seattle Suburbs", "lat": 47.6062, "lon": -122.3321, "terrain": "HILLY", "veg_density": "HIGH"},
            {"name": "Willamette Valley", "lat": 44.9429, "lon": -123.0351, "terrain": "FLAT", "veg_density": "MEDIUM"},
        ]
    },
    "SOUTHWEST": {
        "name": "Southwest (Arizona/Nevada)",
        "utility_model": "APS-style",
        "fire_season_start_month": 6,
        "fire_season_start_day": 1,
        "fire_season_end_month": 9,
        "fire_season_end_day": 30,
        "asset_count": 800,
        "fire_threat_distribution": {"TIER_3": 0.05, "TIER_2": 0.15, "TIER_1": 0.30, "NON_HFTD": 0.50},
        "avg_rainfall_in": 8,
        "locations": [
            {"name": "Phoenix Metro", "lat": 33.4484, "lon": -112.0740, "terrain": "FLAT", "veg_density": "LOW"},
            {"name": "Tucson District", "lat": 32.2226, "lon": -110.9747, "terrain": "HILLY", "veg_density": "LOW"},
            {"name": "Las Vegas Valley", "lat": 36.1699, "lon": -115.1398, "terrain": "FLAT", "veg_density": "LOW"},
            {"name": "Flagstaff Mountain", "lat": 35.1983, "lon": -111.6513, "terrain": "MOUNTAINOUS", "veg_density": "MEDIUM"},
        ]
    },
    "MOUNTAIN": {
        "name": "Mountain Region (Colorado/Utah)",
        "utility_model": "Xcel-style",
        "fire_season_start_month": 6,
        "fire_season_start_day": 15,
        "fire_season_end_month": 10,
        "fire_season_end_day": 15,
        "asset_count": 700,
        "fire_threat_distribution": {"TIER_3": 0.15, "TIER_2": 0.25, "TIER_1": 0.35, "NON_HFTD": 0.25},
        "avg_rainfall_in": 16,
        "locations": [
            {"name": "Denver Metro", "lat": 39.7392, "lon": -104.9903, "terrain": "FLAT", "veg_density": "LOW"},
            {"name": "Boulder Foothills", "lat": 40.0150, "lon": -105.2705, "terrain": "MOUNTAINOUS", "veg_density": "MEDIUM"},
            {"name": "Salt Lake Valley", "lat": 40.7608, "lon": -111.8910, "terrain": "FLAT", "veg_density": "LOW"},
            {"name": "Colorado Springs", "lat": 38.8339, "lon": -104.8214, "terrain": "HILLY", "veg_density": "MEDIUM"},
        ]
    }
}

# =============================================================================
# VEGETATION SPECIES - Growth rates and characteristics
# =============================================================================

TREE_SPECIES = {
    "EUCALYPTUS": {"growth_rate_ft": 6.0, "category": "VERY_FAST", "regions": ["NORCAL", "SOCAL"], "fire_risk": "HIGH"},
    "COAST_LIVE_OAK": {"growth_rate_ft": 2.0, "category": "MEDIUM", "regions": ["NORCAL", "SOCAL"], "fire_risk": "MEDIUM"},
    "MONTEREY_PINE": {"growth_rate_ft": 3.0, "category": "FAST", "regions": ["NORCAL"], "fire_risk": "HIGH"},
    "DOUGLAS_FIR": {"growth_rate_ft": 2.5, "category": "MEDIUM", "regions": ["PNW", "MOUNTAIN"], "fire_risk": "MEDIUM"},
    "PONDEROSA_PINE": {"growth_rate_ft": 2.0, "category": "MEDIUM", "regions": ["MOUNTAIN", "SOUTHWEST"], "fire_risk": "HIGH"},
    "COTTONWOOD": {"growth_rate_ft": 5.0, "category": "VERY_FAST", "regions": ["SOUTHWEST", "MOUNTAIN"], "fire_risk": "LOW"},
    "JUNIPER": {"growth_rate_ft": 0.5, "category": "SLOW", "regions": ["SOUTHWEST", "MOUNTAIN"], "fire_risk": "MEDIUM"},
    "PALM": {"growth_rate_ft": 1.5, "category": "SLOW", "regions": ["SOCAL", "SOUTHWEST"], "fire_risk": "HIGH"},
    "WESTERN_RED_CEDAR": {"growth_rate_ft": 2.0, "category": "MEDIUM", "regions": ["PNW"], "fire_risk": "LOW"},
    "BRUSH": {"growth_rate_ft": 4.0, "category": "FAST", "regions": ["NORCAL", "SOCAL"], "fire_risk": "VERY_HIGH"},
}

# =============================================================================
# CPUC GO95 CLEARANCE REQUIREMENTS (actual values)
# =============================================================================

CLEARANCE_REQUIREMENTS = {
    # Format: (voltage_class, fire_tier) -> required_radial_clearance_ft
    ("4KV", "TIER_3"): 12.0,
    ("4KV", "TIER_2"): 6.0,
    ("4KV", "TIER_1"): 4.0,
    ("4KV", "NON_HFTD"): 4.0,
    ("12KV", "TIER_3"): 12.0,
    ("12KV", "TIER_2"): 6.0,
    ("12KV", "TIER_1"): 4.0,
    ("12KV", "NON_HFTD"): 4.0,
    ("21KV", "TIER_3"): 12.0,
    ("21KV", "TIER_2"): 6.0,
    ("21KV", "TIER_1"): 4.5,
    ("21KV", "NON_HFTD"): 4.5,
    ("33KV", "TIER_3"): 15.0,
    ("33KV", "TIER_2"): 8.0,
    ("33KV", "TIER_1"): 6.0,
    ("33KV", "NON_HFTD"): 6.0,
    ("69KV", "TIER_3"): 18.0,
    ("69KV", "TIER_2"): 12.0,
    ("69KV", "TIER_1"): 10.0,
    ("69KV", "NON_HFTD"): 10.0,
}

# =============================================================================
# UNDERGROUND CABLE CONFIGURATIONS (for Water Treeing Hidden Discovery)
# =============================================================================

CABLE_INSULATION_TYPES = {
    "XLPE": {"failure_rate": 0.02, "water_treeing_susceptible": True, "age_threshold": 15},
    "TR-XLPE": {"failure_rate": 0.01, "water_treeing_susceptible": False, "age_threshold": 25},
    "EPR": {"failure_rate": 0.015, "water_treeing_susceptible": False, "age_threshold": 30},
    "PILC": {"failure_rate": 0.03, "water_treeing_susceptible": False, "age_threshold": 40},
}


def generate_uuid() -> str:
    """Generate a short UUID for IDs."""
    return str(uuid.uuid4())[:8].upper()


def random_date_in_range(start_date: datetime, end_date: datetime) -> datetime:
    """Generate a random date between two dates."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


def get_fire_tier(region_config: dict) -> str:
    """Select fire tier based on region distribution."""
    distribution = region_config["fire_threat_distribution"]
    return np.random.choice(
        list(distribution.keys()),
        p=list(distribution.values())
    )


def get_species_for_region(region: str) -> str:
    """Get a random tree species appropriate for the region."""
    valid_species = [s for s, config in TREE_SPECIES.items() if region in config["regions"]]
    if not valid_species:
        valid_species = ["BRUSH"]  # Default
    return random.choice(valid_species)


def get_clearance_requirement(voltage_class: str, fire_tier: str) -> float:
    """Get required clearance based on voltage and fire tier."""
    return CLEARANCE_REQUIREMENTS.get((voltage_class, fire_tier), 4.0)


# =============================================================================
# LOCATION GENERATOR
# =============================================================================

def generate_locations_df() -> pd.DataFrame:
    """Generate location/zone data."""
    locations_data = []
    location_counter = 1
    
    for region_code, region_config in REGIONS.items():
        for loc in region_config["locations"]:
            location_id = f"LOC-{location_counter:04d}"
            location_counter += 1
            
            fire_tier = get_fire_tier(region_config)
            
            locations_data.append({
                "LOCATION_ID": location_id,
                "ZONE_NAME": loc["name"],
                "ZONE_TYPE": "SERVICE_TERRITORY",
                "FIRE_THREAT_TIER": fire_tier,
                "HFTD_FLAG": fire_tier in ["TIER_2", "TIER_3"],
                "STATE": {
                    "NORCAL": "CA", "SOCAL": "CA", "PNW": "OR",
                    "SOUTHWEST": "AZ", "MOUNTAIN": "CO"
                }.get(region_code, "CA"),
                "COUNTY": loc["name"].split()[0],
                "REGION": region_code,
                "CENTER_LATITUDE": loc["lat"],
                "CENTER_LONGITUDE": loc["lon"],
                "H3_INDEX": f"8a{random.randint(1000000, 9999999)}fffffff",
                "AREA_SQUARE_MILES": random.uniform(50, 200),
                "AVG_WIND_SPEED_MPH": random.uniform(5, 25),
                "AVG_ANNUAL_RAINFALL_IN": region_config["avg_rainfall_in"] * random.uniform(0.8, 1.2),
                "VEGETATION_DENSITY": loc["veg_density"],
                "TERRAIN_TYPE": loc["terrain"],
            })
    
    return pd.DataFrame(locations_data)


# =============================================================================
# CIRCUIT GENERATOR
# =============================================================================

def generate_circuits_df(locations_df: pd.DataFrame) -> pd.DataFrame:
    """Generate circuit/feeder data."""
    circuits_data = []
    circuit_counter = 1
    
    voltage_classes = ["4KV", "12KV", "21KV", "33KV", "69KV"]
    voltage_weights = [0.1, 0.5, 0.25, 0.1, 0.05]
    
    for _, loc in locations_df.iterrows():
        # Generate 3-6 circuits per location
        num_circuits = random.randint(3, 6)
        
        for i in range(num_circuits):
            circuit_id = f"CKT-{circuit_counter:05d}"
            circuit_counter += 1
            
            voltage_class = np.random.choice(voltage_classes, p=voltage_weights)
            total_miles = random.uniform(5, 30)
            overhead_pct = random.uniform(0.6, 0.95)
            
            # Last trim date in past 0-4 years
            last_trim = datetime.now() - timedelta(days=random.randint(0, 1460))
            trim_cycle = random.choice([2, 3, 4])  # Years
            next_trim = last_trim + timedelta(days=trim_cycle * 365)
            
            circuits_data.append({
                "CIRCUIT_ID": circuit_id,
                "CIRCUIT_NAME": f"{loc['ZONE_NAME']} Feeder {i+1}",
                "FEEDER_ID": f"FDR-{circuit_counter:05d}",
                "SUBSTATION_NAME": f"{loc['ZONE_NAME']} Substation",
                "SUBSTATION_ID": f"SUB-{loc['LOCATION_ID'][-4:]}",
                "DISTRICT": loc["ZONE_NAME"],
                "DIVISION": loc["REGION"],
                "VOLTAGE_CLASS": voltage_class,
                "CIRCUIT_TYPE": "DISTRIBUTION" if voltage_class in ["4KV", "12KV", "21KV"] else "SUBTRANSMISSION",
                "CONSTRUCTION_TYPE": "MIXED",
                "TOTAL_MILES": round(total_miles, 2),
                "OVERHEAD_MILES": round(total_miles * overhead_pct, 2),
                "UNDERGROUND_MILES": round(total_miles * (1 - overhead_pct), 2),
                "POLE_COUNT": int(total_miles * overhead_pct * random.uniform(15, 25)),
                "TRANSFORMER_COUNT": int(total_miles * random.uniform(3, 8)),
                "CUSTOMER_COUNT": int(total_miles * random.uniform(50, 200)),
                "LOCATION_ID": loc["LOCATION_ID"],
                "FIRE_THREAT_TIER": loc["FIRE_THREAT_TIER"],
                "PRIORITY_TIER": "P1" if loc["FIRE_THREAT_TIER"] == "TIER_3" else "P2" if loc["FIRE_THREAT_TIER"] == "TIER_2" else "P3",
                "SAIDI_MINUTES": random.uniform(30, 180),
                "SAIFI_COUNT": random.uniform(0.5, 2.5),
                "MAIFI_COUNT": random.uniform(2, 10),
                "LAST_PATROL_DATE": (datetime.now() - timedelta(days=random.randint(0, 90))).date(),
                "LAST_TRIM_DATE": last_trim.date(),
                "TRIM_CYCLE_YEARS": trim_cycle,
                "NEXT_SCHEDULED_TRIM": next_trim.date(),
            })
    
    return pd.DataFrame(circuits_data)


# =============================================================================
# ASSET GENERATOR
# =============================================================================

def generate_assets_df(circuits_df: pd.DataFrame, locations_df: pd.DataFrame) -> pd.DataFrame:
    """Generate 5,000 assets across all circuits."""
    assets_data = []
    asset_counter = 1
    
    # Calculate assets per circuit based on region targets
    total_target = 5000
    circuit_count = len(circuits_df)
    base_per_circuit = total_target // circuit_count
    
    asset_types = {
        "POLE": {"pct": 0.45, "subtypes": ["WOOD_POLE", "STEEL_POLE", "CONCRETE_POLE"]},
        "CONDUCTOR": {"pct": 0.30, "subtypes": ["ACSR", "AAC", "AAAC", "COVERED_CONDUCTOR"]},
        "TRANSFORMER": {"pct": 0.12, "subtypes": ["PADMOUNT", "POLE_MOUNT", "VAULT"]},
        "SWITCH": {"pct": 0.05, "subtypes": ["RECLOSER", "SECTIONALIZER", "FUSE"]},
        "CABLE_UNDERGROUND": {"pct": 0.08, "subtypes": ["PRIMARY_CABLE", "SECONDARY_CABLE"]},
    }
    
    for _, circuit in circuits_df.iterrows():
        location = locations_df[locations_df["LOCATION_ID"] == circuit["LOCATION_ID"]].iloc[0]
        
        # Vary assets per circuit
        num_assets = base_per_circuit + random.randint(-10, 20)
        
        for i in range(num_assets):
            asset_id = f"AST-{asset_counter:06d}"
            asset_counter += 1
            
            # Select asset type
            asset_type = np.random.choice(
                list(asset_types.keys()),
                p=[v["pct"] for v in asset_types.values()]
            )
            asset_config = asset_types[asset_type]
            asset_subtype = random.choice(asset_config["subtypes"])
            
            # Age distribution (older infrastructure)
            if asset_type == "CABLE_UNDERGROUND":
                # Underground cables: key for Water Treeing detection
                age = random.randint(5, 35)
                insulation_type = random.choice(list(CABLE_INSULATION_TYPES.keys()))
                moisture_exposure = random.choice(["LOW", "MEDIUM", "HIGH"])
                soil_type = random.choice(["SANDY", "CLAY", "LOAM", "ROCKY"])
            else:
                age = random.randint(3, 50)
                insulation_type = None
                moisture_exposure = None
                soil_type = None
            
            # Position with slight randomization around circuit location
            lat = location["CENTER_LATITUDE"] + random.uniform(-0.05, 0.05)
            lon = location["CENTER_LONGITUDE"] + random.uniform(-0.05, 0.05)
            
            # Condition and risk scores
            condition_score = max(1, min(5, int(5 - (age / 15) + random.uniform(-1, 1))))
            
            # Risk calculation
            base_risk = (age / 50) * 40  # Age contribution
            condition_risk = (5 - condition_score) * 10  # Condition contribution
            fire_tier_risk = {"TIER_3": 25, "TIER_2": 15, "TIER_1": 5, "NON_HFTD": 0}.get(location["FIRE_THREAT_TIER"], 0)
            composite_risk = min(100, base_risk + condition_risk + fire_tier_risk + random.uniform(-10, 10))
            
            assets_data.append({
                "ASSET_ID": asset_id,
                "ASSET_NAME": f"{asset_subtype.replace('_', ' ').title()} {asset_counter}",
                "ASSET_TYPE": asset_type,
                "ASSET_SUBTYPE": asset_subtype,
                "CIRCUIT_ID": circuit["CIRCUIT_ID"],
                "LOCATION_ID": circuit["LOCATION_ID"],
                "PARENT_ASSET_ID": None,
                "MANUFACTURER": random.choice(["ABB", "Siemens", "GE", "Eaton", "S&C", "Cooper"]),
                "MODEL": f"Model-{random.randint(100, 999)}",
                "INSTALL_DATE": (datetime.now() - timedelta(days=age * 365 + random.randint(0, 365))).date(),
                "EXPECTED_LIFE_YEARS": {"POLE": 45, "CONDUCTOR": 40, "TRANSFORMER": 35, "SWITCH": 30, "CABLE_UNDERGROUND": 40}.get(asset_type, 40),
                "AGE_YEARS": age,
                "VOLTAGE_CLASS": circuit["VOLTAGE_CLASS"],
                "PHASE": random.choice(["A", "B", "C", "ABC", "AB", "BC"]),
                "RATED_CAPACITY": random.uniform(100, 1000),
                "LATITUDE": round(lat, 6),
                "LONGITUDE": round(lon, 6),
                "ELEVATION_FT": random.uniform(100, 8000),
                "SPAN_LENGTH_FT": random.uniform(100, 400) if asset_type == "CONDUCTOR" else None,
                "HEIGHT_FT": random.uniform(35, 65) if asset_type == "POLE" else None,
                "DEPTH_FT": random.uniform(3, 6) if asset_type == "CABLE_UNDERGROUND" else None,
                "CONDITION_SCORE": condition_score,
                "LAST_INSPECTION_DATE": (datetime.now() - timedelta(days=random.randint(30, 365))).date(),
                "LAST_INSPECTION_TYPE": random.choice(["VISUAL", "INTRUSIVE", "DRONE", "LIDAR"]),
                "REPLACEMENT_PRIORITY": "IMMEDIATE" if composite_risk >= 80 else "HIGH" if composite_risk >= 60 else "MEDIUM" if composite_risk >= 40 else "LOW",
                "INSULATION_TYPE": insulation_type,
                "CABLE_JACKET": "PVC" if asset_type == "CABLE_UNDERGROUND" else None,
                "SOIL_TYPE": soil_type,
                "MOISTURE_EXPOSURE": moisture_exposure,
                "FAILURE_PROBABILITY": round(composite_risk / 200, 3),
                "IGNITION_RISK_SCORE": round(composite_risk * random.uniform(0.8, 1.2), 1) if location["FIRE_THREAT_TIER"] in ["TIER_2", "TIER_3"] else round(composite_risk * 0.5, 1),
                "COMPOSITE_RISK_SCORE": round(composite_risk, 1),
                "RISK_SCORE_DATE": datetime.now().date(),
                "STATUS": "IN_SERVICE",
                "OPERATIONAL_FLAG": True,
            })
    
    return pd.DataFrame(assets_data)


# =============================================================================
# VEGETATION ENCROACHMENT GENERATOR
# =============================================================================

def generate_vegetation_df(assets_df: pd.DataFrame, locations_df: pd.DataFrame, circuits_df: pd.DataFrame) -> pd.DataFrame:
    """Generate vegetation encroachment data for overhead assets."""
    vegetation_data = []
    veg_counter = 1
    
    # Only overhead assets have vegetation issues
    overhead_assets = assets_df[assets_df["ASSET_TYPE"].isin(["POLE", "CONDUCTOR"])]
    
    for _, asset in overhead_assets.iterrows():
        # 70% of overhead assets have vegetation nearby
        if random.random() > 0.70:
            continue
            
        veg_id = f"VEG-{veg_counter:06d}"
        veg_counter += 1
        
        location = locations_df[locations_df["LOCATION_ID"] == asset["LOCATION_ID"]].iloc[0]
        circuit = circuits_df[circuits_df["CIRCUIT_ID"] == asset["CIRCUIT_ID"]].iloc[0]
        
        # Get species appropriate for region
        species = get_species_for_region(location["REGION"])
        species_config = TREE_SPECIES[species]
        
        # Get required clearance
        required_clearance = get_clearance_requirement(
            asset["VOLTAGE_CLASS"], 
            location["FIRE_THREAT_TIER"]
        )
        
        # Current distance - vary based on when last trimmed
        days_since_trim = (datetime.now().date() - circuit["LAST_TRIM_DATE"]).days
        growth_since_trim = (species_config["growth_rate_ft"] / 365) * days_since_trim
        
        # Base clearance after trim, then subtract growth
        post_trim_clearance = required_clearance + random.uniform(2, 8)
        current_distance = max(0.5, post_trim_clearance - growth_since_trim + random.uniform(-2, 2))
        
        # Determine clearance status
        if current_distance < required_clearance * 0.5:
            clearance_status = "CRITICAL"
        elif current_distance < required_clearance:
            clearance_status = "VIOLATION"
        elif current_distance < required_clearance * 1.5:
            clearance_status = "MARGINAL"
        else:
            clearance_status = "COMPLIANT"
        
        # Predict future encroachment
        growth_30d = (species_config["growth_rate_ft"] / 365) * 30
        growth_90d = (species_config["growth_rate_ft"] / 365) * 90
        
        predicted_30d = max(0, current_distance - growth_30d)
        predicted_90d = max(0, current_distance - growth_90d)
        
        # Days to critical
        if current_distance <= required_clearance * 0.5:
            days_to_critical = 0
        else:
            distance_to_critical = current_distance - (required_clearance * 0.5)
            daily_growth = species_config["growth_rate_ft"] / 365
            days_to_critical = int(distance_to_critical / daily_growth) if daily_growth > 0 else 999
        
        vegetation_data.append({
            "ENCROACHMENT_ID": veg_id,
            "ASSET_ID": asset["ASSET_ID"],
            "MEASUREMENT_DATE": datetime.now().date(),
            "MEASUREMENT_SOURCE": random.choice(["LIDAR", "DRONE", "FIELD_INSPECTION"]),
            "TREE_SPECIES": species,
            "TREE_HEIGHT_FT": random.uniform(20, 80),
            "TREE_CANOPY_DIAMETER_FT": random.uniform(10, 40),
            "TREE_HEALTH": random.choice(["HEALTHY", "HEALTHY", "HEALTHY", "STRESSED", "DEAD"]),
            "DISTANCE_TO_CONDUCTOR_FT": round(current_distance, 2),
            "HORIZONTAL_CLEARANCE_FT": round(current_distance * random.uniform(0.8, 1.0), 2),
            "VERTICAL_CLEARANCE_FT": round(current_distance * random.uniform(0.9, 1.1), 2),
            "GROWTH_RATE_ANNUAL_FT": species_config["growth_rate_ft"],
            "GROWTH_RATE_CATEGORY": species_config["category"],
            "PREDICTED_ENCROACHMENT_30D_FT": round(growth_30d, 2),
            "PREDICTED_ENCROACHMENT_90D_FT": round(growth_90d, 2),
            "DAYS_TO_CRITICAL": days_to_critical,
            "REQUIRED_CLEARANCE_FT": required_clearance,
            "CLEARANCE_STATUS": clearance_status,
            "IN_VIOLATION": clearance_status in ["VIOLATION", "CRITICAL"],
            "STRIKE_POTENTIAL": "HIGH" if current_distance < 4 else "MEDIUM" if current_distance < 8 else "LOW",
            "FALL_IN_POTENTIAL": random.random() < 0.2,
            "BLOW_IN_POTENTIAL": random.random() < 0.3,
        })
    
    return pd.DataFrame(vegetation_data)


# =============================================================================
# AMI READING GENERATOR - THE HIDDEN DISCOVERY (Water Treeing)
# =============================================================================

def generate_ami_readings_df(assets_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate AMI (smart meter) readings for underground cables.
    
    THE HIDDEN DISCOVERY: Water Treeing Detection
    - Cables with XLPE insulation, age 15-25 years, high moisture exposure
    - Show voltage dips (2-5%) correlated with rainfall events
    - Pattern: voltage_dip_flag = TRUE when rainfall_mm > 10
    """
    ami_data = []
    reading_counter = 1
    
    # Get underground cables
    ug_cables = assets_df[assets_df["ASSET_TYPE"] == "CABLE_UNDERGROUND"]
    
    # Identify "problem cables" - THE HIDDEN DISCOVERY PATTERN
    problem_cables = ug_cables[
        (ug_cables["INSULATION_TYPE"] == "XLPE") &
        (ug_cables["AGE_YEARS"] >= 15) &
        (ug_cables["AGE_YEARS"] <= 25) &
        (ug_cables["MOISTURE_EXPOSURE"].isin(["MEDIUM", "HIGH"]))
    ]["ASSET_ID"].tolist()
    
    # Generate 90 days of readings
    for _, cable in ug_cables.iterrows():
        is_problem_cable = cable["ASSET_ID"] in problem_cables
        
        for day_offset in range(90):
            reading_date = datetime.now() - timedelta(days=day_offset)
            
            # Simulate weather
            is_rainy = random.random() < 0.25  # 25% chance of rain
            rainfall_mm = random.uniform(10, 50) if is_rainy else 0
            soil_moisture = 30 + (rainfall_mm * 0.5) + random.uniform(-5, 5)
            
            # Base voltage
            nominal_voltage = 120.0
            base_voltage = nominal_voltage * random.uniform(0.98, 1.02)
            
            # THE WATER TREEING PATTERN
            if is_problem_cable and is_rainy and rainfall_mm > 10:
                # Problem cables show voltage dips during rain
                voltage_dip_pct = random.uniform(2.0, 5.0)
                voltage = base_voltage * (1 - voltage_dip_pct / 100)
                voltage_dip_flag = True
                rain_correlated_dip = True
            elif is_problem_cable and random.random() < 0.1:
                # Occasional dips even without rain (early stage)
                voltage_dip_pct = random.uniform(1.0, 2.5)
                voltage = base_voltage * (1 - voltage_dip_pct / 100)
                voltage_dip_flag = True
                rain_correlated_dip = False
            else:
                # Normal operation
                voltage = base_voltage
                voltage_dip_pct = 0
                voltage_dip_flag = False
                rain_correlated_dip = False
            
            reading_id = f"AMI-{reading_counter:08d}"
            reading_counter += 1
            
            ami_data.append({
                "READING_ID": reading_id,
                "ASSET_ID": cable["ASSET_ID"],
                "READING_TIMESTAMP": reading_date,
                "VOLTAGE_A": round(voltage * random.uniform(0.99, 1.01), 2),
                "VOLTAGE_B": round(voltage * random.uniform(0.99, 1.01), 2),
                "VOLTAGE_C": round(voltage * random.uniform(0.99, 1.01), 2),
                "VOLTAGE_AVG": round(voltage, 2),
                "VOLTAGE_NOMINAL": nominal_voltage,
                "VOLTAGE_DIP_PCT": round(voltage_dip_pct, 2),
                "VOLTAGE_DIP_FLAG": voltage_dip_flag,
                "DIP_DURATION_SECONDS": random.randint(100, 500) if voltage_dip_flag else 0,
                "RAINFALL_MM": round(rainfall_mm, 1),
                "SOIL_MOISTURE_PCT": round(soil_moisture, 1),
                "TEMPERATURE_F": random.uniform(40, 90),
                "RAIN_CORRELATED_DIP": rain_correlated_dip,
                "CONSECUTIVE_DIP_COUNT": 0,  # Would be calculated in production
                "CURRENT_A": round(random.uniform(50, 200), 2),
                "CURRENT_B": round(random.uniform(50, 200), 2),
                "CURRENT_C": round(random.uniform(50, 200), 2),
                "POWER_KW": round(random.uniform(100, 500), 2),
                "POWER_FACTOR": round(random.uniform(0.85, 0.98), 2),
                "READING_QUALITY": "VALID",
            })
    
    return pd.DataFrame(ami_data)


# =============================================================================
# WORK ORDER GENERATOR
# =============================================================================

def generate_work_orders_df(assets_df: pd.DataFrame, vegetation_df: pd.DataFrame) -> pd.DataFrame:
    """Generate historical and open work orders."""
    work_orders = []
    wo_counter = 1
    
    # Historical completed work orders (past 2 years)
    for i in range(300):
        wo_id = f"WO-{wo_counter:06d}"
        wo_counter += 1
        
        asset = assets_df.sample(1).iloc[0]
        
        activity_type = random.choice(["TRIM", "TRIM", "TRIM", "INSPECT", "REPAIR", "REPLACE"])
        completion_date = datetime.now() - timedelta(days=random.randint(30, 730))
        
        work_orders.append({
            "WORK_ORDER_ID": wo_id,
            "WORK_ORDER_NUMBER": f"WO-{datetime.now().year}-{wo_counter:05d}",
            "ASSET_ID": asset["ASSET_ID"],
            "CIRCUIT_ID": asset["CIRCUIT_ID"],
            "LOCATION_ID": asset["LOCATION_ID"],
            "ACTIVITY_TYPE": activity_type,
            "WORK_TYPE": random.choice(["ROUTINE", "CORRECTIVE", "PREVENTIVE"]),
            "PRIORITY": random.choice(["HIGH", "MEDIUM", "LOW"]),
            "DESCRIPTION": f"{activity_type} work on {asset['ASSET_TYPE']}",
            "SCOPE_NOTES": f"Standard {activity_type.lower()} procedure",
            "ESTIMATED_HOURS": random.uniform(2, 16),
            "ESTIMATED_COST": random.uniform(500, 5000),
            "TREES_TO_TRIM": random.randint(5, 50) if activity_type == "TRIM" else None,
            "ESTIMATED_MILES": random.uniform(0.5, 5) if activity_type == "TRIM" else None,
            "SPECIES_TARGET": None,
            "REQUESTED_DATE": (completion_date - timedelta(days=random.randint(7, 30))).date(),
            "SCHEDULED_DATE": (completion_date - timedelta(days=random.randint(1, 7))).date(),
            "DUE_DATE": completion_date.date(),
            "COMPLETION_DATE": completion_date.date(),
            "STATUS": "COMPLETED",
            "ACTUAL_HOURS": random.uniform(2, 20),
            "ACTUAL_COST": random.uniform(500, 6000),
            "MILES_TRIMMED": random.uniform(0.5, 5) if activity_type == "TRIM" else None,
            "TREES_TRIMMED": random.randint(5, 60) if activity_type == "TRIM" else None,
            "ASSIGNED_CREW": f"Crew-{random.randint(1, 20)}",
            "CONTRACTOR": random.choice(["Davey Tree", "Asplundh", "Wright Tree Service", "Internal Crew"]),
            "PRE_WORK_RISK_SCORE": random.uniform(40, 80),
            "POST_WORK_RISK_SCORE": random.uniform(20, 50),
            "RISK_REDUCTION_VALUE": random.uniform(10, 40),
            "CREATED_BY": "system",
            "CREATED_SOURCE": "PATROL",
        })
    
    # Open work orders (based on vegetation violations)
    violations = vegetation_df[vegetation_df["CLEARANCE_STATUS"].isin(["VIOLATION", "CRITICAL"])]
    
    for _, veg in violations.head(100).iterrows():
        wo_id = f"WO-{wo_counter:06d}"
        wo_counter += 1
        
        asset = assets_df[assets_df["ASSET_ID"] == veg["ASSET_ID"]].iloc[0]
        
        priority = "EMERGENCY" if veg["CLEARANCE_STATUS"] == "CRITICAL" else "URGENT"
        status = random.choice(["SUBMITTED", "APPROVED", "SCHEDULED", "IN_PROGRESS"])
        
        work_orders.append({
            "WORK_ORDER_ID": wo_id,
            "WORK_ORDER_NUMBER": f"WO-{datetime.now().year}-{wo_counter:05d}",
            "ASSET_ID": asset["ASSET_ID"],
            "CIRCUIT_ID": asset["CIRCUIT_ID"],
            "LOCATION_ID": asset["LOCATION_ID"],
            "ACTIVITY_TYPE": "TRIM",
            "WORK_TYPE": "CORRECTIVE",
            "PRIORITY": priority,
            "DESCRIPTION": f"Vegetation clearance - {veg['TREE_SPECIES']} at {veg['DISTANCE_TO_CONDUCTOR_FT']:.1f}ft",
            "SCOPE_NOTES": f"Required clearance: {veg['REQUIRED_CLEARANCE_FT']}ft. Current: {veg['DISTANCE_TO_CONDUCTOR_FT']:.1f}ft",
            "ESTIMATED_HOURS": random.uniform(2, 8),
            "ESTIMATED_COST": random.uniform(500, 2000),
            "TREES_TO_TRIM": random.randint(1, 10),
            "ESTIMATED_MILES": None,
            "SPECIES_TARGET": veg["TREE_SPECIES"],
            "REQUESTED_DATE": datetime.now().date(),
            "SCHEDULED_DATE": (datetime.now() + timedelta(days=random.randint(1, 14))).date() if status in ["SCHEDULED", "IN_PROGRESS"] else None,
            "DUE_DATE": (datetime.now() + timedelta(days=7 if priority == "EMERGENCY" else 14)).date(),
            "COMPLETION_DATE": None,
            "STATUS": status,
            "ACTUAL_HOURS": None,
            "ACTUAL_COST": None,
            "MILES_TRIMMED": None,
            "TREES_TRIMMED": None,
            "ASSIGNED_CREW": f"Crew-{random.randint(1, 20)}" if status in ["SCHEDULED", "IN_PROGRESS"] else None,
            "CONTRACTOR": random.choice(["Davey Tree", "Asplundh", "Wright Tree Service"]),
            "PRE_WORK_RISK_SCORE": asset["COMPOSITE_RISK_SCORE"],
            "POST_WORK_RISK_SCORE": None,
            "RISK_REDUCTION_VALUE": None,
            "CREATED_BY": "VIGIL_AI",
            "CREATED_SOURCE": "VIGIL_AI",
        })
    
    return pd.DataFrame(work_orders)


# =============================================================================
# WEATHER FORECAST GENERATOR
# =============================================================================

def generate_weather_df(locations_df: pd.DataFrame) -> pd.DataFrame:
    """Generate 14-day weather forecasts per location."""
    weather_data = []
    forecast_counter = 1
    
    for _, location in locations_df.iterrows():
        region = location["REGION"]
        base_temp = {"NORCAL": 70, "SOCAL": 80, "PNW": 60, "SOUTHWEST": 95, "MOUNTAIN": 65}.get(region, 70)
        
        for day_offset in range(14):
            forecast_date = datetime.now().date() + timedelta(days=day_offset)
            
            # Fire weather conditions more likely in certain regions
            fire_weather_prob = {"NORCAL": 0.15, "SOCAL": 0.20, "PNW": 0.05, "SOUTHWEST": 0.10, "MOUNTAIN": 0.10}.get(region, 0.1)
            is_fire_weather = random.random() < fire_weather_prob
            
            wind_speed = random.uniform(25, 60) if is_fire_weather else random.uniform(5, 20)
            humidity = random.uniform(5, 20) if is_fire_weather else random.uniform(30, 70)
            
            forecast_id = f"WX-{forecast_counter:06d}"
            forecast_counter += 1
            
            weather_data.append({
                "FORECAST_ID": forecast_id,
                "LOCATION_ID": location["LOCATION_ID"],
                "FORECAST_DATE": forecast_date,
                "FORECAST_HOUR": 12,
                "SOURCE": "NWS",
                "ISSUED_AT": datetime.now(),
                "TEMPERATURE_F": base_temp + random.uniform(-10, 10),
                "TEMPERATURE_MAX_F": base_temp + random.uniform(5, 15),
                "TEMPERATURE_MIN_F": base_temp + random.uniform(-15, -5),
                "WIND_SPEED_MPH": round(wind_speed, 1),
                "WIND_GUST_MPH": round(wind_speed * random.uniform(1.3, 1.8), 1),
                "WIND_DIRECTION": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
                "HUMIDITY_PCT": round(humidity, 1),
                "PRECIPITATION_PROBABILITY": 0.05 if is_fire_weather else random.uniform(0, 0.4),
                "PRECIPITATION_AMOUNT_IN": 0 if is_fire_weather else random.uniform(0, 0.5),
                "PRECIPITATION_TYPE": "NONE" if is_fire_weather else random.choice(["NONE", "NONE", "RAIN"]),
                "RED_FLAG_WARNING": is_fire_weather and wind_speed > 40,
                "FIRE_WEATHER_WATCH": is_fire_weather and wind_speed > 30,
                "WIND_ADVISORY": wind_speed > 35,
                "FIRE_WEATHER_INDEX": round(wind_speed * (100 - humidity) / 100, 1),
                "PSPS_PROBABILITY": round(min(1.0, wind_speed / 60 * (100 - humidity) / 100), 2) if is_fire_weather else 0,
            })
    
    return pd.DataFrame(weather_data)


# =============================================================================
# RISK ASSESSMENT GENERATOR
# =============================================================================

def generate_risk_assessments_df(assets_df: pd.DataFrame) -> pd.DataFrame:
    """Generate ML risk assessments for all assets."""
    assessments = []
    assessment_counter = 1
    
    for _, asset in assets_df.iterrows():
        assessment_id = f"RA-{assessment_counter:06d}"
        assessment_counter += 1
        
        # Get composite risk from asset
        composite_risk = asset["COMPOSITE_RISK_SCORE"]
        
        # Determine risk tier
        if composite_risk >= 80:
            risk_tier = "CRITICAL"
            action = "REPLACE"
            priority = "IMMEDIATE"
        elif composite_risk >= 60:
            risk_tier = "HIGH"
            action = "REPAIR" if asset["CONDITION_SCORE"] <= 2 else "INSPECT"
            priority = "HIGH"
        elif composite_risk >= 40:
            risk_tier = "MEDIUM"
            action = "INSPECT"
            priority = "MEDIUM"
        else:
            risk_tier = "LOW"
            action = "MONITOR"
            priority = "LOW"
        
        assessments.append({
            "ASSESSMENT_ID": assessment_id,
            "ASSET_ID": asset["ASSET_ID"],
            "ASSESSMENT_DATE": datetime.now().date(),
            "COMPOSITE_RISK_SCORE": composite_risk,
            "RISK_TIER": risk_tier,
            "RISK_RANK": assessment_counter,
            "FAILURE_PROBABILITY": asset["FAILURE_PROBABILITY"],
            "IGNITION_RISK": asset["IGNITION_RISK_SCORE"],
            "OUTAGE_IMPACT_SCORE": random.uniform(20, 80),
            "SAFETY_RISK_SCORE": composite_risk * random.uniform(0.8, 1.2),
            "AGE_FACTOR": asset["AGE_YEARS"] / 50,
            "CONDITION_FACTOR": (5 - asset["CONDITION_SCORE"]) / 4,
            "VEGETATION_FACTOR": random.uniform(0, 0.5),
            "WEATHER_FACTOR": random.uniform(0, 0.3),
            "LOAD_FACTOR": random.uniform(0.1, 0.4),
            "HISTORICAL_FACTOR": random.uniform(0, 0.3),
            "MODEL_VERSION": "v1.0.0",
            "MODEL_CONFIDENCE": random.uniform(0.75, 0.95),
            "RECOMMENDED_ACTION": action,
            "RECOMMENDED_PRIORITY": priority,
            "ESTIMATED_RISK_REDUCTION": random.uniform(10, 40),
        })
    
    return pd.DataFrame(assessments)


# =============================================================================
# CABLE FAILURE PREDICTION GENERATOR (Hidden Discovery)
# =============================================================================

def generate_cable_failure_predictions_df(assets_df: pd.DataFrame, ami_df: pd.DataFrame) -> pd.DataFrame:
    """Generate cable failure predictions with Water Treeing detection."""
    predictions = []
    pred_counter = 1
    
    ug_cables = assets_df[assets_df["ASSET_TYPE"] == "CABLE_UNDERGROUND"]
    
    for _, cable in ug_cables.iterrows():
        pred_id = f"CFP-{pred_counter:06d}"
        pred_counter += 1
        
        # Get AMI readings for this cable
        cable_ami = ami_df[ami_df["ASSET_ID"] == cable["ASSET_ID"]]
        
        # Calculate Water Treeing metrics
        total_readings = len(cable_ami)
        dip_count = cable_ami["VOLTAGE_DIP_FLAG"].sum()
        rain_correlated_dips = cable_ami["RAIN_CORRELATED_DIP"].sum()
        rain_events = (cable_ami["RAINFALL_MM"] > 10).sum()
        
        # Water Treeing probability based on correlation
        if rain_events > 0:
            rain_correlation = rain_correlated_dips / rain_events
        else:
            rain_correlation = 0
        
        # Severity determination
        is_susceptible = (
            cable["INSULATION_TYPE"] == "XLPE" and
            cable["AGE_YEARS"] >= 15 and
            cable["MOISTURE_EXPOSURE"] in ["MEDIUM", "HIGH"]
        )
        
        if is_susceptible and rain_correlation > 0.6:
            water_treeing_prob = rain_correlation * 0.95
            severity = "SEVERE" if water_treeing_prob > 0.8 else "MODERATE"
            action = "REPLACE"
            urgency = "URGENT" if severity == "SEVERE" else "HIGH"
        elif is_susceptible and rain_correlation > 0.3:
            water_treeing_prob = rain_correlation * 0.7
            severity = "EARLY"
            action = "MONITOR"
            urgency = "MEDIUM"
        else:
            water_treeing_prob = rain_correlation * 0.2
            severity = "NONE"
            action = "NO_ACTION"
            urgency = "LOW"
        
        predictions.append({
            "PREDICTION_ID": pred_id,
            "ASSET_ID": cable["ASSET_ID"],
            "PREDICTION_DATE": datetime.now().date(),
            "MODEL_ID": "CABLE_FAILURE_V1",
            "WATER_TREEING_PROBABILITY": round(water_treeing_prob, 3),
            "WATER_TREEING_SEVERITY": severity,
            "FAILURE_PROBABILITY_30D": round(water_treeing_prob * 0.1, 3),
            "FAILURE_PROBABILITY_90D": round(water_treeing_prob * 0.25, 3),
            "FAILURE_PROBABILITY_1Y": round(water_treeing_prob * 0.5, 3),
            "VOLTAGE_DIP_FREQUENCY": round(dip_count / max(total_readings, 1), 3),
            "RAIN_CORRELATION_SCORE": round(rain_correlation, 3),
            "ANOMALY_SCORE": round(water_treeing_prob * 100, 1),
            "DIP_EVENTS_LAST_30D": int(cable_ami[cable_ami["READING_TIMESTAMP"] >= datetime.now() - timedelta(days=30)]["VOLTAGE_DIP_FLAG"].sum()),
            "DIP_EVENTS_LAST_90D": int(dip_count),
            "AVG_DIP_MAGNITUDE_PCT": round(cable_ami[cable_ami["VOLTAGE_DIP_FLAG"]]["VOLTAGE_DIP_PCT"].mean() if dip_count > 0 else 0, 2),
            "RAIN_EVENTS_WITH_DIPS": int(rain_correlated_dips),
            "RAIN_EVENTS_WITHOUT_DIPS": int(rain_events - rain_correlated_dips),
            "CABLE_AGE_YEARS": cable["AGE_YEARS"],
            "INSULATION_TYPE": cable["INSULATION_TYPE"],
            "MOISTURE_EXPOSURE": cable["MOISTURE_EXPOSURE"],
            "PROACTIVE_REPLACEMENT_COST": 10000,
            "EMERGENCY_REPAIR_COST": 100000,
            "REGULATORY_FINE_RISK": 50000 if severity == "SEVERE" else 10000 if severity == "MODERATE" else 0,
            "RECOMMENDED_ACTION": action,
            "ACTION_URGENCY": urgency,
            "PREDICTION_CONFIDENCE": random.uniform(0.80, 0.95),
            "TOP_ANOMALY_INDICATOR": "RAIN_CORRELATED_VOLTAGE_DIP" if rain_correlation > 0.3 else "AGE_FACTOR",
            "DETECTION_METHOD": "RAIN_CORRELATION" if rain_correlation > 0.3 else "COMBINED",
        })
    
    return pd.DataFrame(predictions)


# =============================================================================
# COMPLIANCE DOCUMENTS (CPUC GO95)
# =============================================================================

def generate_compliance_docs_df() -> pd.DataFrame:
    """Generate CPUC GO95 compliance documents for Cortex Search."""
    docs = [
        {
            "DOCUMENT_ID": "GO95-R37",
            "DOCUMENT_TYPE": "REGULATION",
            "REGULATION_CODE": "GO95",
            "TITLE": "Rule 37 - Vegetation Management",
            "SECTION": "Rule 37",
            "SUBSECTION": "37.1",
            "CONTENT": """RULE 37. VEGETATION MANAGEMENT
            
37.1 General Requirements
Utilities shall maintain adequate clearance between conductors and vegetation to prevent contact during normal conditions and under design wind conditions.

37.2 Minimum Clearances in High Fire Threat Districts (HFTD)
For Tier 2 and Tier 3 High Fire Threat Districts:
- At time of trim: 12 feet minimum radial clearance for all voltages up to 72kV
- At time of inspection: 4 feet minimum for voltages below 72kV

37.3 Clearance Requirements by Voltage
For conductors operating at:
- 750V to 22.5kV: Minimum radial clearance of 4 feet (non-HFTD) or 12 feet (Tier 2/3 HFTD)
- 22.5kV to 72kV: Minimum radial clearance of 6 feet (non-HFTD) or 12 feet (Tier 2/3 HFTD)
- Greater than 72kV: Minimum radial clearance of 10 feet (non-HFTD) or 18 feet (Tier 2/3 HFTD)""",
            "ASSET_TYPE": "CONDUCTOR",
            "VOLTAGE_CLASS": "ALL",
            "FIRE_TIER": "ALL",
            "MIN_CLEARANCE_FT": 4.0,
            "RADIAL_CLEARANCE_FT": 12.0,
            "EFFECTIVE_DATE": datetime(2020, 1, 1).date(),
            "LAST_UPDATED": datetime(2023, 6, 1).date(),
            "SOURCE_URL": "https://www.cpuc.ca.gov/go95",
        },
        {
            "DOCUMENT_ID": "GO95-T1",
            "DOCUMENT_TYPE": "REGULATION",
            "REGULATION_CODE": "GO95",
            "TITLE": "Table 1 - Minimum Clearances of Wires Above Ground",
            "SECTION": "Table 1",
            "SUBSECTION": "Case 14",
            "CONTENT": """TABLE 1. MINIMUM CLEARANCES OF WIRES ABOVE GROUND, RAILS OR WATER

Case 14 - Conductors along and within the limits of highways and other thoroughfares

For supply conductors at voltages:
- 0-750V: 18 feet minimum vertical clearance
- 750V-22.5kV: 25 feet minimum vertical clearance  
- 22.5kV-72kV: 27 feet minimum vertical clearance
- Greater than 72kV: 30 feet minimum vertical clearance

These clearances apply to conductors crossing or within 10 feet of a highway, road, or street.""",
            "ASSET_TYPE": "CONDUCTOR",
            "VOLTAGE_CLASS": "12KV",
            "FIRE_TIER": "ALL",
            "MIN_CLEARANCE_FT": 25.0,
            "RADIAL_CLEARANCE_FT": None,
            "EFFECTIVE_DATE": datetime(2020, 1, 1).date(),
            "LAST_UPDATED": datetime(2023, 6, 1).date(),
            "SOURCE_URL": "https://www.cpuc.ca.gov/go95",
        },
        {
            "DOCUMENT_ID": "GO95-R35",
            "DOCUMENT_TYPE": "REGULATION",
            "REGULATION_CODE": "GO95",
            "TITLE": "Rule 35 - Clearance of Conductors from Buildings",
            "SECTION": "Rule 35",
            "SUBSECTION": "35.1",
            "CONTENT": """RULE 35. CLEARANCE OF CONDUCTORS FROM BUILDINGS AND OTHER INSTALLATIONS

35.1 Horizontal Clearance
Supply conductors shall have a horizontal clearance from buildings and structures of not less than:
- For voltages below 750V: 3 feet
- For 750V to 22.5kV: 6 feet
- For 22.5kV to 72kV: 8 feet
- For greater than 72kV: 10 feet plus 0.4 inches per kV above 72kV

35.2 Vertical Clearance
Supply conductors passing over buildings shall have a vertical clearance above the roof of not less than:
- For voltages below 750V: 8 feet
- For 750V to 22.5kV: 12 feet
- For 22.5kV to 72kV: 15 feet""",
            "ASSET_TYPE": "CONDUCTOR",
            "VOLTAGE_CLASS": "ALL",
            "FIRE_TIER": "ALL",
            "MIN_CLEARANCE_FT": 6.0,
            "RADIAL_CLEARANCE_FT": None,
            "EFFECTIVE_DATE": datetime(2020, 1, 1).date(),
            "LAST_UPDATED": datetime(2023, 6, 1).date(),
            "SOURCE_URL": "https://www.cpuc.ca.gov/go95",
        },
        {
            "DOCUMENT_ID": "VMS-001",
            "DOCUMENT_TYPE": "STANDARD",
            "REGULATION_CODE": "VEG_MGMT",
            "TITLE": "Vegetation Management Standards - Species Growth Rates",
            "SECTION": "Growth Rates",
            "SUBSECTION": "3.1",
            "CONTENT": """VEGETATION MANAGEMENT STANDARDS - SPECIES GROWTH RATES

3.1 Fast-Growing Species (>4 feet per year)
Species requiring enhanced trim cycles:
- Eucalyptus: 6 feet/year average growth
- Cottonwood: 5 feet/year average growth
- Brush/Chaparral: 4 feet/year average growth

Recommended trim cycle: Annual in HFTD areas

3.2 Medium-Growing Species (2-4 feet per year)
- Monterey Pine: 3 feet/year average growth
- Douglas Fir: 2.5 feet/year average growth
- Coast Live Oak: 2 feet/year average growth

Recommended trim cycle: 2 years in HFTD, 3 years in non-HFTD

3.3 Slow-Growing Species (<2 feet per year)
- Juniper: 0.5 feet/year average growth
- Palm: 1.5 feet/year average growth

Recommended trim cycle: 3-4 years""",
            "ASSET_TYPE": "CONDUCTOR",
            "VOLTAGE_CLASS": "ALL",
            "FIRE_TIER": "ALL",
            "MIN_CLEARANCE_FT": None,
            "RADIAL_CLEARANCE_FT": None,
            "EFFECTIVE_DATE": datetime(2021, 1, 1).date(),
            "LAST_UPDATED": datetime(2024, 1, 1).date(),
            "SOURCE_URL": None,
        },
        {
            "DOCUMENT_ID": "GO95-HFTD",
            "DOCUMENT_TYPE": "REGULATION",
            "REGULATION_CODE": "GO95",
            "TITLE": "High Fire Threat District (HFTD) Classification",
            "SECTION": "Fire Safety",
            "SUBSECTION": "FS.1",
            "CONTENT": """HIGH FIRE THREAT DISTRICT (HFTD) CLASSIFICATION

Tier 3 - Extreme Fire Threat
Areas where there is an extreme risk of wildfire ignition from utility infrastructure and where the wildfire would likely spread rapidly. Enhanced clearances and inspection requirements apply.
Required radial clearance: 12 feet minimum for all voltages up to 72kV

Tier 2 - Elevated Fire Threat  
Areas where there is an elevated risk of wildfire ignition from utility infrastructure. Standard HFTD requirements apply.
Required radial clearance: 6-12 feet depending on voltage

Tier 1 - Moderate Fire Threat
Areas with moderate fire risk. Standard clearance requirements apply with enhanced patrol frequency.
Required radial clearance: Per standard Table 1 requirements

Non-HFTD Areas
Areas outside designated fire threat districts. Standard GO95 clearances apply.
Required radial clearance: Per Table 1 minimums (typically 4 feet for distribution)""",
            "ASSET_TYPE": "ALL",
            "VOLTAGE_CLASS": "ALL",
            "FIRE_TIER": "ALL",
            "MIN_CLEARANCE_FT": 4.0,
            "RADIAL_CLEARANCE_FT": 12.0,
            "EFFECTIVE_DATE": datetime(2018, 1, 1).date(),
            "LAST_UPDATED": datetime(2024, 1, 1).date(),
            "SOURCE_URL": "https://www.cpuc.ca.gov/hftd",
        },
    ]
    
    return pd.DataFrame(docs)


# =============================================================================
# MONTHLY SNAPSHOT GENERATOR
# =============================================================================

def generate_monthly_snapshots_df(circuits_df: pd.DataFrame, assets_df: pd.DataFrame, vegetation_df: pd.DataFrame) -> pd.DataFrame:
    """Generate monthly snapshots for trending."""
    snapshots = []
    snapshot_counter = 1
    
    for _, circuit in circuits_df.iterrows():
        circuit_assets = assets_df[assets_df["CIRCUIT_ID"] == circuit["CIRCUIT_ID"]]
        circuit_veg = vegetation_df[vegetation_df["ASSET_ID"].isin(circuit_assets["ASSET_ID"])]
        
        # Generate 12 months of history
        for month_offset in range(12):
            snapshot_date = (datetime.now() - timedelta(days=month_offset * 30)).date()
            
            snapshot_id = f"SNAP-{snapshot_counter:06d}"
            snapshot_counter += 1
            
            # Calculate dynamic fire season days
            region = circuit["DIVISION"]
            region_config = REGIONS.get(region, REGIONS["NORCAL"])
            fire_start = datetime(
                datetime.now().year,
                region_config["fire_season_start_month"],
                region_config["fire_season_start_day"]
            ).date()
            days_to_fire = (fire_start - snapshot_date).days
            
            snapshots.append({
                "SNAPSHOT_ID": snapshot_id,
                "CIRCUIT_ID": circuit["CIRCUIT_ID"],
                "SNAPSHOT_DATE": snapshot_date,
                "HIGH_RISK_ASSET_COUNT": int((circuit_assets["COMPOSITE_RISK_SCORE"] >= 60).sum() * random.uniform(0.8, 1.2)),
                "CRITICAL_RISK_ASSET_COUNT": int((circuit_assets["COMPOSITE_RISK_SCORE"] >= 80).sum() * random.uniform(0.8, 1.2)),
                "AVG_RISK_SCORE": round(circuit_assets["COMPOSITE_RISK_SCORE"].mean() * random.uniform(0.9, 1.1), 1),
                "MAX_RISK_SCORE": round(circuit_assets["COMPOSITE_RISK_SCORE"].max(), 1),
                "TOTAL_SPANS": len(circuit_veg),
                "SPANS_REQUIRING_TRIM": int((circuit_veg["CLEARANCE_STATUS"].isin(["VIOLATION", "CRITICAL", "MARGINAL"])).sum() * random.uniform(0.7, 1.3)),
                "SPANS_IN_VIOLATION": int((circuit_veg["CLEARANCE_STATUS"] == "VIOLATION").sum() * random.uniform(0.7, 1.3)),
                "MILES_TRIMMED_MTD": round(random.uniform(0.5, 3), 2),
                "MILES_TRIMMED_YTD": round(random.uniform(5, 20), 2),
                "OPEN_WORK_ORDERS": random.randint(2, 15),
                "COMPLETED_WORK_ORDERS_MTD": random.randint(1, 10),
                "BACKLOG_DAYS": random.uniform(5, 30),
                "BUDGET_ALLOCATED": random.uniform(50000, 200000),
                "BUDGET_SPENT_MTD": random.uniform(10000, 50000),
                "BUDGET_SPENT_YTD": random.uniform(100000, 500000),
                "COST_PER_MILE": random.uniform(5000, 15000),
                "RISK_REDUCTION_VALUE_MTD": random.uniform(5, 25),
                "RISK_REDUCTION_VALUE_YTD": random.uniform(50, 200),
                "RISK_REDUCTION_PER_DOLLAR": random.uniform(0.001, 0.005),
                "OUTAGES_MTD": random.randint(0, 5),
                "OUTAGE_MINUTES_MTD": random.uniform(0, 120),
                "VEG_CAUSED_OUTAGES_MTD": random.randint(0, 2),
                "DAYS_TO_FIRE_SEASON": max(0, days_to_fire),
                "FIRE_SEASON_READINESS_PCT": round(random.uniform(60, 95), 1),
            })
    
    return pd.DataFrame(snapshots)


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def main():
    """Generate all synthetic data and save to parquet files."""
    print("🔧 VIGIL Synthetic Data Generator")
    print("=" * 50)
    
    # Generate data in dependency order
    print("📍 Generating locations...")
    locations_df = generate_locations_df()
    print(f"   Created {len(locations_df)} locations")
    
    print("⚡ Generating circuits...")
    circuits_df = generate_circuits_df(locations_df)
    print(f"   Created {len(circuits_df)} circuits")
    
    print("🔩 Generating assets...")
    assets_df = generate_assets_df(circuits_df, locations_df)
    print(f"   Created {len(assets_df)} assets")
    
    print("🌲 Generating vegetation encroachment...")
    vegetation_df = generate_vegetation_df(assets_df, locations_df, circuits_df)
    print(f"   Created {len(vegetation_df)} vegetation records")
    
    print("📊 Generating AMI readings (Hidden Discovery data)...")
    ami_df = generate_ami_readings_df(assets_df)
    print(f"   Created {len(ami_df)} AMI readings")
    
    print("📋 Generating work orders...")
    work_orders_df = generate_work_orders_df(assets_df, vegetation_df)
    print(f"   Created {len(work_orders_df)} work orders")
    
    print("🌤️ Generating weather forecasts...")
    weather_df = generate_weather_df(locations_df)
    print(f"   Created {len(weather_df)} weather forecasts")
    
    print("⚠️ Generating risk assessments...")
    risk_assessments_df = generate_risk_assessments_df(assets_df)
    print(f"   Created {len(risk_assessments_df)} risk assessments")
    
    print("🔌 Generating cable failure predictions (Water Treeing)...")
    cable_predictions_df = generate_cable_failure_predictions_df(assets_df, ami_df)
    print(f"   Created {len(cable_predictions_df)} cable predictions")
    
    print("📜 Generating compliance documents...")
    compliance_docs_df = generate_compliance_docs_df()
    print(f"   Created {len(compliance_docs_df)} compliance documents")
    
    print("📈 Generating monthly snapshots...")
    snapshots_df = generate_monthly_snapshots_df(circuits_df, assets_df, vegetation_df)
    print(f"   Created {len(snapshots_df)} monthly snapshots")
    
    # Save to parquet
    print("\n💾 Saving to parquet files...")
    output_dir = "../data/synthetic"
    
    locations_df.to_parquet(f"{output_dir}/locations.parquet", index=False)
    circuits_df.to_parquet(f"{output_dir}/circuits.parquet", index=False)
    assets_df.to_parquet(f"{output_dir}/assets.parquet", index=False)
    vegetation_df.to_parquet(f"{output_dir}/vegetation.parquet", index=False)
    ami_df.to_parquet(f"{output_dir}/ami_readings.parquet", index=False)
    work_orders_df.to_parquet(f"{output_dir}/work_orders.parquet", index=False)
    weather_df.to_parquet(f"{output_dir}/weather.parquet", index=False)
    risk_assessments_df.to_parquet(f"{output_dir}/risk_assessments.parquet", index=False)
    cable_predictions_df.to_parquet(f"{output_dir}/cable_predictions.parquet", index=False)
    compliance_docs_df.to_parquet(f"{output_dir}/compliance_docs.parquet", index=False)
    snapshots_df.to_parquet(f"{output_dir}/monthly_snapshots.parquet", index=False)
    
    print("\n✅ Data generation complete!")
    print("\n📊 Summary:")
    print(f"   Locations: {len(locations_df)}")
    print(f"   Circuits: {len(circuits_df)}")
    print(f"   Assets: {len(assets_df)}")
    print(f"   Vegetation: {len(vegetation_df)}")
    print(f"   AMI Readings: {len(ami_df)}")
    print(f"   Work Orders: {len(work_orders_df)}")
    print(f"   Weather Forecasts: {len(weather_df)}")
    print(f"   Risk Assessments: {len(risk_assessments_df)}")
    print(f"   Cable Predictions: {len(cable_predictions_df)}")
    print(f"   Compliance Docs: {len(compliance_docs_df)}")
    print(f"   Monthly Snapshots: {len(snapshots_df)}")
    
    # Hidden Discovery summary
    water_treeing_cables = cable_predictions_df[cable_predictions_df["WATER_TREEING_SEVERITY"].isin(["MODERATE", "SEVERE"])]
    print(f"\n🔍 Hidden Discovery (Water Treeing):")
    print(f"   Cables with Water Treeing: {len(water_treeing_cables)}")
    print(f"   Severe cases: {len(cable_predictions_df[cable_predictions_df['WATER_TREEING_SEVERITY'] == 'SEVERE'])}")
    print(f"   Potential savings: ${len(water_treeing_cables) * 90000:,} (proactive vs emergency)")


if __name__ == "__main__":
    main()
