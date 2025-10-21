"""Custom HTML adapter for service status checking."""

import logging
from typing import Dict
import requests
from bs4 import BeautifulSoup

from app.models import ServiceStatus, ServiceStatusEnum
from app.services.adapters.base_adapter import BaseServiceAdapter


logger = logging.getLogger(__name__)


class CustomHTMLAdapter(BaseServiceAdapter):
    """Adapter for services with custom HTML status pages."""
    
    def parse_response(self, response: requests.Response, config: Dict) -> ServiceStatus:
        """Parse custom HTML response using CSS selectors."""
        service_name = config['name']
        
        try:
            # Ensure we got a successful response
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get configuration for HTML parsing
            selector = config.get('selector', '.status')
            success_text = config.get('success_text', 'operational').lower()
            degraded_text = config.get('degraded_text', 'degraded').lower()
            down_text = config.get('down_text', 'down').lower()
            
            # Check if this is a detailed service parsing configuration
            detailed_parsing = config.get('detailed_parsing', False)
            service_selector = config.get('service_selector', '.component, .service-item')
            service_name_selector = config.get('service_name_selector', '.name, .service-name')
            service_status_selector = config.get('service_status_selector', '.component-status')
            
            # Check if we should do detailed service parsing
            if detailed_parsing:
                return self._parse_detailed_services(soup, config, service_name, service_selector, 
                                                   service_name_selector, service_status_selector)
            
            # Try multiple selectors if provided as comma-separated
            selectors = [s.strip() for s in selector.split(',')]
            status_element = None
            status_text = ""
            
            for sel in selectors:
                status_element = soup.select_one(sel)
                if status_element:
                    break
            
            if not status_element:
                # Fallback: look for common status indicators in the page
                fallback_selectors = [
                    '[class*="status"]', '[id*="status"]', 
                    '[class*="health"]', '[id*="health"]',
                    '.service-status', '.system-status', '.operational', '.status'
                    '[data-status]', '[data-health]'
                ]
                
                for fallback_sel in fallback_selectors:
                    status_element = soup.select_one(fallback_sel)
                    if status_element:
                        logger.info(f"Found status using fallback selector {fallback_sel} for {service_name}")
                        break
            
            if status_element:
                # Extract text content and normalize
                status_text = status_element.get_text(strip=True).lower()
                
                # Also check for data attributes that might contain status
                for attr in ['data-status', 'data-health', 'class', 'title']:
                    if status_element.get(attr):
                        status_text += " " + str(status_element.get(attr)).lower()
            else:
                # Last resort: search entire page for status keywords
                page_text = soup.get_text().lower()
                if any(word in page_text for word in ['all systems operational', 'all services operational', 'healthy']):
                    status_text = "operational"
                elif any(word in page_text for word in ['service disruption', 'degraded', 'partial outage']):
                    status_text = "degraded"
                elif any(word in page_text for word in ['major outage', 'service unavailable', 'down']):
                    status_text = "down"
                else:
                    logger.warning(f"No status element found for {service_name} using any selector")
                    return self._get_fallback_status(response, service_name)
            
            # Determine status based on text content
            if success_text in status_text:
                status = ServiceStatusEnum.OPERATIONAL
                message = "Service is operational"
            elif degraded_text in status_text:
                status = ServiceStatusEnum.DEGRADED
                message = "Service is experiencing issues"
            elif down_text in status_text or 'offline' in status_text or 'unavailable' in status_text:
                status = ServiceStatusEnum.DOWN
                message = "Service is down"
            else:
                # Enhanced keyword detection for various status page formats
                operational_keywords = [
                    'ok', 'good', 'normal', 'online', 'up', 'healthy', 'operational', 
                    'running', 'available', 'active', 'green', 'all systems', 'no issues'
                ]
                degraded_keywords = [
                    'issue', 'problem', 'slow', 'partial', 'degraded', 'warning', 
                    'yellow', 'limited', 'reduced', 'investigating', 'advisory'
                ]
                down_keywords = [
                    'error', 'fail', 'outage', 'maintenance', 'down', 'offline', 
                    'unavailable', 'red', 'major', 'critical', 'service disruption'
                ]
                
                if any(word in status_text for word in operational_keywords):
                    status = ServiceStatusEnum.OPERATIONAL
                    message = "Service appears operational"
                elif any(word in status_text for word in degraded_keywords):
                    status = ServiceStatusEnum.DEGRADED
                    message = "Service may have issues"
                elif any(word in status_text for word in down_keywords):
                    status = ServiceStatusEnum.DOWN
                    message = "Service appears to be down"
                else:
                    status = ServiceStatusEnum.UNKNOWN
                    message = f"Status unclear: {status_text[:50]}"
            
            return ServiceStatus(
                name=service_name,
                status=status,
                last_checked=None,  # Will be set by base adapter
                message=message,
                response_time=0.0  # Will be set by base adapter
            )
            
        except Exception as e:
            logger.error(f"Error parsing HTML response for {service_name}: {e}")
            return self._get_fallback_status(response, service_name)
    
    def _parse_detailed_services(self, soup: BeautifulSoup, config: Dict, service_name: str,
                                service_selector: str, service_name_selector: str, 
                                service_status_selector: str) -> ServiceStatus:
        """Parse individual services from a detailed status page."""
        try:
            # Find all service components
            service_elements = soup.select(service_selector)
            
            if not service_elements:
                logger.warning(f"No service elements found for {service_name} using selector: {service_selector}")
                return self._get_fallback_status_detailed(service_name, "No services found")
            
            # Analyze each service
            services_status = []
            problem_services = []
            
            for service_elem in service_elements:
                # Get service name
                name_elem = service_elem.select_one(service_name_selector)
                if not name_elem:
                    continue
                
                svc_name = name_elem.get_text(strip=True)
                
                # Get service status
                status_elem = service_elem.select_one(service_status_selector)
                if not status_elem:
                    # Try to find status in the service element itself
                    status_elem = service_elem
                
                status_text = status_elem.get_text(strip=True).lower()
                
                # Check for data-component-status attribute (priority)
                data_status = service_elem.get('data-component-status', '').lower()
                if data_status:
                    status_text = data_status + " " + status_text
                
                # Also check for CSS classes that might indicate status
                status_classes = ' '.join(service_elem.get('class', [])).lower()
                status_text += " " + status_classes
                
                # Determine service status
                if any(word in status_text for word in ['operational', 'ok', 'good', 'normal', 'up', 'healthy', 'green']):
                    svc_status = 'operational'
                elif any(word in status_text for word in ['degraded', 'partial', 'warning', 'yellow', 'issue']):
                    svc_status = 'degraded'
                    problem_services.append(f"{svc_name} (degraded)")
                elif any(word in status_text for word in ['down', 'outage', 'offline', 'red', 'critical', 'major']):
                    svc_status = 'down'
                    problem_services.append(f"{svc_name} (down)")
                else:
                    svc_status = 'unknown'
                    problem_services.append(f"{svc_name} (unknown)")
                
                services_status.append({
                    'name': svc_name,
                    'status': svc_status,
                    'text': status_text[:50]
                })
            
            # Determine overall status
            if not problem_services:
                overall_status = ServiceStatusEnum.OPERATIONAL
                message = f"All {len(services_status)} services operational"
            else:
                # Check severity of problems
                down_services = [s for s in problem_services if 'down' in s]
                degraded_services = [s for s in problem_services if 'degraded' in s]
                
                if down_services:
                    overall_status = ServiceStatusEnum.DOWN
                    message = f"Services down: {', '.join(down_services[:3])}"
                    if len(down_services) > 3:
                        message += f" and {len(down_services) - 3} more"
                elif degraded_services:
                    overall_status = ServiceStatusEnum.DEGRADED
                    message = f"Services degraded: {', '.join(degraded_services[:3])}"
                    if len(degraded_services) > 3:
                        message += f" and {len(degraded_services) - 3} more"
                else:
                    overall_status = ServiceStatusEnum.UNKNOWN
                    message = f"Issues with: {', '.join(problem_services[:3])}"
            
            logger.info(f"Detailed parsing for {service_name}: {len(services_status)} services, {len(problem_services)} with issues")
            
            return ServiceStatus(
                name=service_name,
                status=overall_status,
                last_checked=None,  # Will be set by base adapter
                message=message,
                response_time=0.0  # Will be set by base adapter
            )
            
        except Exception as e:
            logger.error(f"Error in detailed parsing for {service_name}: {e}")
            return self._get_fallback_status_detailed(service_name, f"Parsing error: {str(e)}")
    
    def _get_fallback_status_detailed(self, service_name: str, error_msg: str) -> ServiceStatus:
        """Get fallback status for detailed parsing errors."""
        return ServiceStatus(
            name=service_name,
            status=ServiceStatusEnum.UNKNOWN,
            last_checked=None,
            message=f"Could not parse detailed status: {error_msg}",
            response_time=0.0
        )