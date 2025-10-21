"""RSS adapter for status monitoring."""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Optional
import re
import requests

from app.services.adapters.base_adapter import BaseServiceAdapter
from app.models import ServiceStatus, ServiceStatusEnum


class RSSAdapter(BaseServiceAdapter):
    """Adapter for RSS-based status pages."""
    
    def __init__(self, timeout: int = 30):
        super().__init__(timeout)
    
    def parse_response(self, response: requests.Response, service_config: Dict[str, Any]) -> ServiceStatus:
        """Parse RSS feed response to determine service status."""
        try:
            # Parse RSS XML
            root = ET.fromstring(response.text)
            
            # Extract service information
            service_name = service_config.get("name", "Unknown Service")
            display_name = service_config.get("display_name", service_name)
            url = service_config.get("url", "")
            
            # Parse RSS feed based on provider
            provider = service_config.get("provider", "generic")
            
            if provider == "aws":
                return self._parse_aws_rss(root, service_name, display_name, url, service_config)
            else:
                return self._parse_generic_rss(root, service_name, display_name, url, service_config)
                
        except ET.ParseError as e:
            return ServiceStatus(
                name=service_config.get("name", "unknown"),
                status=ServiceStatusEnum.UNKNOWN,
                message=f"Failed to parse RSS feed: {str(e)}",
                last_checked=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
        except Exception as e:
            return ServiceStatus(
                name=service_config.get("name", "unknown"),
                status=ServiceStatusEnum.UNKNOWN,
                message=f"Error checking status: {str(e)}",
                last_checked=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
    
    def _parse_aws_rss(self, root: ET.Element, service_name: str, display_name: str, 
                       url: str, service_config: Dict[str, Any]) -> ServiceStatus:
        """Parse AWS-specific RSS feed format."""
        try:
            # AWS RSS uses channel/item structure
            channel = root.find('channel')
            if channel is None:
                raise ValueError("No channel found in RSS feed")
            
            # Get recent items (incidents)
            items = channel.findall('item')
            
            # Filter services if specified
            target_services = service_config.get("services", [])
            region = service_config.get("region", "us-east-1")
            
            # Check for recent incidents
            recent_incidents = []
            operational_services = set()
            
            for item in items:
                title = item.find('title')
                description = item.find('description')
                pub_date = item.find('pubDate')
                
                if title is None or description is None:
                    continue
                
                title_text = title.text or ""
                desc_text = description.text or ""
                
                # Parse AWS incident format
                incident_info = self._parse_aws_incident(title_text, desc_text, region, target_services)
                
                if incident_info:
                    recent_incidents.append(incident_info)
                    
            # Determine overall status
            if not recent_incidents:
                status = ServiceStatusEnum.OPERATIONAL
                message = f"All monitored AWS services operational in {region}"
            else:
                # Check severity of incidents
                critical_incidents = [i for i in recent_incidents if i['severity'] in ['high', 'critical']]
                
                if critical_incidents:
                    status = ServiceStatusEnum.DOWN
                    affected_services = list(set([i['service'] for i in critical_incidents]))
                    message = f"Critical issues: {', '.join(affected_services[:3])}"
                    if len(affected_services) > 3:
                        message += f" and {len(affected_services) - 3} more"
                else:
                    status = ServiceStatusEnum.DEGRADED
                    affected_services = list(set([i['service'] for i in recent_incidents]))
                    message = f"Service issues: {', '.join(affected_services[:3])}"
                    if len(affected_services) > 3:
                        message += f" and {len(affected_services) - 3} more"
            
            # Add region info to message if there are incidents
            if recent_incidents:
                message += f" ({region})"
            
            return ServiceStatus(
                name=service_name,
                status=status,
                message=message,
                last_checked=datetime.now(),
                response_time=0.0
            )
            
        except Exception as e:
            return ServiceStatus(
                name=service_name,
                status=ServiceStatusEnum.UNKNOWN,
                message=f"Error parsing AWS status: {str(e)}",
                last_checked=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
    
    def _parse_aws_incident(self, title: str, description: str, region: str, 
                           target_services: list) -> Optional[Dict[str, Any]]:
        """Parse individual AWS incident from RSS item."""
        try:
            # AWS RSS title format: "[RESOLVED] Service Issue - EC2 (us-east-1)"
            # or "Service Degradation - RDS (us-west-2)"
            
            # Extract status
            status_match = re.search(r'\[(.*?)\]', title)
            incident_status = status_match.group(1).lower() if status_match else 'ongoing'
            
            # Skip resolved incidents older than 24 hours (you might want to adjust this)
            if incident_status == 'resolved':
                return None
            
            # Extract service name
            service_match = re.search(r'- ([A-Za-z0-9\s]+) \(', title)
            if not service_match:
                return None
                
            service = service_match.group(1).strip()
            
            # Extract region
            region_match = re.search(r'\(([^)]+)\)', title)
            incident_region = region_match.group(1) if region_match else 'unknown'
            
            # Filter by region if specified
            if region != 'all' and incident_region != region:
                return None
            
            # Filter by services if specified
            if target_services and service.lower() not in [s.lower() for s in target_services]:
                return None
            
            # Determine severity from title and description
            severity = 'medium'
            if any(word in title.lower() for word in ['outage', 'down', 'unavailable']):
                severity = 'high'
            elif any(word in title.lower() for word in ['degraded', 'slow', 'intermittent']):
                severity = 'medium'
            elif any(word in description.lower() for word in ['critical', 'major']):
                severity = 'high'
            
            return {
                'service': service,
                'region': incident_region,
                'status': incident_status,
                'severity': severity,
                'title': title,
                'description': description[:200] + '...' if len(description) > 200 else description
            }
            
        except Exception as e:
            return None
    
    def _parse_generic_rss(self, root: ET.Element, service_name: str, display_name: str,
                          url: str, service_config: Dict[str, Any]) -> ServiceStatus:
        """Parse generic RSS feed format."""
        try:
            # Generic RSS parsing - look for recent items
            channel = root.find('channel')
            if channel is None:
                # Try direct items
                items = root.findall('.//item')
            else:
                items = channel.findall('item')
            
            # If no recent incidents, assume operational
            if not items:
                return ServiceStatus(
                    name=service_name,
                    status=ServiceStatusEnum.OPERATIONAL,
                    message="No recent incidents reported",
                    last_checked=datetime.now(),
                    response_time=0.0
                )
            
            # Check most recent item
            latest_item = items[0]
            title = latest_item.find('title')
            description = latest_item.find('description')
            
            title_text = title.text if title is not None else ""
            desc_text = description.text if description is not None else ""
            
            # Simple status detection based on keywords
            combined_text = (title_text + " " + desc_text).lower()
            
            if any(word in combined_text for word in ['resolved', 'fixed', 'restored', 'operational']):
                status = ServiceStatusEnum.OPERATIONAL
                message = "Service restored"
            elif any(word in combined_text for word in ['outage', 'down', 'unavailable', 'offline']):
                status = ServiceStatusEnum.DOWN
                message = title_text or "Service outage reported"
            elif any(word in combined_text for word in ['degraded', 'slow', 'issues', 'problems']):
                status = ServiceStatusEnum.DEGRADED
                message = title_text or "Service issues reported"
            else:
                status = ServiceStatusEnum.OPERATIONAL
                message = "No current issues"
            
            return ServiceStatus(
                name=service_name,
                status=status,
                message=message,
                last_checked=datetime.now(),
                response_time=0.0
            )
            
        except Exception as e:
            return ServiceStatus(
                name=service_name,
                status=ServiceStatusEnum.UNKNOWN,
                message=f"Error parsing RSS feed: {str(e)}",
                last_checked=datetime.now(),
                response_time=0.0,
                error=str(e)
            )