"""Generic API adapter for service status checking."""

import json
import logging
from typing import Dict, Any
import requests

from app.models import ServiceStatus, ServiceStatusEnum
from app.services.adapters.base_adapter import BaseServiceAdapter


logger = logging.getLogger(__name__)


class APIAdapter(BaseServiceAdapter):
    """Adapter for services with custom JSON APIs."""
    
    def parse_response(self, response: requests.Response, config: Dict) -> ServiceStatus:
        """Parse custom JSON API response."""
        service_name = config['name']
        
        try:
            # Ensure we got a successful response
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Get configuration for JSON parsing
            status_path = config.get('status_path', 'status')
            status_mapping = config.get('status_mapping', {})
            
            # Extract status value using dot notation path
            status_value = self._get_nested_value(data, status_path)
            
            if status_value is None:
                logger.warning(f"Status path '{status_path}' not found for {service_name}")
                return self._get_fallback_status(response, service_name)
            
            # Handle array responses (like incidents)
            if isinstance(status_value, list):
                status = self._parse_incidents_array(status_value, status_mapping, service_name)
            else:
                # Handle single value responses
                status = self._map_status_value(status_value, status_mapping)
            
            # Generate appropriate message
            if isinstance(status_value, list):
                message = f"Found {len(status_value)} items in status array"
            else:
                message = f"Status: {status_value}"
            
            return ServiceStatus(
                name=service_name,
                status=status,
                last_checked=None,  # Will be set by base adapter
                message=message,
                response_time=0.0  # Will be set by base adapter
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {service_name}: {e}")
            return self._get_fallback_status(response, service_name)
            
        except Exception as e:
            logger.error(f"Error parsing API response for {service_name}: {e}")
            return self._get_fallback_status(response, service_name)
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Extract nested value from dictionary using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _parse_incidents_array(self, incidents: list, status_mapping: Dict, service_name: str) -> ServiceStatusEnum:
        """Parse incidents array to determine overall status."""
        if not incidents:
            # No incidents means operational
            return ServiceStatusEnum.OPERATIONAL
        
        # Check for open/active incidents
        active_incidents = []
        for incident in incidents:
            if isinstance(incident, dict):
                incident_status = incident.get('status', '').lower()
                if incident_status in ['open', 'investigating', 'identified', 'monitoring']:
                    active_incidents.append(incident)
        
        if active_incidents:
            # Determine severity based on incident impact
            max_severity = ServiceStatusEnum.DEGRADED
            for incident in active_incidents:
                impact = incident.get('impact', '').lower()
                if impact in ['critical', 'major']:
                    max_severity = ServiceStatusEnum.DOWN
                    break
                elif impact in ['minor']:
                    max_severity = ServiceStatusEnum.DEGRADED
            
            return max_severity
        
        return ServiceStatusEnum.OPERATIONAL
    
    def _map_status_value(self, value: Any, status_mapping: Dict) -> ServiceStatusEnum:
        """Map status value to ServiceStatusEnum using provided mapping."""
        # Convert value to string for mapping
        str_value = str(value).lower()
        
        # Check custom mapping first
        for map_key, map_status in status_mapping.items():
            if str_value == map_key.lower():
                return ServiceStatusEnum(map_status)
        
        # Default mapping for common values
        default_mapping = {
            'operational': ServiceStatusEnum.OPERATIONAL,
            'ok': ServiceStatusEnum.OPERATIONAL,
            'up': ServiceStatusEnum.OPERATIONAL,
            'online': ServiceStatusEnum.OPERATIONAL,
            'good': ServiceStatusEnum.OPERATIONAL,
            'degraded': ServiceStatusEnum.DEGRADED,
            'partial': ServiceStatusEnum.DEGRADED,
            'issues': ServiceStatusEnum.DEGRADED,
            'down': ServiceStatusEnum.DOWN,
            'offline': ServiceStatusEnum.DOWN,
            'outage': ServiceStatusEnum.DOWN,
            'critical': ServiceStatusEnum.DOWN
        }
        
        return default_mapping.get(str_value, ServiceStatusEnum.UNKNOWN)