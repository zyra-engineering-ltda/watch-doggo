"""Data models for Service Status Monitor."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ServiceStatusEnum(Enum):
    """Enumeration for service status states."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class ServiceStatus:
    """Data model for service status information."""
    name: str
    status: ServiceStatusEnum
    last_checked: datetime
    message: str
    response_time: float
    error: Optional[str] = None
    category: Optional[str] = None
    display_name: Optional[str] = None
    url: Optional[str] = None
    
    def to_dict(self):
        """Convert ServiceStatus to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'status': self.status.value,
            'last_checked': self.last_checked.isoformat(),
            'message': self.message,
            'response_time': self.response_time,
            'error': self.error,
            'category': self.category,
            'display_name': self.display_name,
            'url': self.url
        }