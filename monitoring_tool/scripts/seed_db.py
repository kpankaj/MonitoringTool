from monitoring_tool import db


SAMPLE_EVENTS = [
    ("billing-job", "Billing run failed with exit code 2"),
    ("inventory-sync", "Inventory sync timeout"),
]


def main() -> None:
    db.init_db()
    for tag_name, description in SAMPLE_EVENTS:
        db.execute(
            "INSERT INTO fatal_events (tag_name, description) VALUES (?, ?)",
            [tag_name, description],
        )
    print("Inserted sample fatal events.")


if __name__ == "__main__":
    main()
