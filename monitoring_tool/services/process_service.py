from monitoring_tool import db


def list_processes() -> list[dict]:
    rows = db.query_all("SELECT id, tag_name, folder_path FROM processes ORDER BY tag_name")
    return [dict(row) for row in rows]


def add_process(tag_name: str, folder_path: str) -> None:
    db.execute(
        "INSERT INTO processes (tag_name, folder_path) VALUES (?, ?)",
        [tag_name, folder_path],
    )


def list_recipients() -> list[str]:
    rows = db.query_all("SELECT email FROM notification_recipients ORDER BY email")
    return [row["email"] for row in rows]


def add_recipient(email: str) -> None:
    db.execute("INSERT OR IGNORE INTO notification_recipients (email) VALUES (?)", [email])
