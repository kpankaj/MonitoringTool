from monitoring_tool.db import init_db
from monitoring_tool.logging_setup import configure_logging

configure_logging()

__all__ = ["init_db", "configure_logging"]
