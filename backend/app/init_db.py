"""
Initialize the database:
1) Create the Postgres database if it doesn't exist.
2) Create tables from SQLAlchemy models.
"""

from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy import create_engine

from .core.database import engine as app_engine
from .core.config import settings
from .models.db_models import Base


def ensure_database_exists() -> None:
    # Parse the DSN string into a URL object
    url = make_url(settings.DATABASE_URL)

    # Build an admin URL pointing to the default 'postgres' DB
    admin_url = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database="postgres",
    )

    # Use autocommit for CREATE DATABASE
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    db_name = url.database

    with admin_engine.connect() as conn:
        # Check if DB exists
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": db_name},
        ).scalar() is not None

        if not exists:
            # CREATE DATABASE must be run outside of a transaction
            conn.exec_driver_sql(f"CREATE DATABASE \"{db_name}\"")
            print(f"Created database '{db_name}'.")
        else:
            print(f"Database '{db_name}' already exists.")


def create_tables() -> None:
    Base.metadata.create_all(bind=app_engine)
    print("Database tables created/verified.")


if __name__ == "__main__":
    ensure_database_exists()
    create_tables()
