# WatchDoggo — Release History

### **v0.0.3** *(Latest)*
**Date:** 2025-11-03
**Type:** Enhancement Release

Adding PWA support and service worker registration

This will now allow the application to function as a Progressive Web App (PWA) with offline capabilities and push notifications.
Whenever a service's status changes, a push notification will be sent to subscribed users.

### **v0.0.2**

**Date:** 2025-10-23
**Type:** Maintenance Release

#### ✨ Improvements

* Added **favicon** and updated dashboard title for better branding.
* Introduced **base.html** layout for consistent page structure.
* Updated **run.sh** with correct execution permissions.

---

### **v0.0.1**

**Release:** First Public Release 🎉
**Date:** 2025-10-21
**Maintainer:** Zyra Engineering LLC (@zyra-engineering-ltda)

#### 🚀 Overview

WatchDoggo is an open-source, lightweight service-status monitor built with **Python + Flask**.
It pings your APIs, CRMs, and infrastructure endpoints and presents a clear, friendly uptime dashboard — so you know when something’s barking before it breaks 🐾.

#### ✨ Key Features

* **Service Health Checks** – Ping multiple APIs/endpoints from one JSON config (`config/services.json`).
* **Live Status Dashboard** – Responsive web UI for quick visibility.
* **Custom Logging** – Centralized per-service logs (`service_monitor.log`).
* **Configurable Intervals** – Different polling schedules per service.
* **JSON Configuration** – Simple, human-readable settings.
* **Lightweight Flask Backend** – Runs anywhere: macOS, Linux, Docker.
* **Extensible Adapters** – Built-in `ping`, `custom_html`, and `json` parsers.

#### ⚙️ Quick Setup

```bash
git clone https://github.com/zyra-engineering-ltda/watch-doggo.git
cd watch-doggo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run
```

`config/services.json` example:

```json
[
  {
    "name": "Active Prospect",
    "url": "https://status.activeprospect.com/",
    "adapter": "custom_html",
    "service_selector": ".component-inner-container"
  }
]
```

#### 🧱 Environment Variables

| Variable               | Default                | Description         |
| ---------------------- | ---------------------- | ------------------- |
| `FLASK_ENV`            | development            | Run mode            |
| `LOG_LEVEL`            | INFO                   | Logging verbosity   |
| `SERVICE_LOG_PATH`     | ./service_monitor.log  | Log file path       |
| `SERVICES_CONFIG_PATH` | ./config/services.json | Service config file |
| `SECRET_KEY`           | *(required)*           | Flask secret key    |

#### 🧑‍💻 Developer Notes

* Follow `CONTRIBUTING.md` for PR guidelines.
* Report security issues privately via `security@zyra.engineering`.
* Respect `CODE_OF_CONDUCT.md`.

#### 🛠️ Known Limitations

* Supports only HTML and JSON adapters.
* No database/persistent history (by design).
* Manual dashboard refresh (auto-update planned v1.1).

#### 🧭 Roadmap

* CLI / Docker image for headless monitoring
* Email / Slack alerts on failures
* Live uptime history charts
* Optional authentication + roles
* REST API for remote queries

#### ❤️ Acknowledgments

Huge thanks to early testers and the **Zyra Engineering** team for QA and feedback.

---

## 🔗 Follow Updates

[github.com/zyra-engineering-ltda/watch-doggo](https://github.com/zyra-engineering-ltda/watch-doggo)