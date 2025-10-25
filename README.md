# WatchDoggo - Service Status Monitor

A Flask web application that monitors the status of various third-party services and displays their current operational status in a user-friendly dashboard.

## Features

- **Real-time Monitoring**: Automatically checks service status every 5 minutes (configurable)
- **Visual Dashboard**: Clean, responsive interface with Bootstrap styling
- **Multiple Adapters**: Supports StatusPage.io, custom HTML, and generic API formats
- **Status Indicators**: Color-coded status icons (green ✓, yellow ⚠, red ✗)
- **Detailed Information**: Response times, last check times, error messages
- **Auto-refresh**: Background updates without page reload
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices
- **Configuration Reload**: Update monitored services without restart

## Supported Services

The application comes pre-configured to monitor:

- GitHub
- Twilio
- Docker
- Google Maps
- Google APIs
- Google DNS
- Power BI
- Amazon Web Services (AWS)
- Microsoft Azure
- OpenAI

## Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the application**
   ```bash
   git clone git@github.com:zyra-engineering-ltda/watch-doggo.git
   cd watch-doggo
   ```

2. **Run the startup script**
   
   **Linux/macOS:**
   ```bash
   ./run.sh
   ```
   
   **Windows:**
   ```cmd
   run.bat
   ```

3. **Access the dashboard**
   
   Open your web browser and navigate to: `http://127.0.0.1:5000`

The startup script will automatically:
- Create a virtual environment
- Install dependencies
- Start the Flask application

## Manual Installation

If you prefer to set up manually:

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate.bat  # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application**
   ```bash
   python app.py
   ```

## Configuration

### Services Configuration

Edit `config/services.json` to add, remove, or modify monitored services:

```json
{
  "refresh_interval": 300,
  "timeout": 30,
  "services": [
    {
      "name": "github",
      "url": "https://www.githubstatus.com/api/v2/status.json",
      "adapter": "statuspage_io",
      "display_name": "GitHub"
    },
    {
      "name": "custom_service",
      "url": "https://example.com/status",
      "adapter": "custom_html",
      "display_name": "Custom Service",
      "selector": ".status-indicator",
      "success_text": "operational"
    }
  ]
}
```

### Configuration Options

- **refresh_interval**: How often to check services (seconds)
- **timeout**: HTTP request timeout (seconds)
- **services**: Array of service configurations

### Service Adapters

#### StatusPage.io Adapter
For services using StatusPage.io format:
```json
{
  "name": "service_name",
  "url": "https://status.example.com/api/v2/status.json",
  "adapter": "statuspage_io",
  "display_name": "Service Name"
}
```

#### Custom HTML Adapter
For services with custom HTML status pages:
```json
{
  "name": "service_name",
  "url": "https://example.com/status",
  "adapter": "custom_html",
  "display_name": "Service Name",
  "category": "infrastructure",
  "selector": ".status-indicator",
  "success_text": "operational",
  "degraded_text": "degraded",
  "down_text": "down"
}
```

For detailed parsing of individual services on a status page:
```json
{
  "name": "service_name",
  "url": "https://status.example.com/",
  "adapter": "custom_html",
  "display_name": "Service Name",
  "category": "infrastructure",
  "detailed_parsing": true,
  "service_selector": ".component, .service-item",
  "service_name_selector": ".name, .component-name",
  "service_status_selector": ".status, .component-status",
  "success_text": "operational"
}
```

#### Generic API Adapter
For services with custom JSON APIs:
```json
{
  "name": "service_name",
  "url": "https://api.example.com/status",
  "adapter": "api_adapter",
  "display_name": "Service Name",
  "status_path": "status.current",
  "status_mapping": {
    "ok": "operational",
    "issues": "degraded",
    "down": "down"
  }
}
```

#### Ping Adapter
For simple HTTP status checks (just checks if URL returns 200):
```json
{
  "name": "service_name",
  "url": "https://example.com",
  "adapter": "ping",
  "display_name": "Service Name",
  "category": "infrastructure"
}
```

### Service Categories

Services can be organized into categories for better dashboard organization. Add a `category` field to each service configuration:

```json
{
  "name": "service_name",
  "url": "https://example.com",
  "adapter": "ping",
  "display_name": "Service Name",
  "category": "crm"
}
```

The dashboard will automatically group services by category, making it easier to understand which services belong to which part of your infrastructure.

### Display Names

Each service should have a `display_name` field that provides a human-readable name for the dashboard and API responses:

```json
{
  "name": "github",
  "url": "https://www.githubstatus.com/api/v2/status.json",
  "adapter": "statuspage_io",
  "display_name": "GitHub",
  "category": "development"
}
```

The `display_name` is used in the dashboard interface and API responses, while `name` is used internally for identification.

### Status Page Links

Each service automatically includes a link to its status page in the dashboard. The URL from the service configuration is used to create clickable links on service cards:

```json
{
  "name": "github",
  "url": "https://www.githubstatus.com/api/v2/status.json",
  "adapter": "statuspage_io",
  "display_name": "GitHub",
  "category": "development"
}
```

Users can click the "View Status Page" button on each service card to open the full status page in a new tab.

## Environment Variables

You can customize the application using environment variables:

- `FLASK_HOST`: Host to bind to (default: 127.0.0.1)
- `FLASK_PORT`: Port to bind to (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: False)
- `SERVICES_CONFIG_PATH`: Path to services.json file
- `SECRET_KEY`: Flask secret key for sessions

Example:
```bash
export FLASK_HOST=0.0.0.0
export FLASK_PORT=8080
export FLASK_DEBUG=True
python app.py
```

## API Endpoints

The application provides REST API endpoints:

- `GET /api/status` - Get all service statuses
- `POST /api/refresh` - Force refresh all services
- `GET /api/config` - Get current configuration
- `GET /api/service/<name>` - Get specific service status
- `POST /api/config/reload` - Reload configuration
- `POST /api/config/validate` - Validate configuration

## Development

### Project Structure

```
service-status-monitor/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes.py                # Web routes and API endpoints
│   ├── models.py                # Data models
│   ├── services/
│   │   ├── status_checker.py    # Core status checking logic
│   │   ├── config_manager.py    # Configuration management
│   │   └── adapters/            # Service adapters
│   ├── static/                  # CSS, JavaScript, images
│   └── templates/               # HTML templates
├── config/
│   └── services.json           # Service configuration
├── app.py                      # Application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Adding New Service Adapters

1. Create a new adapter class in `app/services/adapters/`
2. Inherit from `BaseServiceAdapter`
3. Implement the `parse_response` method
4. Register the adapter in `StatusChecker.__init__`

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   - Change the port using `FLASK_PORT` environment variable
   - Or kill the process using the port: `lsof -ti:5000 | xargs kill`

2. **Configuration file not found**
   - Ensure `config/services.json` exists
   - Check the `SERVICES_CONFIG_PATH` environment variable

3. **Service not responding**
   - Check the service URL in configuration
   - Verify network connectivity
   - Check application logs for detailed error messages

4. **Permission denied on startup script**
   - Make the script executable: `chmod +x run.sh`

### Logs

Application logs are written to:
- Console output (stdout)
- `service_monitor.log` file

Check logs for detailed error information and debugging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Create an issue in the repository

## Changelog

### Version 0.0.1
- Initial release
- Support for StatusPage.io, HTML, and API adapters
- Real-time dashboard with auto-refresh
- Configuration management
- Responsive design
- REST API endpoints
