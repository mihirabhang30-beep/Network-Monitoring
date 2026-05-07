# NetGuard — Network Monitoring Tool (IDS + IPS)

A full-stack web application for real-time network packet monitoring with built-in Intrusion Detection System (IDS) and Intrusion Prevention System (IPS).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js, Socket.IO |
| Backend | Python 3, Flask, Flask-SocketIO, Flask-Login |
| Database | MySQL (via Flask-SQLAlchemy + PyMySQL) |
| Packet Capture | Scapy |

## Features

- **Real-time Packet Monitoring** — Live capture with WebSocket streaming
- **IDS (Intrusion Detection)** — Detects port scans and high-traffic anomalies
- **IPS (Intrusion Prevention)** — Auto-blocks suspicious IPs via OS firewall
- **Authentication** — Login, registration, session handling
- **Role-Based Access** — Admin and Viewer roles
- **Packet History** — Searchable, filterable, paginated packet logs
- **Alert Management** — Severity-based alerts with resolve/delete actions
- **IP Block Management** — Manual and automatic blocking/unblocking
- **CSV Export** — Export packet data for analysis
- **Audit Logging** — Full trail of user actions
- **Admin Panel** — User management, session management, audit logs
- **Dashboard Charts** — Protocol distribution and top source IP visualizations

## Setup Instructions

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install and Start MySQL
Make sure MySQL is running, then create the database:
```sql
CREATE DATABASE network_monitor;
```

### 3. Configure Database (Optional)
Edit `config.py` if your MySQL credentials differ from defaults:
- Default user: `root`
- Default password: `password`
- Default database: `network_monitor`

### 4. Initialize Database
```bash
python init_db.py
```
This creates all 6 tables and a default admin user.

### 5. Run the Application
```bash
python app.py
```
Open: http://localhost:5000

### Default Login
- **Username:** admin
- **Password:** admin123

> **Note:** Run as Administrator for packet capture functionality (Scapy requires elevated privileges).

## Database Schema

| Table | Description |
|-------|------------|
| `users` | User accounts with roles |
| `capture_sessions` | Packet capture session metadata |
| `packets` | Captured network packets |
| `alerts` | IDS alert records |
| `blocked_ips` | IPS blocked IP addresses |
| `audit_logs` | User activity audit trail |

## Project Structure

```
network-monitor/
├── app.py              # Flask entry point + SocketIO
├── config.py           # App configuration
├── init_db.py          # Database initialization
├── models.py           # SQLAlchemy models (6 tables)
├── sniffer.py          # Scapy packet capture engine
├── requirements.txt    # Python dependencies
├── routes/
│   ├── auth.py         # Authentication routes
│   ├── dashboard.py    # Dashboard + API stats
│   ├── packets.py      # Packet history + search + CSV export
│   ├── alerts.py       # Alert management
│   ├── blocked.py      # IP block/unblock management
│   └── admin.py        # Admin panel
├── templates/          # Jinja2 HTML templates
│   ├── base.html, login.html, register.html
│   ├── dashboard.html, packets.html
│   ├── alerts.html, blocked_ips.html
│   └── admin/ (users, sessions, audit_logs)
└── static/
    ├── css/style.css   # Dark theme + glassmorphism
    └── js/             # Dashboard, charts, utilities
```

## License

Open-source project for educational purposes.
