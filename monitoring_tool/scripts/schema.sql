CREATE TABLE IF NOT EXISTS processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL UNIQUE,
    folder_path TEXT NOT NULL,
    check_uc4_file INTEGER NOT NULL DEFAULT 0,
    scheduled_time TEXT,
    check_query TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS fatal_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL,
    event_time TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS process_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL,
    run_time TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL,
    reasons TEXT NOT NULL,
    uc4_status TEXT NOT NULL,
    check_type TEXT NOT NULL
);
