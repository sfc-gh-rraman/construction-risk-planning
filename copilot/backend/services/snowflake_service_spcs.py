"""
VIGIL Risk Planning - Snowflake Service (SPCS Compatible)
Uses Snowpark Session for SPCS (auto-detects environment).
Falls back to CLI for local development.
Includes auto-reconnection on token expiration.

ACTUAL SCHEMA (matches DDL):
- ASSET: ASSET_ID, CIRCUIT_ID, LOCATION_ID, ASSET_TYPE, ASSET_SUBTYPE, MATERIAL,
         MANUFACTURER, MODEL_NUMBER, VOLTAGE_CLASS, INSTALLATION_DATE, ASSET_AGE_YEARS,
         CONDITION_SCORE, LAST_INSPECTION_DATE, NEXT_INSPECTION_DUE, INSPECTION_CYCLE_MONTHS,
         REPLACEMENT_COST, MOISTURE_EXPOSURE, WIND_EXPOSURE
- LOCATION: LOCATION_ID, REGION, COUNTY, CITY, ZIP_CODE, LATITUDE, LONGITUDE,
            ELEVATION_FT, TERRAIN_TYPE, LAND_USE
- CIRCUIT: CIRCUIT_ID, CIRCUIT_NAME, VOLTAGE_CLASS, FIRE_THREAT_DISTRICT,
           PRIMARY_LOCATION_ID, TOTAL_CUSTOMERS, CRITICAL_FACILITIES,
           MEDICAL_BASELINE_CUSTOMERS, CIRCUIT_MILES, SUBSTATION_NAME, PSPS_ELIGIBLE
- RISK_ASSESSMENT: ASSESSMENT_ID, ASSET_ID, ASSESSMENT_DATE, FIRE_RISK_SCORE,
                   IGNITION_PROBABILITY, CONSEQUENCE_SCORE, WIND_EXPOSURE_FACTOR,
                   FUEL_LOAD_FACTOR, TERRAIN_FACTOR, ACCESS_DIFFICULTY_FACTOR,
                   COMPOSITE_RISK_SCORE, RISK_TIER, ASSESSED_BY, ASSESSMENT_METHOD
"""

import json
import os
import subprocess
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


def _detect_spcs() -> bool:
    """Detect if running inside SPCS container"""
    if os.path.exists("/snowflake/session/token"):
        return True
    if os.environ.get("SNOWFLAKE_HOST"):
        return True
    if not os.path.exists(os.path.expanduser("~/Library/Python/3.11/bin/snow")):
        if os.path.exists("/app"):
            return True
    return False


IS_SPCS = _detect_spcs()


class SnowflakeServiceSPCS:
    """
    Service for interacting with Snowflake.
    Automatically detects SPCS environment and uses appropriate connection method.
    Includes auto-reconnection on token expiration.
    """
    
    def __init__(self, connection_name: str = "my_snowflake"):
        self.connection_name = connection_name
        self.database = os.getenv("SNOWFLAKE_DATABASE", "RISK_PLANNING_DB")
        self.schema = os.getenv("SNOWFLAKE_SCHEMA", "ATOMIC")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
        self._session = None
        self._connection = None
        
        self.is_spcs = IS_SPCS
        
        if self.is_spcs:
            logger.info("Running inside SPCS - using Snowpark Session")
            self._init_snowpark_session()
        else:
            logger.info("Running locally - using Snowflake CLI")
            self.snow_path = self._find_snow_cli()
    
    def _find_snow_cli(self) -> str:
        """Find the snow CLI path"""
        possible_paths = [
            os.path.expanduser("~/Library/Python/3.11/bin/snow"),
            os.path.expanduser("~/.local/bin/snow"),
            os.path.expanduser("~/.snowflake/bin/snow"),
            "/usr/local/bin/snow",
            "snow"
        ]
        for path in possible_paths:
            if os.path.exists(path) or path == "snow":
                return path
        return "snow"
    
    def _init_snowpark_session(self):
        """Initialize Snowpark Session for SPCS environment"""
        try:
            from snowflake.snowpark import Session
            
            print(f"[SPCS] Initializing Snowpark Session...", flush=True)
            
            self._session = Session.builder.getOrCreate()
            
            print(f"[SPCS] Session created, setting database/schema...", flush=True)
            
            self._session.sql(f"USE DATABASE {self.database}").collect()
            self._session.sql(f"USE SCHEMA {self.schema}").collect()
            
            print(f"[SPCS] Snowpark Session established - DB: {self.database}, Schema: {self.schema}", flush=True)
            logger.info(f"Snowpark Session established - DB: {self.database}, Schema: {self.schema}")
            
            test_result = self._session.sql("SELECT COUNT(*) as cnt FROM ASSET").collect()
            print(f"[SPCS] Test query result: {test_result}", flush=True)
            
        except Exception as e:
            import traceback
            print(f"[SPCS] Failed to establish Snowpark Session: {e}", flush=True)
            traceback.print_exc()
            logger.error(f"Failed to establish Snowpark Session: {e}")
            self._init_connector_fallback()
    
    def _init_connector_fallback(self):
        """Fallback to connector if Snowpark fails - also used for reconnection"""
        try:
            import snowflake.connector
            
            if self._connection:
                try:
                    self._connection.close()
                except:
                    pass
                self._connection = None
            
            token_path = "/snowflake/session/token"
            token = ""
            if os.path.exists(token_path):
                with open(token_path, "r") as f:
                    token = f.read().strip()
            
            self._connection = snowflake.connector.connect(
                host=os.environ.get("SNOWFLAKE_HOST", ""),
                account=os.environ.get("SNOWFLAKE_ACCOUNT", ""),
                authenticator="oauth",
                token=token,
                database=self.database,
                schema=self.schema,
                warehouse=self.warehouse
            )
            print(f"[SPCS] Connector established with warehouse: {self.warehouse}", flush=True)
            logger.info(f"Connector fallback connection established with warehouse: {self.warehouse}")
            return True
        except Exception as e:
            print(f"[SPCS] Connector fallback failed: {e}", flush=True)
            logger.error(f"Connector fallback also failed: {e}")
            return False
    
    def _reconnect_if_needed(self, error_msg: str) -> bool:
        """Check if error is token expiration and reconnect if so"""
        error_str = str(error_msg).lower()
        if "390114" in str(error_msg) or ("token" in error_str and "expired" in error_str):
            print(f"[SPCS] Token expired, reconnecting...", flush=True)
            return self._init_connector_fallback()
        return False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dicts"""
        if self.is_spcs:
            return self._execute_query_snowpark(query)
        else:
            return self._execute_query_cli(query)
    
    def _execute_query_snowpark(self, query: str, retry: bool = True) -> List[Dict[str, Any]]:
        """Execute query using Snowpark Session (SPCS) with auto-reconnect on token expiration"""
        print(f"[QUERY] Executing: {query[:200]}...", flush=True)
        
        try:
            if self._session:
                print(f"[QUERY] Using Snowpark Session", flush=True)
                df = self._session.sql(query)
                rows = df.collect()
                if not rows:
                    print(f"[QUERY] No rows returned", flush=True)
                    return []
                
                results = []
                for row in rows:
                    row_dict = row.asDict()
                    for key, value in row_dict.items():
                        if hasattr(value, 'isoformat'):
                            row_dict[key] = value.isoformat()
                    results.append(row_dict)
                
                print(f"[QUERY] Returned {len(results)} rows", flush=True)
                return results
            elif self._connection:
                print(f"[QUERY] Using Connector fallback", flush=True)
                cursor = self._connection.cursor()
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                
                print(f"[QUERY] Fetched {len(rows)} rows, columns: {columns[:5]}...", flush=True)
                
                results = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        row_dict[col] = value
                    results.append(row_dict)
                
                cursor.close()
                print(f"[QUERY] Returning {len(results)} results", flush=True)
                return results
            else:
                print(f"[QUERY] ERROR: No connection available!", flush=True)
                logger.error("No SPCS connection available")
                return []
                
        except Exception as e:
            error_str = str(e)
            print(f"[QUERY] EXCEPTION: {error_str}", flush=True)
            logger.error(f"SPCS query failed: {e}")
            
            if retry and self._reconnect_if_needed(error_str):
                print(f"[QUERY] Retrying after reconnect...", flush=True)
                return self._execute_query_snowpark(query, retry=False)
            
            return []
    
    def _execute_query_cli(self, query: str) -> List[Dict[str, Any]]:
        """Execute query using Snowflake CLI (local development)"""
        try:
            cmd = [
                self.snow_path, "sql", 
                "-c", self.connection_name,
                "--format", "JSON",
                "-q", query
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"Query failed: {result.stderr}")
                return []
            
            return self._parse_json_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            logger.error("Query timeout")
            return []
        except Exception as e:
            logger.error(f"CLI query failed: {e}")
            return []
    
    def _parse_json_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse snow sql JSON output into list of dicts"""
        try:
            lines = output.strip().split('\n')
            json_lines = []
            in_json = False
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('['):
                    in_json = True
                if in_json:
                    json_lines.append(line)
                if in_json and stripped.endswith(']'):
                    break
            
            if not json_lines:
                return []
            
            json_str = '\n'.join(json_lines)
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []
    
    def execute_dml(self, sql: str, params: Optional[Dict] = None) -> int:
        """Execute DML (INSERT/UPDATE/DELETE) and return affected rows."""
        if self.is_spcs:
            return self._execute_dml_snowpark(sql)
        else:
            return self._execute_dml_cli(sql)
    
    def _execute_dml_snowpark(self, sql: str) -> int:
        """Execute DML using Snowpark Session"""
        try:
            if self._session:
                self._session.sql(sql).collect()
                return 1
            elif self._connection:
                cursor = self._connection.cursor()
                cursor.execute(sql)
                affected = cursor.rowcount
                cursor.close()
                return affected
            return 0
        except Exception as e:
            logger.error(f"DML execution failed: {e}")
            return 0
    
    def _execute_dml_cli(self, sql: str) -> int:
        """Execute DML using CLI"""
        try:
            cmd = [self.snow_path, "sql", "-c", self.connection_name, "-q", sql]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return 1 if result.returncode == 0 else 0
        except Exception as e:
            logger.error(f"CLI DML failed: {e}")
            return 0
    
    # =========================================================================
    # FIRE SEASON COUNTDOWN
    # =========================================================================
    
    def get_fire_season_countdown(self) -> Dict[str, Any]:
        """Calculate days until fire season based on current date."""
        today = date.today()
        current_year = today.year
        
        fire_season_start = date(current_year, 6, 1)
        fire_season_end = date(current_year, 11, 30)
        
        if today < fire_season_start:
            days_until = (fire_season_start - today).days
            return {
                "status": "PRE_SEASON",
                "days_until_fire_season": days_until,
                "fire_season_start": fire_season_start.isoformat(),
                "message": f"{days_until} DAYS until Fire Season"
            }
        elif today <= fire_season_end:
            days_remaining = (fire_season_end - today).days
            return {
                "status": "ACTIVE",
                "days_remaining": days_remaining,
                "fire_season_end": fire_season_end.isoformat(),
                "message": f"FIRE SEASON ACTIVE - {days_remaining} days remaining"
            }
        else:
            next_start = date(current_year + 1, 6, 1)
            days_until = (next_start - today).days
            return {
                "status": "POST_SEASON",
                "days_until_fire_season": days_until,
                "fire_season_start": next_start.isoformat(),
                "message": f"{days_until} DAYS until next Fire Season"
            }
    
    # =========================================================================
    # Direct SQL Query - Pattern Matching (RELIABLE)
    # =========================================================================
    
    def direct_sql_query(self, question: str) -> Dict[str, Any]:
        """Handle common questions with direct SQL - RELIABLE approach."""
        question_lower = question.lower()
        sql = None
        explanation = ""
        db = self.database
        schema = self.schema
        
        if any(kw in question_lower for kw in ["list", "name", "what are", "show me", "give me"]) and "asset" in question_lower:
            sql = f"""
                SELECT ASSET_ID, ASSET_TYPE, ASSET_SUBTYPE, 
                       VOLTAGE_CLASS, ASSET_AGE_YEARS, CONDITION_SCORE, MATERIAL
                FROM {db}.{schema}.ASSET 
                ORDER BY CONDITION_SCORE ASC NULLS LAST
                LIMIT 50
            """
            explanation = "Listing assets with key metrics"
        
        elif "how many" in question_lower and "asset" in question_lower:
            sql = f"SELECT COUNT(*) as ASSET_COUNT FROM {db}.{schema}.ASSET"
            explanation = "Counting total assets"
        
        elif any(kw in question_lower for kw in ["list", "show", "what are"]) and "circuit" in question_lower:
            sql = f"""
                SELECT CIRCUIT_ID, CIRCUIT_NAME, SUBSTATION_NAME, VOLTAGE_CLASS,
                       CIRCUIT_MILES, TOTAL_CUSTOMERS, FIRE_THREAT_DISTRICT
                FROM {db}.{schema}.CIRCUIT
                ORDER BY TOTAL_CUSTOMERS DESC
                LIMIT 50
            """
            explanation = "Listing circuits with details"
        
        elif any(kw in question_lower for kw in ["high risk", "critical", "risk"]) and "asset" in question_lower:
            sql = f"""
                SELECT a.ASSET_ID, a.ASSET_TYPE, a.ASSET_AGE_YEARS,
                       r.COMPOSITE_RISK_SCORE, r.RISK_TIER, r.IGNITION_PROBABILITY,
                       c.CIRCUIT_NAME, c.FIRE_THREAT_DISTRICT
                FROM {db}.{schema}.ASSET a
                JOIN {db}.{schema}.RISK_ASSESSMENT r ON a.ASSET_ID = r.ASSET_ID
                JOIN {db}.{schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
                WHERE r.RISK_TIER IN ('CRITICAL', 'HIGH')
                ORDER BY r.COMPOSITE_RISK_SCORE DESC
                LIMIT 50
            """
            explanation = "High-risk assets requiring attention"
        
        elif "vegetation" in question_lower or "encroachment" in question_lower or "clearance" in question_lower:
            sql = f"""
                SELECT v.ENCROACHMENT_ID, a.ASSET_ID, v.SPECIES, 
                       v.CURRENT_CLEARANCE_FT, v.REQUIRED_CLEARANCE_FT,
                       v.COMPLIANCE_STATUS, v.DAYS_UNTIL_VIOLATION, v.STRIKE_POTENTIAL,
                       c.CIRCUIT_NAME, c.FIRE_THREAT_DISTRICT
                FROM {db}.{schema}.VEGETATION_ENCROACHMENT v
                JOIN {db}.{schema}.ASSET a ON v.ASSET_ID = a.ASSET_ID
                JOIN {db}.{schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
                WHERE v.COMPLIANCE_STATUS IN ('VIOLATION', 'WARNING')
                ORDER BY v.DAYS_UNTIL_VIOLATION ASC NULLS LAST
                LIMIT 50
            """
            explanation = "Vegetation encroachments requiring trim"
        
        elif "work order" in question_lower or "backlog" in question_lower:
            sql = f"""
                SELECT WORK_ORDER_ID, WORK_TYPE, PRIORITY, STATUS, 
                       ESTIMATED_COST, SCHEDULED_DATE, DESCRIPTION
                FROM {db}.{schema}.WORK_ORDER
                WHERE STATUS IN ('PENDING', 'SCHEDULED', 'IN_PROGRESS')
                ORDER BY 
                    CASE PRIORITY 
                        WHEN 'EMERGENCY' THEN 1 
                        WHEN 'URGENT' THEN 2
                        WHEN 'HIGH' THEN 3 
                        WHEN 'MEDIUM' THEN 4 
                        ELSE 5 
                    END,
                    SCHEDULED_DATE ASC
                LIMIT 50
            """
            explanation = "Open work orders by priority"
        
        elif "fire" in question_lower and ("tier" in question_lower or "threat" in question_lower or "district" in question_lower):
            sql = f"""
                SELECT c.FIRE_THREAT_DISTRICT, l.REGION, l.COUNTY,
                       COUNT(DISTINCT c.CIRCUIT_ID) as CIRCUIT_COUNT,
                       COUNT(DISTINCT a.ASSET_ID) as ASSET_COUNT
                FROM {db}.{schema}.CIRCUIT c
                JOIN {db}.{schema}.ASSET a ON c.CIRCUIT_ID = a.CIRCUIT_ID
                JOIN {db}.{schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
                GROUP BY c.FIRE_THREAT_DISTRICT, l.REGION, l.COUNTY
                ORDER BY c.FIRE_THREAT_DISTRICT DESC
                LIMIT 50
            """
            explanation = "Fire threat district summary"
        
        elif any(kw in question_lower for kw in ["summary", "overview", "dashboard", "kpi"]):
            sql = f"""
                SELECT 
                    (SELECT COUNT(*) FROM {db}.{schema}.ASSET) as TOTAL_ASSETS,
                    (SELECT COUNT(*) FROM {db}.{schema}.CIRCUIT) as TOTAL_CIRCUITS,
                    (SELECT COUNT(*) FROM {db}.{schema}.RISK_ASSESSMENT WHERE RISK_TIER = 'CRITICAL') as CRITICAL_RISKS,
                    (SELECT COUNT(*) FROM {db}.{schema}.VEGETATION_ENCROACHMENT WHERE COMPLIANCE_STATUS = 'VIOLATION') as VEG_VIOLATIONS,
                    (SELECT COUNT(*) FROM {db}.{schema}.WORK_ORDER WHERE STATUS IN ('SCHEDULED', 'IN_PROGRESS')) as ACTIVE_WORK_ORDERS
            """
            explanation = "Portfolio summary metrics"
        
        if sql:
            try:
                results = self.execute_query(sql)
                return {
                    "sql": sql.strip(),
                    "results": results,
                    "explanation": explanation,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Direct SQL query failed: {e}")
                return {"error": str(e), "sql": sql, "results": []}
        
        return {"error": "Could not understand the question", "sql": None, "results": []}
    
    # =========================================================================
    # Asset Queries - USING ACTUAL COLUMN NAMES
    # =========================================================================
    
    def get_assets(self, region: Optional[str] = None, asset_type: Optional[str] = None) -> List[Dict]:
        """Get assets with optional filtering."""
        sql = f"""
        SELECT 
            a.ASSET_ID,
            a.ASSET_TYPE,
            a.ASSET_SUBTYPE,
            a.VOLTAGE_CLASS,
            a.INSTALLATION_DATE,
            a.ASSET_AGE_YEARS,
            a.CONDITION_SCORE,
            a.LAST_INSPECTION_DATE,
            a.REPLACEMENT_COST,
            a.MOISTURE_EXPOSURE,
            c.CIRCUIT_NAME,
            c.FIRE_THREAT_DISTRICT,
            l.REGION,
            l.LATITUDE,
            l.LONGITUDE
        FROM {self.database}.{self.schema}.ASSET a
        JOIN {self.database}.{self.schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        WHERE 1=1
        """
        if region:
            sql += f" AND l.REGION = '{region}'"
        if asset_type:
            sql += f" AND a.ASSET_TYPE = '{asset_type}'"
        sql += " ORDER BY a.CONDITION_SCORE ASC NULLS LAST LIMIT 1000"
        
        return self.execute_query(sql)
    
    def get_asset_summary(self) -> List[Dict]:
        """Get asset summary by region and type."""
        sql = f"""
        SELECT 
            l.REGION,
            a.ASSET_TYPE,
            COUNT(*) as ASSET_COUNT,
            AVG(a.CONDITION_SCORE) as AVG_CONDITION,
            AVG(a.ASSET_AGE_YEARS) as AVG_AGE,
            COUNT(CASE WHEN a.CONDITION_SCORE < 0.5 THEN 1 END) as POOR_CONDITION_COUNT
        FROM {self.database}.{self.schema}.ASSET a
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        GROUP BY l.REGION, a.ASSET_TYPE
        ORDER BY l.REGION, a.ASSET_TYPE
        """
        return self.execute_query(sql)
    
    def get_replacement_priorities(self, limit: int = 50) -> List[Dict]:
        """Get assets prioritized for replacement."""
        sql = f"""
        SELECT 
            a.ASSET_ID,
            a.ASSET_TYPE,
            a.CONDITION_SCORE,
            a.ASSET_AGE_YEARS,
            a.REPLACEMENT_COST,
            c.CIRCUIT_NAME,
            c.FIRE_THREAT_DISTRICT,
            l.REGION,
            r.IGNITION_PROBABILITY,
            r.COMPOSITE_RISK_SCORE,
            CASE 
                WHEN c.FIRE_THREAT_DISTRICT = 'TIER_3' THEN 3.0
                WHEN c.FIRE_THREAT_DISTRICT = 'TIER_2' THEN 2.0
                WHEN c.FIRE_THREAT_DISTRICT = 'TIER_1' THEN 1.5
                ELSE 1.0
            END * COALESCE(r.IGNITION_PROBABILITY, 0.5) as PRIORITY_SCORE
        FROM {self.database}.{self.schema}.ASSET a
        JOIN {self.database}.{self.schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        LEFT JOIN {self.database}.{self.schema}.RISK_ASSESSMENT r ON a.ASSET_ID = r.ASSET_ID
        WHERE a.CONDITION_SCORE < 0.5
        ORDER BY PRIORITY_SCORE DESC
        LIMIT {limit}
        """
        return self.execute_query(sql)
    
    # =========================================================================
    # Vegetation Queries
    # =========================================================================
    
    def get_vegetation_encroachments(self, region: Optional[str] = None) -> List[Dict]:
        """Get vegetation encroachment data."""
        sql = f"""
        SELECT 
            v.ENCROACHMENT_ID,
            v.ASSET_ID,
            v.SPECIES,
            v.TREE_HEIGHT_FT,
            v.CURRENT_CLEARANCE_FT,
            v.REQUIRED_CLEARANCE_FT,
            v.CLEARANCE_DEFICIT_FT,
            v.DAYS_TO_CONTACT,
            v.TRIM_PRIORITY,
            v.GROWTH_RATE_FT_YEAR,
            c.CIRCUIT_NAME,
            c.FIRE_THREAT_DISTRICT,
            l.REGION,
            l.LATITUDE,
            l.LONGITUDE
        FROM {self.database}.{self.schema}.VEGETATION_ENCROACHMENT v
        JOIN {self.database}.{self.schema}.ASSET a ON v.ASSET_ID = a.ASSET_ID
        JOIN {self.database}.{self.schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        WHERE 1=1
        """
        if region:
            sql += f" AND l.REGION = '{region}'"
        sql += " ORDER BY v.DAYS_TO_CONTACT ASC NULLS LAST LIMIT 1000"
        
        return self.execute_query(sql)
    
    def get_compliance_summary(self) -> List[Dict]:
        """Get GO95 compliance summary by region and fire district."""
        sql = f"""
        SELECT 
            l.REGION,
            c.FIRE_THREAT_DISTRICT,
            COUNT(*) as TOTAL_ENCROACHMENTS,
            COUNT(CASE WHEN v.TRIM_PRIORITY = 'CRITICAL' THEN 1 END) as CRITICAL,
            COUNT(CASE WHEN v.TRIM_PRIORITY = 'HIGH' THEN 1 END) as HIGH_PRIORITY,
            COUNT(CASE WHEN v.TRIM_PRIORITY IN ('CRITICAL', 'HIGH') THEN 1 END) as OUT_OF_COMPLIANCE,
            AVG(v.CURRENT_CLEARANCE_FT) as AVG_CLEARANCE_FT,
            MIN(v.DAYS_TO_CONTACT) as MIN_DAYS_TO_CONTACT,
            SUM(v.ESTIMATED_TRIM_COST) as TOTAL_TRIM_COST
        FROM {self.database}.{self.schema}.VEGETATION_ENCROACHMENT v
        JOIN {self.database}.{self.schema}.ASSET a ON v.ASSET_ID = a.ASSET_ID
        JOIN {self.database}.{self.schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        GROUP BY l.REGION, c.FIRE_THREAT_DISTRICT
        ORDER BY l.REGION, c.FIRE_THREAT_DISTRICT
        """
        return self.execute_query(sql)
    
    def get_trim_priorities(self, limit: int = 50) -> List[Dict]:
        """Get vegetation trim priorities."""
        sql = f"""
        SELECT 
            v.ENCROACHMENT_ID,
            v.ASSET_ID,
            v.SPECIES,
            v.CURRENT_CLEARANCE_FT,
            v.REQUIRED_CLEARANCE_FT,
            v.DAYS_TO_CONTACT,
            v.TRIM_PRIORITY,
            c.CIRCUIT_NAME,
            c.FIRE_THREAT_DISTRICT,
            l.REGION,
            CASE 
                WHEN c.FIRE_THREAT_DISTRICT = 'TIER_3' THEN 3.0
                WHEN c.FIRE_THREAT_DISTRICT = 'TIER_2' THEN 2.0
                WHEN c.FIRE_THREAT_DISTRICT = 'TIER_1' THEN 1.5
                ELSE 1.0
            END * (1.0 / NULLIF(v.DAYS_TO_CONTACT, 0)) as PRIORITY_SCORE
        FROM {self.database}.{self.schema}.VEGETATION_ENCROACHMENT v
        JOIN {self.database}.{self.schema}.ASSET a ON v.ASSET_ID = a.ASSET_ID
        JOIN {self.database}.{self.schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        WHERE v.TRIM_PRIORITY IN ('CRITICAL', 'HIGH')
        ORDER BY PRIORITY_SCORE DESC NULLS LAST
        LIMIT {limit}
        """
        return self.execute_query(sql)
    
    # =========================================================================
    # Risk Queries
    # =========================================================================
    
    def get_risk_assessments(self, region: Optional[str] = None) -> List[Dict]:
        """Get risk assessment data."""
        sql = f"""
        SELECT 
            r.ASSESSMENT_ID,
            r.ASSET_ID,
            r.COMPOSITE_RISK_SCORE,
            r.RISK_TIER,
            r.IGNITION_PROBABILITY,
            r.FIRE_RISK_SCORE,
            r.CONSEQUENCE_SCORE,
            a.ASSET_TYPE,
            c.CIRCUIT_NAME,
            c.FIRE_THREAT_DISTRICT,
            l.REGION,
            l.LATITUDE,
            l.LONGITUDE
        FROM {self.database}.{self.schema}.RISK_ASSESSMENT r
        JOIN {self.database}.{self.schema}.ASSET a ON r.ASSET_ID = a.ASSET_ID
        JOIN {self.database}.{self.schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        WHERE 1=1
        """
        if region:
            sql += f" AND l.REGION = '{region}'"
        sql += " ORDER BY r.COMPOSITE_RISK_SCORE DESC LIMIT 1000"
        
        return self.execute_query(sql)
    
    def get_risk_summary(self) -> List[Dict]:
        """Get risk summary by region and tier."""
        sql = f"""
        SELECT 
            l.REGION,
            r.RISK_TIER,
            COUNT(*) as ASSET_COUNT,
            AVG(r.IGNITION_PROBABILITY) as AVG_IGNITION_PROB,
            AVG(r.FIRE_RISK_SCORE) as AVG_FIRE_RISK,
            AVG(r.COMPOSITE_RISK_SCORE) as AVG_COMPOSITE_RISK
        FROM {self.database}.{self.schema}.RISK_ASSESSMENT r
        JOIN {self.database}.{self.schema}.ASSET a ON r.ASSET_ID = a.ASSET_ID
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        GROUP BY l.REGION, r.RISK_TIER
        ORDER BY l.REGION, 
            CASE r.RISK_TIER 
                WHEN 'CRITICAL' THEN 1 
                WHEN 'HIGH' THEN 2 
                WHEN 'MEDIUM' THEN 3 
                ELSE 4 
            END
        """
        return self.execute_query(sql)
    
    def get_psps_candidates(self) -> List[Dict]:
        """Get circuits eligible for PSPS."""
        sql = f"""
        SELECT 
            c.CIRCUIT_ID,
            c.CIRCUIT_NAME,
            c.FIRE_THREAT_DISTRICT,
            c.TOTAL_CUSTOMERS,
            c.CRITICAL_FACILITIES,
            c.MEDICAL_BASELINE_CUSTOMERS,
            c.CIRCUIT_MILES,
            c.PSPS_ELIGIBLE,
            l.REGION
        FROM {self.database}.{self.schema}.CIRCUIT c
        LEFT JOIN {self.database}.{self.schema}.LOCATION l ON c.PRIMARY_LOCATION_ID = l.LOCATION_ID
        WHERE c.PSPS_ELIGIBLE = TRUE
        ORDER BY c.TOTAL_CUSTOMERS DESC
        LIMIT 100
        """
        return self.execute_query(sql)
    
    # =========================================================================
    # AMI Queries (for Water Treeing discovery - if AMI_READING table exists)
    # =========================================================================
    
    def get_ami_readings(self) -> List[Dict]:
        """Get AMI readings if table exists."""
        sql = f"""
        SELECT * FROM {self.database}.{self.schema}.AMI_READING
        ORDER BY READING_TIMESTAMP DESC NULLS LAST
        LIMIT 500
        """
        return self.execute_query(sql)
    
    def get_water_treeing_candidates(self) -> List[Dict]:
        """Get underground cables with water treeing indicators."""
        sql = f"""
        SELECT 
            a.ASSET_ID,
            a.ASSET_TYPE,
            a.MATERIAL,
            a.MOISTURE_EXPOSURE,
            a.ASSET_AGE_YEARS,
            a.CONDITION_SCORE,
            c.CIRCUIT_NAME,
            c.FIRE_THREAT_DISTRICT,
            l.REGION
        FROM {self.database}.{self.schema}.ASSET a
        JOIN {self.database}.{self.schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        WHERE a.ASSET_TYPE = 'CABLE_UNDERGROUND'
        AND a.MOISTURE_EXPOSURE = 'HIGH'
        ORDER BY a.CONDITION_SCORE ASC, a.ASSET_AGE_YEARS DESC
        LIMIT 200
        """
        return self.execute_query(sql)
    
    def get_rain_correlated_dips(self) -> List[Dict]:
        """Get rain-correlated voltage dips if AMI data exists."""
        return []
    
    # =========================================================================
    # Work Order Queries
    # =========================================================================
    
    def get_work_orders(self, status: Optional[str] = None) -> List[Dict]:
        """Get work orders with optional status filter."""
        sql = f"""
        SELECT 
            w.WORK_ORDER_ID,
            w.WORK_ORDER_TYPE,
            w.PRIORITY,
            w.STATUS,
            w.DESCRIPTION,
            w.ESTIMATED_COST,
            w.SCHEDULED_DATE,
            w.COMPLETED_DATE,
            w.ASSIGNED_CREW,
            a.ASSET_ID,
            a.ASSET_TYPE,
            l.REGION,
            c.CIRCUIT_NAME
        FROM {self.database}.{self.schema}.WORK_ORDER w
        LEFT JOIN {self.database}.{self.schema}.ASSET a ON w.ASSET_ID = a.ASSET_ID
        LEFT JOIN {self.database}.{self.schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
        LEFT JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        WHERE 1=1
        """
        if status:
            sql += f" AND w.STATUS = '{status}'"
        sql += """
        ORDER BY 
            CASE w.PRIORITY 
                WHEN 'EMERGENCY' THEN 1 
                WHEN 'URGENT' THEN 2 
                WHEN 'HIGH' THEN 3 
                WHEN 'MEDIUM' THEN 4 
                ELSE 5 
            END,
            w.SCHEDULED_DATE ASC
        LIMIT 500
        """
        return self.execute_query(sql)
    
    def get_work_order_backlog(self) -> List[Dict]:
        """Get work order backlog summary."""
        sql = f"""
        SELECT 
            l.REGION,
            w.WORK_ORDER_TYPE,
            w.STATUS,
            COUNT(*) as ORDER_COUNT,
            SUM(w.ESTIMATED_COST) as TOTAL_COST
        FROM {self.database}.{self.schema}.WORK_ORDER w
        LEFT JOIN {self.database}.{self.schema}.ASSET a ON w.ASSET_ID = a.ASSET_ID
        LEFT JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        WHERE w.STATUS IN ('PENDING', 'SCHEDULED', 'IN_PROGRESS')
        GROUP BY l.REGION, w.WORK_ORDER_TYPE, w.STATUS
        ORDER BY l.REGION, w.WORK_ORDER_TYPE
        """
        return self.execute_query(sql)
    
    def create_work_order(self, work_order: Dict[str, Any]) -> str:
        """Create a new work order and return the ID."""
        work_order_id = f"WO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        sql = f"""
        INSERT INTO {self.database}.{self.schema}.WORK_ORDER (
            WORK_ORDER_ID,
            ASSET_ID,
            WORK_ORDER_TYPE,
            PRIORITY,
            STATUS,
            DESCRIPTION,
            ESTIMATED_COST,
            SCHEDULED_DATE,
            CREATED_DATE
        ) VALUES (
            '{work_order_id}',
            '{work_order.get('asset_id', '')}',
            '{work_order.get('work_order_type', 'VEGETATION_MANAGEMENT')}',
            '{work_order.get('priority', 'MEDIUM')}',
            'PENDING',
            '{work_order.get('description', '').replace("'", "''")}',
            {work_order.get('estimated_cost', 0)},
            '{work_order.get('scheduled_date', datetime.now().strftime('%Y-%m-%d'))}',
            CURRENT_TIMESTAMP()
        )
        """
        
        self.execute_dml(sql)
        return work_order_id
    
    # =========================================================================
    # Dashboard Queries - MAIN ENDPOINTS
    # =========================================================================
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get all metrics for the main dashboard."""
        return {
            "fire_season": self.get_fire_season_countdown(),
            "asset_summary": self.get_asset_summary(),
            "risk_summary": self.get_risk_summary(),
            "compliance_summary": self.get_compliance_summary(),
            "work_order_backlog": self.get_work_order_backlog()
        }
    
    def get_map_data(self) -> List[Dict]:
        """Get asset locations with risk data for map visualization."""
        sql = f"""
        SELECT 
            a.ASSET_ID,
            a.ASSET_TYPE,
            a.CONDITION_SCORE,
            r.COMPOSITE_RISK_SCORE,
            r.RISK_TIER,
            c.FIRE_THREAT_DISTRICT,
            l.REGION,
            l.LATITUDE,
            l.LONGITUDE
        FROM {self.database}.{self.schema}.ASSET a
        LEFT JOIN {self.database}.{self.schema}.RISK_ASSESSMENT r ON a.ASSET_ID = r.ASSET_ID
        JOIN {self.database}.{self.schema}.CIRCUIT c ON a.CIRCUIT_ID = c.CIRCUIT_ID
        JOIN {self.database}.{self.schema}.LOCATION l ON a.LOCATION_ID = l.LOCATION_ID
        WHERE l.LATITUDE IS NOT NULL AND l.LONGITUDE IS NOT NULL
        LIMIT 5000
        """
        return self.execute_query(sql)
    
    # =========================================================================
    # Cortex LLM
    # =========================================================================
    
    def cortex_complete(self, prompt: str, model: str = "mistral-large2") -> str:
        """Call Cortex Complete for LLM generation."""
        escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
        
        sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            '{model}',
            '{escaped_prompt}'
        ) AS RESPONSE
        """
        
        print(f"[LLM] Calling Cortex LLM with model: {model}", flush=True)
        
        try:
            if self.is_spcs and self._connection:
                cursor = self._connection.cursor()
                cursor.execute(sql)
                row = cursor.fetchone()
                cursor.close()
                
                if row and row[0]:
                    return str(row[0])
                return ""
            elif self.is_spcs and self._session:
                df = self._session.sql(sql)
                rows = df.collect()
                if rows and rows[0][0]:
                    return str(rows[0][0])
                return ""
            else:
                return self._call_llm_cli(sql)
        except Exception as e:
            print(f"[LLM] Error: {e}", flush=True)
            logger.error(f"LLM call failed: {e}")
            return ""
    
    def _call_llm_cli(self, sql: str) -> str:
        """Call Cortex LLM using CLI"""
        try:
            cmd = [self.snow_path, "sql", "-c", self.connection_name, "-q", sql]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return ""
            
            output = result.stdout
            lines = output.strip().split('\n')
            
            for i, line in enumerate(lines):
                if 'RESPONSE' in line and i + 2 < len(lines):
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith('|') and not lines[j].startswith('|--'):
                            response = lines[j].strip('| ')
                            return response
            return ""
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""
    
    def cortex_analyst(self, question: str) -> Dict[str, Any]:
        """Text-to-SQL using Cortex Complete LLM as fallback."""
        schema_context = f"""
You are a SQL expert. Generate Snowflake SQL to answer the user's question.

DATABASE: {self.database}
SCHEMA: {self.schema}

TABLES:
1. ASSET (ASSET_ID, CIRCUIT_ID, LOCATION_ID, ASSET_TYPE, ASSET_SUBTYPE, MATERIAL,
   VOLTAGE_CLASS, INSTALLATION_DATE, ASSET_AGE_YEARS, CONDITION_SCORE,
   MOISTURE_EXPOSURE, WIND_EXPOSURE, REPLACEMENT_COST)

2. CIRCUIT (CIRCUIT_ID, CIRCUIT_NAME, VOLTAGE_CLASS, FIRE_THREAT_DISTRICT,
   TOTAL_CUSTOMERS, CIRCUIT_MILES, SUBSTATION_NAME, PSPS_ELIGIBLE)

3. LOCATION (LOCATION_ID, REGION, COUNTY, CITY, LATITUDE, LONGITUDE, TERRAIN_TYPE)

4. VEGETATION_ENCROACHMENT (ENCROACHMENT_ID, ASSET_ID, SPECIES, HEIGHT_FT,
   CURRENT_CLEARANCE_FT, REQUIRED_CLEARANCE_FT, COMPLIANCE_STATUS, 
   DAYS_UNTIL_VIOLATION, STRIKE_POTENTIAL, GROWTH_RATE_FT_YEAR)

5. RISK_ASSESSMENT (ASSESSMENT_ID, ASSET_ID, COMPOSITE_RISK_SCORE, RISK_TIER,
   IGNITION_PROBABILITY, FIRE_RISK_SCORE, CONSEQUENCE_SCORE)

6. WORK_ORDER (WORK_ORDER_ID, ASSET_ID, WORK_TYPE, PRIORITY, STATUS, 
   ESTIMATED_COST, SCHEDULED_DATE)

RULES:
- Use {self.database}.{self.schema}.TABLE_NAME for all tables
- Return ONLY valid SQL, no explanations
- Always include ORDER BY and LIMIT 50
"""
        
        prompt = f"{schema_context}\n\nUSER QUESTION: {question}\n\nSQL:"
        
        try:
            generated_sql = self.cortex_complete(prompt)
            
            if not generated_sql:
                return {"answer": None, "sql": None, "data": None, "error": "LLM did not generate SQL"}
            
            generated_sql = generated_sql.strip()
            if generated_sql.startswith("```"):
                lines = generated_sql.split("\n")
                generated_sql = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            generated_sql = generated_sql.strip()
            
            results = self.execute_query(generated_sql)
            return {"answer": "Query executed", "sql": generated_sql, "data": results, "error": None}
        except Exception as e:
            return {"answer": None, "sql": None, "data": None, "error": str(e)}
    
    def close(self):
        """Close the connection"""
        if self._session:
            try:
                self._session.close()
            except:
                pass
        if self._connection:
            try:
                self._connection.close()
            except:
                pass


_snowflake_service: Optional[SnowflakeServiceSPCS] = None


def get_snowflake_service() -> SnowflakeServiceSPCS:
    """Get or create Snowflake service singleton"""
    global _snowflake_service
    if _snowflake_service is None:
        _snowflake_service = SnowflakeServiceSPCS()
    return _snowflake_service
