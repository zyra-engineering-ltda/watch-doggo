"""AWS Hybrid adapter combining RSS and HTML parsing for comprehensive status monitoring."""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Optional, List
import re
import requests
from bs4 import BeautifulSoup

from app.services.adapters.base_adapter import BaseServiceAdapter
from app.models import ServiceStatus, ServiceStatusEnum


class AWSHybridAdapter(BaseServiceAdapter):
    """Hybrid adapter for AWS that combines RSS feed history with real-time HTML status."""
    
    def __init__(self, timeout: int = 30):
        super().__init__(timeout)
    
    def parse_response(self, response: requests.Response, service_config: Dict[str, Any]) -> ServiceStatus:
        """Parse AWS status using both RSS and HTML sources."""
        service_name = service_config.get("name", "aws")
        display_name = service_config.get("display_name", "AWS")
        region = service_config.get("region", "us-east-1")
        
        try:
            # First, get current status from HTML health dashboard
            current_status = self._get_current_status_from_html(region, service_config)
            
            # Then, get historical context from RSS if available
            rss_url = service_config.get("rss_url")
            historical_context = None
            if rss_url:
                historical_context = self._get_historical_context_from_rss(rss_url, region, service_config)
            
            # Combine both sources for comprehensive status
            return self._combine_status_sources(
                current_status, 
                historical_context, 
                service_name, 
                display_name, 
                region,
                service_config
            )
            
        except Exception as e:
            return ServiceStatus(
                name=service_name,
                status=ServiceStatusEnum.UNKNOWN,
                message=f"Error checking AWS status: {str(e)}",
                last_checked=datetime.now(),
                response_time=0.0,
                error=str(e)
            )
    
    def _get_current_status_from_html(self, region: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get current AWS status from the health dashboard HTML."""
        try:
            # Get the main AWS health status page
            health_url = "https://health.aws.amazon.com/health/status"
            response = self.session.get(health_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for severity and impact indicators
            current_status = {
                'total_impacted': 0,
                'severity_issues': [],
                'region_status': 'operational',
                'global_issues': [],
                'raw_indicators': []
            }
            
            # Get all text content
            page_text = soup.get_text()
            
            # Enhanced search patterns for AWS status indicators
            impact_patterns = [
                r'impacted\s*\((\d+)\s*services?\)',
                r'(\d+)\s*services?\s*impacted',
                r'severity.*?impacted.*?(\d+)',
                r'(\d+)\s*affected\s*services?',
                r'issues\s*affecting\s*(\d+)\s*services?',
                r'(\d+)\s*services?\s*experiencing\s*issues'
            ]
            
            # Search for impact numbers
            for pattern in impact_patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    try:
                        count = int(match.group(1))
                        if count > current_status['total_impacted']:
                            current_status['total_impacted'] = count
                            current_status['raw_indicators'].append(match.group(0))
                    except (ValueError, IndexError):
                        continue
            
            # Look for severity and status keywords
            severity_keywords = [
                'high severity', 'medium severity', 'low severity',
                'critical', 'major outage', 'service disruption',
                'degraded performance', 'intermittent issues',
                'connectivity issues', 'elevated error rates'
            ]
            
            for keyword in severity_keywords:
                if keyword in page_text.lower():
                    current_status['severity_issues'].append(keyword)
            
            # Look for region-specific issues (simplified approach)
            region_keywords = [region, 'us-east-1', 'us-west-2', 'eu-west-1']
            issue_keywords = ['outage', 'degraded', 'issues', 'problems', 'disruption', 'unavailable']
            
            for region_kw in region_keywords:
                for issue_kw in issue_keywords:
                    # Simple text search without complex regex
                    if region_kw in page_text.lower() and issue_kw in page_text.lower():
                        # Check if they appear close to each other (within 100 characters)
                        region_pos = page_text.lower().find(region_kw)
                        issue_pos = page_text.lower().find(issue_kw)
                        if abs(region_pos - issue_pos) < 100:
                            current_status['region_status'] = 'degraded'
                            current_status['global_issues'].append(f'{region_kw} {issue_kw}')
                            break
            
            # Look for JavaScript variables or data attributes that might contain status
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_text = script.string
                    # Look for status data in JavaScript
                    js_patterns = [
                        r'impacted["\']?\s*:\s*(\d+)',
                        r'affected["\']?\s*:\s*(\d+)',
                        r'services["\']?\s*:\s*(\d+)',
                        r'count["\']?\s*:\s*(\d+)'
                    ]
                    
                    for pattern in js_patterns:
                        matches = re.finditer(pattern, script_text, re.IGNORECASE)
                        for match in matches:
                            try:
                                count = int(match.group(1))
                                if count > 0 and count < 1000:  # Reasonable service count
                                    current_status['total_impacted'] = max(current_status['total_impacted'], count)
                                    current_status['raw_indicators'].append(f'JS: {match.group(0)}')
                            except (ValueError, IndexError):
                                continue
            
            # Look for meta tags or data attributes
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                content = meta.get('content', '')
                if any(word in content.lower() for word in ['impacted', 'affected', 'outage', 'degraded']):
                    current_status['global_issues'].append(f'Meta: {content[:100]}')
            
            # Look for specific AWS service mentions with status
            aws_services = service_config.get('services', [])
            for service in aws_services:
                if service.lower() in page_text.lower():
                    # Check for issues near service mentions
                    service_pos = page_text.lower().find(service.lower())
                    nearby_text = page_text[max(0, service_pos-50):service_pos+100].lower()
                    if any(issue in nearby_text for issue in ['degraded', 'outage', 'issues', 'unavailable', 'down']):
                        current_status['severity_issues'].append(f'{service} issues detected')
            
            # Fallback: Look for general AWS status indicators
            general_indicators = [
                'service health dashboard', 'current status', 'service status',
                'operational status', 'system status'
            ]
            
            for indicator in general_indicators:
                if indicator in page_text.lower():
                    current_status['global_issues'].append(f'Status page active: {indicator}')
            
            # If we found any indicators but no specific issues, it might mean services are operational
            if not current_status['total_impacted'] and not current_status['severity_issues']:
                # Check if the page mentions "operational" or "healthy"
                if any(word in page_text.lower() for word in ['operational', 'healthy', 'normal', 'good']):
                    current_status['region_status'] = 'operational'
            
            return current_status
            
        except Exception as e:
            # Fallback: try to get basic connectivity status
            return {
                'total_impacted': 0,
                'severity_issues': [],
                'region_status': 'unknown',
                'global_issues': [f"Error parsing status: {str(e)}"],
                'error': str(e)
            }
    
    def _get_historical_context_from_rss(self, rss_url: str, region: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get historical context from RSS feed."""
        try:
            response = self.session.get(rss_url, timeout=self.timeout)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            channel = root.find('channel')
            if channel is None:
                return {'recent_incidents': []}
            
            items = channel.findall('item')
            target_services = service_config.get("services", [])
            
            recent_incidents = []
            for item in items[:10]:  # Check last 10 incidents
                title = item.find('title')
                description = item.find('description')
                
                if title is None or description is None:
                    continue
                
                title_text = title.text or ""
                desc_text = description.text or ""
                
                # Parse incident
                incident_info = self._parse_rss_incident(title_text, desc_text, region, target_services)
                if incident_info and incident_info['status'] != 'resolved':
                    recent_incidents.append(incident_info)
            
            return {'recent_incidents': recent_incidents}
            
        except Exception as e:
            return {'recent_incidents': [], 'error': str(e)}
    
    def _parse_rss_incident(self, title: str, description: str, region: str, target_services: list) -> Optional[Dict[str, Any]]:
        """Parse individual RSS incident."""
        try:
            # Extract status
            status_match = re.search(r'\[(.*?)\]', title)
            incident_status = status_match.group(1).lower() if status_match else 'ongoing'
            
            # Skip resolved incidents
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
            
            # Determine severity
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
            
        except Exception:
            return None
    
    def _combine_status_sources(self, current_status: Dict[str, Any], historical_context: Optional[Dict[str, Any]], 
                               service_name: str, display_name: str, region: str, service_config: Dict[str, Any]) -> ServiceStatus:
        """Combine current HTML status with historical RSS context."""
        
        # Determine overall status based on current conditions
        total_impacted = current_status.get('total_impacted', 0)
        severity_issues = current_status.get('severity_issues', [])
        region_status = current_status.get('region_status', 'operational')
        global_issues = current_status.get('global_issues', [])
        
        # Get recent incidents from RSS
        recent_incidents = []
        if historical_context:
            recent_incidents = historical_context.get('recent_incidents', [])
        
        # Determine status priority: Current HTML status > RSS incidents
        if total_impacted > 50:
            status = ServiceStatusEnum.DOWN
            message = f"Major service disruption: {total_impacted} services impacted"
        elif total_impacted > 10:
            status = ServiceStatusEnum.DEGRADED
            message = f"Service issues: {total_impacted} services impacted"
        elif total_impacted > 0:
            status = ServiceStatusEnum.DEGRADED
            message = f"Limited impact: {total_impacted} services affected"
        elif severity_issues:
            status = ServiceStatusEnum.DEGRADED
            message = f"Severity issues detected: {', '.join(severity_issues[:2])}"
        elif region_status == 'degraded':
            status = ServiceStatusEnum.DEGRADED
            message = f"Regional issues detected in {region}"
        elif global_issues:
            status = ServiceStatusEnum.DEGRADED
            message = f"Service monitoring detected issues"
        elif recent_incidents:
            # Check RSS incidents for ongoing issues
            critical_incidents = [i for i in recent_incidents if i['severity'] == 'high']
            if critical_incidents:
                status = ServiceStatusEnum.DOWN
                affected_services = [i['service'] for i in critical_incidents]
                message = f"Critical incidents: {', '.join(affected_services[:3])}"
            else:
                status = ServiceStatusEnum.DEGRADED
                affected_services = [i['service'] for i in recent_incidents]
                message = f"Service incidents: {', '.join(affected_services[:3])}"
        else:
            status = ServiceStatusEnum.OPERATIONAL
            message = f"All monitored services operational in {region}"
        
        # Add impact count to message if significant
        if total_impacted > 0:
            if "impacted" not in message.lower():
                message += f" ({total_impacted} services impacted)"
        
        return ServiceStatus(
            name=service_name,
            status=status,
            message=message,
            last_checked=datetime.now(),
            response_time=0.0
        )