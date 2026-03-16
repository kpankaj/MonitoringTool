import logging

from monitoring_tool import db

logger = logging.getLogger(__name__)


def list_processes() -> list[dict]:
    logger.debug("Listing configured processes")
    rows = db.query_all(
        "SELECT id, tag_name, folder_path, check_uc4_file, uc4_folder_path, scheduled_time, check_query "
        "FROM processes WHERE folder_path != '' ORDER BY tag_name"
    )

    return [dict(row) for row in rows]


    
def list_tags() -> list[str]:
    rows = db.query_all("SELECT tag_name FROM processes ORDER BY tag_name")
    return [row["tag_name"] for row in rows]


def add_tag(tag_name: str) -> None:
    logger.info("Adding process tag %s", tag_name)
    db.execute(
        "INSERT INTO processes (tag_name, folder_path, check_uc4_file, uc4_folder_path) VALUES (?, '', 0, NULL)",
        [tag_name],
    )


def list_folder_configs() -> list[dict]:
    rows = db.query_all(
        "SELECT tag_name, folder_path, check_uc4_file, uc4_folder_path, scheduled_time, check_query "
        "FROM processes WHERE folder_path != '' ORDER BY tag_name"
    )
    return [dict(row) for row in rows]


def set_folder(
    tag_name: str,
    folder_path: str,
    check_uc4_file: bool,
    uc4_folder_path: str | None,
    scheduled_time: str | None,
    check_query: str | None,
) -> None:
    logger.info("Updating folder for tag %s to %s", tag_name, folder_path)
    db.execute(
        "UPDATE processes SET folder_path = ?, check_uc4_file = ?, uc4_folder_path = ?, scheduled_time = ?, check_query = ? "
        "WHERE tag_name = ?",
        [folder_path, int(check_uc4_file), uc4_folder_path, scheduled_time, check_query, tag_name],
    )


def clear_folder(tag_name: str) -> None:
    logger.info("Clearing folder configuration for tag %s", tag_name)
    db.execute(
        "UPDATE processes SET folder_path = '', check_uc4_file = 0, uc4_folder_path = NULL, scheduled_time = NULL, check_query = NULL "
        "WHERE tag_name = ?",
        [tag_name],
    )

def list_recipients() -> list[str]:
    rows = db.query_all("SELECT email FROM notification_recipients ORDER BY email")
    return [row["email"] for row in rows]


def add_recipient(email: str) -> None:
    logger.info("Adding recipient %s", email)
    db.execute("INSERT OR IGNORE INTO notification_recipients (email) VALUES (?)", [email])

def remove_recipient(email: str) -> None:
    logger.info("Removing recipient %s", email)
    db.execute("DELETE FROM notification_recipients WHERE email = ?", [email])
    
    
def remove_tag(tag_name: str) -> None:
    logger.info("Removing process tag %s", tag_name)
    db.execute("DELETE FROM processes WHERE tag_name = ?", [tag_name])

