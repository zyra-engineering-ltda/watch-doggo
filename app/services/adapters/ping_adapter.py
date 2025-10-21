"""Ping adapter for simple HTTP status checking."""

import logging
from typing import Dict
import requests

from app.models import ServiceStatus, ServiceStatusEnum
from app.services.adapters.base_adapter import BaseServiceAdapter


logger = logging.getLogger(__name__)


class PingAdapter(BaseServiceAdapter):
    """Adapter for simple HTTP ping checks - just checks if URL returns 200."""
    
    def parse_response(self, response: requests.Response, config: Dict) -> ServiceStatus:
        """Parse HTTP response for simple ping check."""
        service_name = config['name']
        
        try:
            # For ping adapter, we only care about HTTP status code
            if response.status_code == 200:
                status = ServiceStatusEnum.OPERATIONAL
                message = f"HTTP {response.status_code} - Service responding"
            elif 400 <= response.status_code < 500:
                status = ServiceStatusEnum.DOWN
                message = f"HTTP {response.status_code} - Client error"
            elif 500 <= response.status_code < 600:
                status = ServiceStatusEnum.DOWN
                message = f"HTTP {response.status_code} - Server error"
            else:
                status = ServiceStatusEnum.UNKNOWN
                message = f"HTTP {response.status_code} - Unexpected response"
            
            return ServiceStatus(
                name=service_name,
                status=status,
                last_checked=None,  # Will be set by base adapter
                message=message,
                response_time=0.0  # Will be set by base adapter
            )
            
        except Exception as e:
            logger.error(f"Error in ping check for {service_name}: {e}")
            return self._get_fallback_status(response, service_name)