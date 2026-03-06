# MonitoringTool

MonitoringTool is a simple Python/Flask application that monitors configured processes, checks for fatal events in SQLite, validates filesystem markers, and notifies recipients when failures occur.

## Features
- Configure processes with tag names and folder paths.
- Track fatal events in SQLite.
- Detect filesystem failures based on marker files.
- Review failed processes in the UI and send email notifications.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python -m monitoring_tool.app
```

Open http://localhost:5000 to configure processes and view reports.

### Marker Files
Each process folder is evaluated with two marker files:
- `success.flag` must exist for success.
- `failure.flag` triggers failure.

### Email Settings
Configure SMTP settings using environment variables:

```bash
export SMTP_HOST=localhost
export SMTP_PORT=25
export SMTP_SENDER=monitoring@example.com
```

Recipients can be managed from the Configure page.

### SQL Server Query Checks
Optional queries from **Configure Folder Paths** can be executed against a SQL Server database for check validation.

Set these environment variables to enable SQL Server execution:

```bash
export MONITORING_SQLSERVER_CONNECTION_STRING="DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:sql-host,1433;DATABASE=Monitoring;UID=user;PWD=pass;Encrypt=yes;TrustServerCertificate=yes"
export MONITORING_SQLSERVER_QUERY_TIMEOUT_SECONDS=30
```

If `MONITORING_SQLSERVER_CONNECTION_STRING` is not set, query checks run against the local SQLite monitoring database.


## Scripts
- `python scripts/init_db.py` initializes the SQLite database.
- `python scripts/seed_db.py` adds sample fatal events for testing.
monitorin