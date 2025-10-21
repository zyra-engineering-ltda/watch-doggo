#!/usr/bin/env python3
"""
Simple test script to validate the Service Status Monitor application.
"""

import sys
import json
import time
from app import create_app
from app.services.config_manager import ConfigManager
from app.services.status_checker import StatusChecker

def test_configuration():
    """Test configuration loading and validation."""
    print("Testing configuration management...")
    
    try:
        config_manager = ConfigManager('config/services.json')
        config = config_manager.load_config()
        
        assert 'services' in config, "Services not found in config"
        assert 'refresh_interval' in config, "Refresh interval not found in config"
        assert 'timeout' in config, "Timeout not found in config"
        
        services = config_manager.get_services()
        assert len(services) > 0, "No services configured"
        
        print(f"✓ Configuration loaded: {len(services)} services configured")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_status_checker():
    """Test status checking functionality."""
    print("Testing status checker...")
    
    try:
        config_manager = ConfigManager('config/services.json')
        status_checker = StatusChecker(config_manager)
        
        # Test single service check
        services = config_manager.get_services()
        if services:
            test_service = services[0]  # Test first service
            status = status_checker.check_service_status(test_service)
            
            assert hasattr(status, 'name'), "Status missing name"
            assert hasattr(status, 'status'), "Status missing status"
            assert hasattr(status, 'last_checked'), "Status missing last_checked"
            
            print(f"✓ Single service check: {status.name} -> {status.status.value}")
        
        # Test getting all statuses
        all_statuses = status_checker.get_all_statuses()
        print(f"✓ Status checker working: {len(all_statuses)} services checked")
        
        # Stop background checks
        status_checker.stop_periodic_checks()
        return True
        
    except Exception as e:
        print(f"✗ Status checker test failed: {e}")
        return False

def test_flask_app():
    """Test Flask application creation."""
    print("Testing Flask application...")
    
    try:
        app = create_app()
        
        # Test app configuration
        assert app.config_manager is not None, "Config manager not initialized"
        assert app.status_checker is not None, "Status checker not initialized"
        
        # Test with test client
        with app.test_client() as client:
            # Test dashboard route
            response = client.get('/')
            assert response.status_code == 200, f"Dashboard route failed: {response.status_code}"
            
            # Test API routes
            response = client.get('/api/status')
            assert response.status_code == 200, f"Status API failed: {response.status_code}"
            
            response = client.get('/api/config')
            assert response.status_code == 200, f"Config API failed: {response.status_code}"
            
            # Test API response format
            data = json.loads(response.data)
            assert 'success' in data, "API response missing success field"
            assert data['success'] == True, "API response indicates failure"
        
        print("✓ Flask application working correctly")
        
        # Stop background processes
        app.status_checker.stop_periodic_checks()
        return True
        
    except Exception as e:
        print(f"✗ Flask application test failed: {e}")
        return False

def test_adapters():
    """Test service adapters."""
    print("Testing service adapters...")
    
    try:
        from app.services.adapters.statuspage_io import StatusPageIOAdapter
        from app.services.adapters.custom_html import CustomHTMLAdapter
        from app.services.adapters.api_adapter import APIAdapter
        
        # Test adapter creation
        statuspage_adapter = StatusPageIOAdapter(timeout=10)
        html_adapter = CustomHTMLAdapter(timeout=10)
        api_adapter = APIAdapter(timeout=10)
        
        print("✓ All adapters created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Adapter test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Service Status Monitor - Application Tests")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_adapters,
        test_status_checker,
        test_flask_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Application is ready to use.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())