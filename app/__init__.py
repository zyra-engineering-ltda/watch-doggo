"""Flask application factory for Service Status Monitor."""

from flask import Flask
import logging
import os
import atexit
from pathlib import Path
from logging.handlers import RotatingFileHandler

from app.services.config_manager import ConfigManager
from app.services.status_checker import StatusChecker


def _configure_logging(app: Flask) -> None:
    """Configure logging safely for both dev and prod."""
    # Defaults, overridable by config and env
    log_level = os.getenv("LOG_LEVEL", app.config.get("LOG_LEVEL", "INFO")).upper()
    log_path = os.getenv(
        "SERVICE_LOG_PATH",
        app.config.get("LOG_FILE", os.path.join(os.getcwd(), "service_monitor.log"))
    )

    # Make sure directory exists
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))

    # Avoid duplicate handlers on reload
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    stream_h = logging.StreamHandler()
    stream_h.setFormatter(fmt)

    file_h = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3)
    file_h.setFormatter(fmt)

    root.addHandler(stream_h)
    root.addHandler(file_h)


def create_app(config_path=None):
    """Create and configure Flask application."""
    app = Flask(__name__)

    # ENV: development vs production
    flask_env = os.environ.get("FLASK_ENV", "development").lower()
    if flask_env == "production":
        from config.production import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
        app.config["DEBUG"] = True

    # Configure logging (after config is loaded)
    _configure_logging(app)

    # Resolve services config file
    default_cfg = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "services.json"))
    config_file = os.path.abspath(config_path or os.environ.get("SERVICES_CONFIG_PATH", default_cfg))
    app.config["SERVICES_CONFIG_PATH"] = config_file

    # Initialize services
    config_manager = ConfigManager(config_file)
    status_checker = StatusChecker(config_manager)
    app.config_manager = config_manager
    app.status_checker = status_checker

    # Start background checks once per process
    if not app.config.get("_STATUS_THREAD_STARTED", False):
        status_checker.start_periodic_checks()
        app.config["_STATUS_THREAD_STARTED"] = True

    # Clean shutdown for this process
    def cleanup():
        try:
            status_checker.stop_periodic_checks()
        except Exception:
            pass
    atexit.register(cleanup)

    # Routes
    from app.routes import main
    app.register_blueprint(main)

    # Errors
    @app.errorhandler(404)
    def not_found(_):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(_):
        return {"error": "Internal server error"}, 500

    return app
