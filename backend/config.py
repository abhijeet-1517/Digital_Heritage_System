import os
from typing import Optional
from dotenv import load_dotenv

# Load variables from root .env if present
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))


class Settings:
    DATABASE_MODE: str = os.getenv("DATABASE_MODE", "mock").strip().lower()
    NEO4J_URI: Optional[str] = os.getenv("NEO4J_URI")
    NEO4J_USERNAME: Optional[str] = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD: Optional[str] = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE: Optional[str] = os.getenv("NEO4J_DATABASE")

    @classmethod
    def validate_neo4j(cls):
        """Validate that all required Neo4j credentials are provided when mode is 'neo4j'."""
        if cls.DATABASE_MODE == "neo4j":
            missing = []
            if not cls.NEO4J_URI or "<dbid>" in cls.NEO4J_URI:
                missing.append("NEO4J_URI")
            if not cls.NEO4J_USERNAME:
                missing.append("NEO4J_USERNAME")
            if not cls.NEO4J_PASSWORD or "your_neo4j_password_here" in cls.NEO4J_PASSWORD:
                missing.append("NEO4J_PASSWORD")
            if missing:
                raise ValueError(
                    f"DATABASE_MODE is set to 'neo4j' but the following configuration variables are missing or unconfigured: {', '.join(missing)}. "
                    "Please set valid credentials in your root .env file."
                )


settings = Settings()
