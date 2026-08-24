# PPPoE Monitoring System

A Django-based **PPPoE monitoring and network activity dashboard** designed to monitor PPPoE users, Access Concentrators (ACs), connection events, and real-time activity from MikroTik devices.

The system collects MikroTik PPPoE-related logs, processes them, identifies user activity, and presents the information through a web-based monitoring dashboard.

---

## 🚀 Features

* 📡 **PPPoE Session Monitoring**

  * Monitor active PPPoE sessions
  * Track login and logout activity
  * Record session history
  * Display connection duration

* 🖥️ **Access Concentrator Monitoring**

  * Monitor multiple Access Concentrators
  * Associate PPPoE sessions with their corresponding AC
  * Track activity coming from different AC devices

* 👤 **PPPoE Client Tracking**

  * Search clients using:

    * PPPoE username
    * MAC address

* View client activity and connection history

* 📜 **MikroTik Log Processing**

  * Collect PPPoE-related MikroTik logs
  * Parse and normalize log entries
  * Identify login/logout events
  * Extract usernames, MAC addresses, and other connection information
  * Prevent duplicate event records using log hashing

* ⚡ **Real-Time Monitoring**

  * Display recent PPPoE activity
  * Monitor connection events as they occur
  * Broadcast new events to the dashboard

* 🔎 **Raw Log Viewer**

  * View collected raw MikroTik logs
  * Inspect individual log entries
  * Useful for troubleshooting and debugging

* 📊 **Network Overview Dashboard**

  * Centralized monitoring interface
  * Active sessions
  * PPPoE events
  * Client information
  * Access Concentrator activity

---

## 🛠️ Technology Stack

| Technology        | Purpose                        |
| ----------------- | ------------------------------ |
| Python            | Backend programming            |
| Django            | Web framework                  |
| SQLite            | Development database           |
| Tailwind CSS      | User interface                 |
| MikroTik RouterOS | PPPoE / network infrastructure |
| Git & GitHub      | Version control                |
| GitHub Codespaces | Cloud development environment  |

---

## 📁 Project Structure

```text
project/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── monitor/
│   ├── admin.py
│   ├── models.py
│   ├── views.py
│   ├── log_collector.py
│   │
│   ├── management/
│   │   └── commands/
│   │
│   └── ...
│
├── raw_logs/
│   └── ...
│
├── cred.txt
├── db.sqlite3
├── manage.py
└── requirements.txt
```

---

## 🗄️ Main Database Models

### AccessConcentrator

Stores information about the monitored Access Concentrators.

### PPPoESession

Represents a PPPoE connection/session, including information such as:

* Username
* Access Concentrator
* Login time
* Logout time
* Connection duration
* Connection state

### PPPoEEvent

Stores PPPoE-related events detected from MikroTik logs.

Supported event types include:

```text
LOGIN
LOGOUT
CONNECTION
AUTH_FAILURE
OTHER
```

### PPPoEClient

Stores information associated with PPPoE clients and allows users to locate clients through identifiers such as usernames, MAC addresses, and IP addresses.

---

## ⚙️ How It Works

The monitoring system follows this general process:

```text
MikroTik Router
      │
      │ PPPoE Logs
      ▼
Log Collector
      │
      │ Parse / Normalize
      ▼
Event Detection
      │
      ├── LOGIN
      ├── LOGOUT
      ├── CONNECTION
      ├── AUTH_FAILURE
      └── OTHER
      │
      ▼
Django Database
      │
      ▼
Monitoring Dashboard
```

The log collector processes MikroTik logs and extracts useful information such as:

* PPPoE username
* MAC address
* Connection events
* Login timestamps
* Logout timestamps
* Access Concentrator information

Duplicate logs are handled using a generated log hash to prevent the same event from being stored multiple times.

---

## 🔐 Configuration

Sensitive credentials should **not** be committed to GitHub.

For example:

```text
cred.txt
.env
```

should contain sensitive information such as device credentials or Django secret keys.

Add sensitive files to `.gitignore`:

```gitignore
.env
cred.txt
*.pyc
__pycache__/
db.sqlite3
```

For production deployments, use environment variables or a proper secret-management system.

---

## ▶️ Running the Project

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
cd <PROJECT_DIRECTORY>
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
python manage.py migrate
```

Create an administrator account:

```bash
python manage.py createsuperuser
```

Start the Django development server:

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

---

## 📡 MikroTik Integration

The monitoring system is designed around MikroTik PPPoE logs.

The log collector analyzes relevant RouterOS log entries and attempts to associate events with existing clients and sessions.

The system also maintains active-session information so that login and logout events can be connected to the appropriate PPPoE session.

---

## 🔄 Development Workflow

The project can be developed using GitHub Codespaces.

Typical workflow:

```bash
git checkout main
git pull
```

Create a development branch:

```bash
git checkout -b feature/my-new-feature
```

After making changes:

```bash
git add .
git commit -m "Add new monitoring feature"
git push -u origin feature/my-new-feature
```

The feature branch can then be reviewed and merged into `main`.

After merging, an existing Codespace can be updated later with:

```bash
git checkout main
git pull
```

---

## 🧪 Development Status

This project is currently under active development.

### Current functionality

* [x] Django monitoring dashboard
* [x] Access Concentrator management
* [x] PPPoE session tracking
* [x] PPPoE event tracking
* [x] MikroTik log processing
* [x] Username detection
* [x] MAC address detection
* [x] Login/logout detection
* [x] Client search
* [x] Raw log viewer
* [x] Real-time event display
* [ ] Production deployment
* [ ] Advanced monitoring analytics
* [ ] Additional network-device integrations

---

## 🎯 Purpose

The main goal of this project is to provide a centralized monitoring interface for PPPoE activity and make it easier for network administrators to:

* Monitor active subscribers
* Identify connection problems
* Track PPPoE login/logout events
* Investigate authentication failures
* Search subscriber connection history
* Monitor multiple Access Concentrators
* Troubleshoot network activity through raw logs

---

## 👨‍💻 Developer

Developed by Jujiedso Programers/Network Engineers for network monitoring project using **Django + MikroTik + PPPoE**.

> Built for network monitoring, troubleshooting, and learning.
