"""Base adapter interface for service status checking."""

from abc import ABC, abstractmethod
import requests
import time
import logging
from typing import Dict
from datetime import datetime

from app.models import ServiceStatus, ServiceStatusEnum


logger = logging.getLogger(__name__)


class BaseServiceAdapter(ABC):
    """Abstract base class for service status adapters."""
    
    def __init__(self, timeout: int = 30):
        """Initialize adapter with timeout setting."""
        self.timeout = timeout
        self.session = requests.Session()
        # Set common headers
        self.session.headers.update({
            'User-Agent': 'ServiceStatusMonitor/1.0'
        })
    
    def check_status(self, service_config: Dict) -> ServiceStatus:
        """Check service status using the configured adapter."""
        start_time = time.time()
        service_name = service_config['name']
        url = service_config['url']
        
        try:
            logger.info(f"Checking status for {service_name} at {url}")
            
            # Make HTTP request
            response = self.session.get(url, timeout=self.timeout)
            response_time = time.time() - start_time
            
            # Parse response using adapter-specific logic
            status = self.parse_response(response, service_config)
            status.response_time = response_time
            status.last_checked = datetime.now()
            
            logger.info(f"Status check completed for {service_name}: {status.status.value}")
            return status
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout checking {service_name}")
            return ServiceStatus(
                name=service_name,
                status=ServiceStatusEnum.UNKNOWN,
                last_checked=datetime.now(),
                message="Request timeout",
                response_time=time.time() - start_time,
                error="Connection timeout"
            )
            
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error checking {service_name}")
            return ServiceStatus(
                name=service_name,
                status=ServiceStatusEnum.DOWN,
                last_checked=datetime.now(),
                message="Connection failed",
                response_time=time.time() - start_time,
                error="Connection error"
            )
            
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error checking {service_name}: {e}")
            return ServiceStatus(
                name=service_name,
                status=ServiceStatusEnum.DOWN,
                last_checked=datetime.now(),
                message=f"HTTP error: {e.response.status_code}",
                response_time=time.time() - start_time,
                error=str(e)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error checking {service_name}: {e}")
            return ServiceStatus(
                name=service_name,
                status=ServiceStatusEnum.UNKNOWN,
                last_checked=datetime.now(),
                message="Unexpected error",
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    @abstractmethod
    def parse_response(self, response: requests.Response, config: Dict) -> ServiceStatus:
        """Parse HTTP response to determine service status.
        
        Args:
            response: HTTP response object
            config: Service configuration dictionary
            
        Returns:
            ServiceStatus object with parsed status information
        """
        pass
    
    def _get_fallback_status(self, response: requests.Response, service_name: str) -> ServiceStatus:
        """Get fallback status based on HTTP response code."""
        if response.status_code == 200:
            status = ServiceStatusEnum.OPERATIONAL
            message = "HTTP 200 OK"
        elif 400 <= response.status_code < 500:
            status = ServiceStatusEnum.DOWN
            message = f"HTTP {response.status_code} Client Error"
        elif 500 <= response.status_code < 600:
            status = ServiceStatusEnum.DOWN
            message = f"HTTP {response.status_code} Server Error"
        else:
            status = ServiceStatusEnum.UNKNOWN
            message = f"HTTP {response.status_code}"
        
        return ServiceStatus(
            name=service_name,
            status=status,
            last_checked=datetime.now(),
            message=message,
            response_time=0.0  # Will be set by check_status
        )