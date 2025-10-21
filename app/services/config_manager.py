"""Configuration manager for Service Status Monitor."""

import json
import logging
from typing import Dict, List, Optional
import os


logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages loading and validation of service configurations."""
    
    def __init__(self, config_path: str):
        """Initialize ConfigManager with path to configuration file."""
        self.config_path = config_path
        self._config = None
        self._last_modified = None
        
    def load_config(self) -> Dict:
        """Load and validate configuration from JSON file."""
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"Configuration file not found: {self.config_path}")
                return self._get_default_config()
            
            # Check if file has been modified
            current_modified = os.path.getmtime(self.config_path)
            if self._config is not None and current_modified == self._last_modified:
                return self._config
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Validate configuration
            if self._validate_config(config):
                self._config = config
                self._last_modified = current_modified
                logger.info(f"Configuration loaded successfully from {self.config_path}")
                return config
            else:
                logger.error("Configuration validation failed, using previous or default config")
                return self._config or self._get_default_config()
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return self._config or self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._config or self._get_default_config()
    
    def _validate_config(self, config: Dict) -> bool:
        """Validate configuration structure and required fields."""
        try:
            # Check required top-level fields
            required_fields = ['refresh_interval', 'timeout', 'services']
            for field in required_fields:
                if field not in config:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate refresh_interval and timeout are positive numbers
            if not isinstance(config['refresh_interval'], (int, float)) or config['refresh_interval'] <= 0:
                logger.error("refresh_interval must be a positive number")
                return False
            
            if not isinstance(config['timeout'], (int, float)) or config['timeout'] <= 0:
                logger.error("timeout must be a positive number")
                return False
            
            # Validate services array
            if not isinstance(config['services'], list):
                logger.error("services must be an array")
                return False
            
            # Validate each service configuration
            for i, service in enumerate(config['services']):
                if not self._validate_service_config(service, i):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False
    
    def _validate_service_config(self, service: Dict, index: int) -> bool:
        """Validate individual service configuration."""
        required_fields = ['name', 'url', 'adapter', 'display_name', 'category']
        
        for field in required_fields:
            if field not in service:
                logger.error(f"Service {index}: Missing required field '{field}'")
                return False
            
            if not isinstance(service[field], str) or not service[field].strip():
                logger.error(f"Service {index}: Field '{field}' must be a non-empty string")
                return False
        
        # Validate URL format (basic check)
        url = service['url']
        if not (url.startswith('http://') or url.startswith('https://')):
            logger.error(f"Service {index}: URL must start with http:// or https://")
            return False
        
        # Validate adapter type
        valid_adapters = ['statuspage_io', 'custom_html', 'api_adapter', 'ping', 'rss', 'aws_hybrid']
        if service['adapter'] not in valid_adapters:
            logger.error(f"Service {index}: Invalid adapter '{service['adapter']}'. Must be one of: {valid_adapters}")
            return False
        
        return True
    
    def _get_default_config(self) -> Dict:
        """Return default configuration when loading fails."""
        return {
            'refresh_interval': 300,
            'timeout': 30,
            'services': []
        }
    
    def get_services(self) -> List[Dict]:
        """Get list of service configurations."""
        config = self.load_config()
        return config.get('services', [])
    
    def get_refresh_interval(self) -> int:
        """Get refresh interval in seconds."""
        config = self.load_config()
        return config.get('refresh_interval', 300)
    
    def get_timeout(self) -> int:
        """Get request timeout in seconds."""
        config = self.load_config()
        return config.get('timeout', 30)
    
    def reload_config(self) -> bool:
        """Force reload configuration from file."""
        self._last_modified = None
        try:
            self.load_config()
            return True
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False