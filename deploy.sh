#!/bin/bash

# LeadConduit Monitor Production Deployment Script

set -e

echo "🚀 Deploying LeadConduit Monitor to Production..."

# Configuration
APP_DIR="/opt/leadconduit-monitor"
SERVICE_NAME="leadconduit-monitor"
NGINX_CONF="/etc/nginx/sites-available/leadconduit-monitor"

# Create application directory
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
echo "📁 Copying application files..."
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' . $APP_DIR/

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create log directory
sudo mkdir -p /var/log/leadconduit-monitor
sudo chown www-data:www-data /var/log/leadconduit-monitor

# Install systemd service
echo "⚙️ Installing systemd service..."
sudo cp leadconduit-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Install nginx configuration
echo "🌐 Setting up Nginx..."
sudo cp nginx-leadconduit-monitor.conf $NGINX_CONF
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo nginx -t

# Set permissions
sudo chown -R www-data:www-data $APP_DIR
sudo chmod +x $APP_DIR/wsgi.py

# Start services
echo "🔄 Starting services..."
sudo systemctl restart $SERVICE_NAME
sudo systemctl restart nginx

# Check status
echo "✅ Checking service status..."
sudo systemctl status $SERVICE_NAME --no-pager
curl -f http://localhost:8000/health || echo "⚠️ Health check failed"

echo "🎉 Deployment complete!"
echo "📊 Monitor should be available at: https://your-domain.com"
echo "📝 Check logs with: sudo journalctl -u $SERVICE_NAME -f"