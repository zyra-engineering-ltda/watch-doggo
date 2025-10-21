# /var/www/html/apps/itd-service-status/wsgi.py
#!/usr/bin/env python3
import os
import sys
from app import create_app

APP_DIR = os.path.dirname(__file__)
VENV_BIN = os.path.join(APP_DIR, ".venv", "bin")

# Ensure project import works and subprocess PATH includes venv
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
os.environ["PATH"] = VENV_BIN + os.pathsep + os.environ.get("PATH", "")

# ---- Production env vars (tweak as needed) ----
os.environ.setdefault("FLASK_ENV", "production")

# If your app expects a config file path, set it here (adjust if different):
os.environ.setdefault("SERVICES_CONFIG_PATH", os.path.join(APP_DIR, "config", "services.json"))

# Optional: direct your app logs to a safe, writable place
os.environ.setdefault("SERVICE_LOG_PATH", "/var/log/itd-service-status/service_monitor.log")

# ---- Create the Flask app and expose as 'application' ----
from app import create_app  # your factory
application = create_app(os.environ.get("SERVICES_CONFIG_PATH"))