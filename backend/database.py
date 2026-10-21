import logging
from typing import Optional
from neo4j import GraphDatabase, Driver
from backend.config import settings

logger = logging.getLogger("heritage.database")
_driver: Optional[Driver] = None


def init_neo4j_driver() -> Driver:
    """Initialize and verify connectivity to Neo4j instance."""
    global _driver
    if settings.DATABASE_MODE != "neo4j":
        logger.info("DATABASE_MODE is '%s'; skipping Neo4j driver initialization.", settings.DATABASE_MODE)
        return None

    settings.validate_neo4j()
    logger.info("Connecting to Neo4j at %s with user %s...", settings.NEO4J_URI, settings.NEO4J_USERNAME)
    try:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
            max_connection_lifetime=30 * 60,
            max_connection_pool_size=50,
            connection_acquisition_timeout=30.0,
        )
        _driver.verify_connectivity()
        logger.info("Connected successfully to Neo4j Aura.")
        return _driver
    except Exception as e:
        logger.error("Failed to connect to Neo4j: %s", str(e))
        if _driver:
            try:
                _driver.close()
            except Exception:
                pass
            _driver = None
        raise RuntimeError(f"Could not connect to Neo4j at '{settings.NEO4J_URI}': {e}") from e


def get_neo4j_driver() -> Optional[Driver]:
    """Retrieve active Neo4j driver instance."""
    return _driver


def close_neo4j_driver():
    """Safely close active Neo4j driver connection."""
    global _driver
    if _driver is not None:
        logger.info("Closing Neo4j driver connection...")
        try:
            _driver.close()
        except Exception as e:
            logger.warning("Error closing Neo4j driver: %s", e)
        finally:
            _driver = None
