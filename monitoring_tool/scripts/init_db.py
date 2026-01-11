from monitoring_tool import db


def main() -> None:
    db.init_db()
    print("Database initialized at", db.DB_PATH)


if __name__ == "__main__":
    main()
