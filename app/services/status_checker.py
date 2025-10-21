"""Core status checking service for Service Status Monitor."""

import logging
import threading
import time
from typing import Dict, List
from datetime import datetime

from app.models import ServiceStatus, ServiceStatusEnum
from app.services.config_manager import ConfigManager
from app.services.adapters.base_adapter import BaseServiceAdapter
from app.services.adapters.statuspage_io import StatusPageIOAdapter
from app.services.adapters.custom_html import CustomHTMLAdapter
from app.services.adapters.api_adapter import APIAdapter
from app.services.adapters.ping_adapter import PingAdapter
from app.services.adapters.rss import RSSAdapter
from app.services.adapters.aws_hybrid import AWSHybridAdapter


logger = logging.getLogger(__name__)


class StatusChecker:
    """Core service for checking and caching service statuses."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize StatusChecker with configuration manager."""
        self.config_manager = config_manager
        self.status_cache: Dict[str, ServiceStatus] = {}
        self.cache_lock = threading.RLock()
        self.background_thread = None
        self.stop_event = threading.Event()
        
        # Initialize adapters
        timeout = self.config_manager.get_timeout()
        self.adapters = {
            'statuspage_io': StatusPageIOAdapter(timeout=timeout),
            'custom_html': CustomHTMLAdapter(timeout=timeout),
            'api_adapter': APIAdapter(timeout=timeout),
            'ping': PingAdapter(timeout=timeout),
            'rss': RSSAdapter(),
            'aws_hybrid': AWSHybridAdapter(timeout=timeout)
        }
    
    def check_service_status(self, service_config: Dict) -> ServiceStatus:
        """Check status for a single service."""
        adapter_name = service_config.get('adapter', 'statuspage_io')
        
        if adapter_name not in self.adapters:
            logger.error(f"Unknown adapter: {adapter_name}")
            return ServiceStatus(
                name=service_config['name'],
                status=ServiceStatusEnum.UNKNOWN,
                last_checked=datetime.now(),
                message="Unknown adapter type",
                response_time=0.0,
                error=f"Adapter '{adapter_name}' not found",
                category=service_config.get('category'),
                display_name=service_config.get('display_name'),
                url=service_config.get('url')
            )
        
        try:
            adapter = self.adapters[adapter_name]
            status = adapter.check_status(service_config)
            
            # Add category, display_name, and url information to the status
            status.category = service_config.get('category')
            status.display_name = service_config.get('display_name')
            status.url = service_config.get('url')
            
            # Cache the result
            with self.cache_lock:
                self.status_cache[service_config['name']] = status
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking status for {service_config['name']}: {e}")
            error_status = ServiceStatus(
                name=service_config['name'],
                status=ServiceStatusEnum.UNKNOWN,
                last_checked=datetime.now(),
                message="Status check failed",
                category=service_config.get('category'),
                display_name=service_config.get('display_name'),
                url=service_config.get('url'),
                response_time=0.0,
                error=str(e)
            )
            
            # Cache the error result
            with self.cache_lock:
                self.status_cache[service_config['name']] = error_status
            
            return error_status
    
    def check_all_services(self) -> Dict[str, ServiceStatus]:
        """Check status for all configured services."""
        services = self.config_manager.get_services()
        results = {}
        
        # Use threading for concurrent checks
        threads = []
        thread_results = {}
        
        def check_service_thread(service_config):
            """Thread function to check a single service."""
            try:
                result = self.check_service_status(service_config)
                thread_results[service_config['name']] = result
            except Exception as e:
                logger.error(f"Thread error checking {service_config['name']}: {e}")
                thread_results[service_config['name']] = ServiceStatus(
                    name=service_config['name'],
                    status=ServiceStatusEnum.UNKNOWN,
                    last_checked=datetime.now(),
                    message="Thread execution failed",
                    category='Uncategorized',
                    response_time=0.0,
                    error=str(e)
                )
        
        # Start threads for each service
        for service_config in services:
            thread = threading.Thread(
                target=check_service_thread,
                args=(service_config,),
                name=f"StatusCheck-{service_config['name']}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=60)  # 60 second timeout per thread
            if thread.is_alive():
                logger.warning(f"Thread {thread.name} timed out")
        
        # Collect results
        with self.cache_lock:
            results = dict(self.status_cache)
        
        logger.info(f"Completed status check for {len(results)} services")
        return results
    
    def get_all_statuses(self) -> Dict[str, ServiceStatus]:
        """Get all cached service statuses."""
        with self.cache_lock:
            return dict(self.status_cache)
    
    def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get cached status for a specific service."""
        with self.cache_lock:
            return self.status_cache.get(service_name)
    
    def start_periodic_checks(self) -> None:
        """Start background thread for periodic status checks."""
        if self.background_thread and self.background_thread.is_alive():
            logger.warning("Periodic checks already running")
            return
        
        self.stop_event.clear()
        self.background_thread = threading.Thread(
            target=self._periodic_check_loop,
            name="StatusChecker-Background",
            daemon=True
        )
        self.background_thread.start()
        logger.info("Started periodic status checks")
    
    def stop_periodic_checks(self) -> None:
        """Stop background thread for periodic status checks."""
        if self.background_thread and self.background_thread.is_alive():
            self.stop_event.set()
            self.background_thread.join(timeout=10)
            if self.background_thread.is_alive():
                logger.warning("Background thread did not stop gracefully")
            else:
                logger.info("Stopped periodic status checks")
    
    def _periodic_check_loop(self) -> None:
        """Background loop for periodic status checks."""
        logger.info("Starting periodic status check loop")
        
        # Initial check
        self.check_all_services()
        
        while not self.stop_event.is_set():
            try:
                refresh_interval = self.config_manager.get_refresh_interval()
                
                # Wait for the refresh interval or stop event
                if self.stop_event.wait(timeout=refresh_interval):
                    break  # Stop event was set
                
                # Perform status checks
                logger.info("Performing periodic status check")
                self.check_all_services()
                
            except Exception as e:
                logger.error(f"Error in periodic check loop: {e}")
                # Continue the loop even if there's an error
                time.sleep(30)  # Wait 30 seconds before retrying
        
        logger.info("Periodic status check loop stopped")
    
    def force_refresh(self) -> Dict[str, ServiceStatus]:
        """Force immediate refresh of all service statuses."""
        logger.info("Forcing immediate status refresh")
        return self.check_all_services()
    
    def clear_cache(self) -> None:
        """Clear the status cache."""
        with self.cache_lock:
            self.status_cache.clear()
        logger.info("Status cache cleared")