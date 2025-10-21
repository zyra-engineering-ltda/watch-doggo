"""StatusPage.io adapter for service status checking."""

import json
import logging
from typing import Dict
import requests

from app.models import ServiceStatus, ServiceStatusEnum
from app.services.adapters.base_adapter import BaseServiceAdapter


logger = logging.getLogger(__name__)


class StatusPageIOAdapter(BaseServiceAdapter):
    """Adapter for services using StatusPage.io format."""
    
    def parse_response(self, response: requests.Response, config: Dict) -> ServiceStatus:
        """Parse StatusPage.io JSON response."""
        service_name = config['name']
        
        try:
            # Ensure we got a successful response
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Extract status information
            status_info = data.get('status', {})
            indicator = status_info.get('indicator', 'unknown')
            description = status_info.get('description', 'No description available')
            
            # Map StatusPage.io indicators to our status enum
            status_mapping = {
                'none': ServiceStatusEnum.OPERATIONAL,
                'minor': ServiceStatusEnum.DEGRADED,
                'major': ServiceStatusEnum.DOWN,
                'critical': ServiceStatusEnum.DOWN,
                'maintenance': ServiceStatusEnum.DEGRADED
            }
            
            status = status_mapping.get(indicator, ServiceStatusEnum.UNKNOWN)
            
            # Check for active incidents that might affect status
            incidents = data.get('incidents', [])
            active_incidents = [inc for inc in incidents if inc.get('status') in ['investigating', 'identified', 'monitoring']]
            
            if active_incidents and status == ServiceStatusEnum.OPERATIONAL:
                # If there are active incidents, status should be at least degraded
                status = ServiceStatusEnum.DEGRADED
                incident_names = [inc.get('name', 'Unknown incident') for inc in active_incidents[:3]]
                description = f"Active incidents: {', '.join(incident_names)}"
            
            return ServiceStatus(
                name=service_name,
                status=status,
                last_checked=None,  # Will be set by base adapter
                message=description,
                response_time=0.0  # Will be set by base adapter
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {service_name}: {e}")
            return self._get_fallback_status(response, service_name)
            
        except KeyError as e:
            logger.error(f"Missing expected field in response for {service_name}: {e}")
            return self._get_fallback_status(response, service_name)
            
        except Exception as e:
            logger.error(f"Error parsing StatusPage.io response for {service_name}: {e}")
            return self._get_fallback_status(response, service_name)