"""
Configuration module for ANP Agent Example.

This module contains configuration settings and constants used throughout
the application, including domain settings, paths, and service parameters.
"""

import os

# Agent service domain configuration
# This should be configured based on your deployment environment
AGENT_DESCRIPTION_JSON_DOMAIN = os.getenv(
    "AGENT_DESCRIPTION_JSON_DOMAIN",
    "agent-connect.ai"
)

# Service configuration
SERVICE_NAME = "ANP智能体示例服务"
SERVICE_VERSION = "1.0.0"
ANP_PROTOCOL_VERSION = "1.0.0"

# API configuration
API_PREFIX = "/agents"
AGENT_PATH_PREFIX = "/travel/test"

# Authentication configuration
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
AUTH_NONCE_EXPIRY_MINUTES = int(os.getenv("AUTH_NONCE_EXPIRY_MINUTES", "5"))
AUTH_TIMESTAMP_EXPIRY_MINUTES = int(os.getenv("AUTH_TIMESTAMP_EXPIRY_MINUTES", "5"))

# Key file paths - default to docs/jwt_key directory (relative to project root)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JWT_PRIVATE_KEY_PATH = os.getenv("JWT_PRIVATE_KEY_PATH", os.path.join(_project_root, "docs/jwt_key/RS256-private.pem"))
JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", os.path.join(_project_root, "docs/jwt_key/RS256-public.pem"))

# API file paths (relative to src directory)
API_FILES_DIRECTORY = "api"
EXTERNAL_INTERFACE_FILE = "external-interface.json"
NL_INTERFACE_FILE = "nl-interface.yaml"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
ALLOWED_METHODS = ["*"]
ALLOWED_HEADERS = ["*"]

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
RELOAD = os.getenv("RELOAD", "True").lower() == "true"

# Agent DID configuration
AGENT_DID_PREFIX = f"did:wba:{AGENT_DESCRIPTION_JSON_DOMAIN}:service"

def get_agent_did(agent_name: str) -> str:
    """
    Generate agent DID based on agent name.
    
    Args:
        agent_name: The name of the agent
        
    Returns:
        Formatted DID string
    """
    return f"{AGENT_DID_PREFIX}:{agent_name}"

def get_agent_url(path: str) -> str:
    """
    Generate full URL for agent resources.
    
    Args:
        path: Resource path
        
    Returns:
        Full URL string
    """
    return f"https://{AGENT_DESCRIPTION_JSON_DOMAIN}{path}"

def get_api_file_path(filename: str) -> str:
    """
    Get full path to API definition file.
    
    Args:
        filename: API file name
        
    Returns:
        Full file path
    """
    return os.path.join(API_FILES_DIRECTORY, filename)

# Validation functions
def validate_config() -> list[str]:
    """
    Validate configuration settings.
    
    Returns:
        List of validation errors, empty if all valid
    """
    errors = []

    if not AGENT_DESCRIPTION_JSON_DOMAIN:
        errors.append("AGENT_DESCRIPTION_JSON_DOMAIN is required")

    if JWT_PRIVATE_KEY_PATH and not os.path.exists(JWT_PRIVATE_KEY_PATH):
        errors.append(f"JWT private key file not found: {JWT_PRIVATE_KEY_PATH}")

    if JWT_PUBLIC_KEY_PATH and not os.path.exists(JWT_PUBLIC_KEY_PATH):
        errors.append(f"JWT public key file not found: {JWT_PUBLIC_KEY_PATH}")

    if not os.path.exists(API_FILES_DIRECTORY):
        errors.append(f"API files directory not found: {API_FILES_DIRECTORY}")

    return errors

# Environment-specific settings
class Settings:
    """Settings class for environment-specific configuration."""

    def __init__(self):
        self.agent_domain = AGENT_DESCRIPTION_JSON_DOMAIN
        self.service_name = SERVICE_NAME
        self.service_version = SERVICE_VERSION
        self.anp_version = ANP_PROTOCOL_VERSION
        self.jwt_algorithm = JWT_ALGORITHM
        self.jwt_private_key_path = JWT_PRIVATE_KEY_PATH
        self.jwt_public_key_path = JWT_PUBLIC_KEY_PATH
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.auth_nonce_expiry_minutes = AUTH_NONCE_EXPIRY_MINUTES
        self.auth_timestamp_expiry_minutes = AUTH_TIMESTAMP_EXPIRY_MINUTES
        self.host = HOST
        self.port = PORT
        self.reload = RELOAD
        self.log_level = LOG_LEVEL

    def validate(self) -> list[str]:
        """Validate settings and return any errors."""
        return validate_config()

# Global settings instance
settings = Settings()
