"""Flask routes for Service Status Monitor."""

from flask import Blueprint, render_template, jsonify, current_app, request
import logging
from datetime import datetime
from app.webpush import add_subscription
import os

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


@main.route('/')
def dashboard():
    """Main dashboard route."""
    timezone = os.getenv("TIMEZONE", "UTC")
    return render_template('dashboard.html', timezone=timezone)


@main.route('/api/status')
def get_status():
    """API endpoint to get current service statuses."""
    try:
        status_checker = current_app.status_checker
        statuses = status_checker.get_all_statuses()
        
        # Convert ServiceStatus objects to dictionaries
        status_data = {}
        for service_name, status in statuses.items():
            status_data[service_name] = status.to_dict()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'services': status_data,
            'total_services': len(status_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting service statuses: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@main.route('/api/refresh', methods=['POST'])
def refresh_status():
    """API endpoint to manually refresh service statuses."""
    try:
        status_checker = current_app.status_checker
        statuses = status_checker.force_refresh()
        
        # Convert ServiceStatus objects to dictionaries
        status_data = {}
        for service_name, status in statuses.items():
            status_data[service_name] = status.to_dict()
        
        return jsonify({
            'success': True,
            'message': 'Status refresh completed',
            'timestamp': datetime.now().isoformat(),
            'services': status_data,
            'total_services': len(status_data)
        })
        
    except Exception as e:
        logger.error(f"Error refreshing service statuses: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@main.route('/api/config')
def get_config():
    """API endpoint to get current configuration."""
    try:
        config_manager = current_app.config_manager
        services = config_manager.get_services()
        
        return jsonify({
            'success': True,
            'refresh_interval': config_manager.get_refresh_interval(),
            'timeout': config_manager.get_timeout(),
            'services': services,
            'total_services': len(services)
        })
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/api/service/<service_name>')
def get_service_status(service_name):
    """API endpoint to get status for a specific service."""
    try:
        status_checker = current_app.status_checker
        status = status_checker.get_service_status(service_name)
        
        if status is None:
            return jsonify({
                'success': False,
                'error': f'Service {service_name} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'service': status.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting status for service {service_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/api/config/reload', methods=['POST'])
def reload_config():
    """API endpoint to reload configuration without restart."""
    try:
        config_manager = current_app.config_manager
        status_checker = current_app.status_checker
        
        # Reload configuration
        success = config_manager.reload_config()
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to reload configuration'
            }), 500
        
        # Clear status cache to force fresh checks with new config
        status_checker.clear_cache()
        
        # Get updated configuration
        services = config_manager.get_services()
        
        logger.info("Configuration reloaded successfully")
        
        return jsonify({
            'success': True,
            'message': 'Configuration reloaded successfully',
            'timestamp': datetime.now().isoformat(),
            'services_count': len(services),
            'refresh_interval': config_manager.get_refresh_interval(),
            'timeout': config_manager.get_timeout()
        })
        
    except Exception as e:
        logger.error(f"Error reloading configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/api/config/validate', methods=['POST'])
def validate_config():
    """API endpoint to validate configuration without applying it."""
    try:
        from flask import request
        
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
        
        config_data = request.get_json()
        config_manager = current_app.config_manager
        
        # Validate the provided configuration
        is_valid = config_manager._validate_config(config_data)
        
        if is_valid:
            return jsonify({
                'success': True,
                'message': 'Configuration is valid',
                'services_count': len(config_data.get('services', []))
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Configuration validation failed'
            }), 400
        
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/health')
def health_check():
    """Health check endpoint for production monitoring."""
    try:
        status_checker = current_app.status_checker
        config_manager = current_app.config_manager
        
        # Basic health checks
        services = config_manager.get_services()
        statuses = status_checker.get_all_statuses()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services_configured': len(services),
            'services_monitored': len(statuses),
            'version': '1.0.0'
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
    

@main.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json()
    if not data:
        return jsonify({"error": "no data"}), 400

    add_subscription(data)
    return jsonify({"success": True})

@main.route("/api/vapid-public-key")
def vapid_public_key():
    return jsonify({"key": os.environ.get("VAPID_PUBLIC_KEY", "")})

from flask import send_from_directory

from flask import send_from_directory

@main.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

