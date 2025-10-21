"""ANP Agent Example Package.

This package demonstrates how to build an ANP-compliant agent service
using FastAPI, implementing agent description protocol, DID-WBA authentication,
and standardized API interfaces.
"""

__version__ = "1.0.0"
__author__ = "ANP Agent Example Team"

# Export main components for easy access
from .config import settings

__all__ = ["settings"]
