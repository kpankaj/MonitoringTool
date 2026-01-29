from monitoring_tool import db


def list_processes() -> list[dict]:
    rows = db.query_all(
        "SELECT id, tag_name, folder_path, check_uc4_file, scheduled_time, check_query "
        "FROM processes WHERE folder_path != '' ORDER BY tag_name"
    )

    return [dict(row) for row in rows]


    
def list_tags() -> list[str]:
    rows = db.query_all("SELECT tag_name FROM processes ORDER BY tag_name")
    return [row["tag_name"] for row in rows]


def add_tag(tag_name: str) -> None:
    db.execute(
        "INSERT INTO processes (tag_name, folder_path, check_uc4_file) VALUES (?, '', 0)",
        [tag_name],
    )


def list_folder_configs() -> list[dict]:
    rows = db.query_all(
        "SELECT tag_name, folder_path, check_uc4_file, scheduled_time, check_query "
        "FROM processes WHERE folder_path != '' ORDER BY tag_name"
    )
    return [dict(row) for row in rows]


def set_folder(
    tag_name: str,
    folder_path: str,
    check_uc4_file: bool,
    scheduled_time: str | None,
    check_query: str | None,
) -> None:
    db.execute(
        "UPDATE processes SET folder_path = ?, check_uc4_file = ?, scheduled_time = ?, check_query = ? "
        "WHERE tag_name = ?",
        [folder_path, int(check_uc4_file), scheduled_time, check_query, tag_name],
    )


def clear_folder(tag_name: str) -> None:
    db.execute(
        "UPDATE processes SET folder_path = '', check_uc4_file = 0, scheduled_time = NULL, check_query = NULL "
        "WHERE tag_name = ?",
        [tag_name],
    )

def list_recipients() -> list[str]:
    rows = db.query_all("SELECT email FROM notification_recipients ORDER BY email")
    return [row["email"] for row in rows]


def add_recipient(email: str) -> None:
    db.execute("INSERT OR IGNORE INTO notification_recipients (email) VALUES (?)", [email])

def remove_recipient(email: str) -> None:
    db.execute("DELETE FROM notification_recipients WHERE email = ?", [email])
    
    
def remove_tag(tag_name: str) -> None:
    db.execute("DELETE FROM processes WHERE tag_name = ?", [tag_name])

