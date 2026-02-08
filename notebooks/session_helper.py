"""
Snowpark Session Helper - Dual Mode (Local Testing + Live Snowflake)

This module provides a unified way to create Snowpark sessions that work both:
1. LOCALLY - Using local testing framework (no Snowflake connection, no credits)
2. LIVE - Connected to Snowflake for real execution

Usage:
    from session_helper import get_session, SessionMode
    
    # For local development/testing (default)
    session = get_session(mode=SessionMode.LOCAL)
    
    # For live Snowflake execution
    session = get_session(mode=SessionMode.LIVE)
    
    # Auto-detect (checks for Snowflake Notebook environment)
    session = get_session(mode=SessionMode.AUTO)
"""

import os
from enum import Enum
from typing import Optional
from snowflake.snowpark import Session


class SessionMode(Enum):
    LOCAL = "local"
    LIVE = "live"
    AUTO = "auto"


def _is_snowflake_notebook() -> bool:
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        return session is not None
    except:
        return False


def _get_connection_params() -> dict:
    connection_name = os.getenv("SNOWFLAKE_CONNECTION_NAME", "my_snowflake")
    
    return {
        "connection_name": connection_name,
        "database": "RISK_PLANNING_DB",
        "schema": "ML",
        "warehouse": "COMPUTE_WH"
    }


def get_session(mode: SessionMode = SessionMode.AUTO) -> Session:
    """
    Get a Snowpark Session based on the specified mode.
    
    Args:
        mode: SessionMode.LOCAL (testing), SessionMode.LIVE (Snowflake), or SessionMode.AUTO
        
    Returns:
        Snowpark Session object
    """
    if mode == SessionMode.AUTO:
        if _is_snowflake_notebook():
            from snowflake.snowpark.context import get_active_session
            print("📍 Running in Snowflake Notebook - using active session")
            return get_active_session()
        else:
            mode = SessionMode.LIVE
            print("📍 Running locally - connecting to Snowflake")
    
    if mode == SessionMode.LOCAL:
        print("🧪 LOCAL MODE - Using Snowpark Local Testing Framework")
        print("   ⚠️  No Snowflake connection, no credits consumed")
        print("   ⚠️  Some features may not be available")
        session = Session.builder.configs({"local_testing": True}).create()
        return session
    
    else:
        print("🔗 LIVE MODE - Connecting to Snowflake")
        params = _get_connection_params()
        print(f"   Connection: {params.get('connection_name', 'default')}")
        print(f"   Database: {params['database']}")
        print(f"   Schema: {params['schema']}")
        
        session = Session.builder.configs(params).create()
        
        session.sql("USE DATABASE RISK_PLANNING_DB").collect()
        session.sql("USE SCHEMA ML").collect()
        session.sql("USE WAREHOUSE COMPUTE_WH").collect()
        
        print("   ✅ Connected successfully!")
        return session


def get_session_info(session: Session) -> dict:
    """Get current session information."""
    try:
        result = session.sql("""
            SELECT 
                CURRENT_DATABASE() as database,
                CURRENT_SCHEMA() as schema,
                CURRENT_WAREHOUSE() as warehouse,
                CURRENT_USER() as user,
                CURRENT_ROLE() as role,
                CURRENT_ACCOUNT() as account
        """).collect()[0]
        
        return {
            "database": result["DATABASE"],
            "schema": result["SCHEMA"],
            "warehouse": result["WAREHOUSE"],
            "user": result["USER"],
            "role": result["ROLE"],
            "account": result["ACCOUNT"]
        }
    except:
        return {"mode": "local_testing", "note": "Limited session info in local mode"}


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Session Helper")
    print("="*60)
    
    session = get_session(mode=SessionMode.LIVE)
    info = get_session_info(session)
    print(f"\nSession Info: {info}")
    
    print("\n✅ Session helper working correctly!")
