# database.py
# This file handles the database connection and configuration.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database file name. This will create a file named 'telemetry.db' in your project directory.
SQLALCHEMY_DATABASE_URL = "sqlite:///./telemetry.db"

# Create the SQLAlchemy engine.
# connect_args={"check_same_thread": False} is needed for SQLite when using multiple threads,
# which FastAPI does by default. It's not needed for other databases like PostgreSQL.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class.
# Each instance of SessionLocal will be a database session.
# The `autocommit=False` means that changes are not automatically committed to the database.
# The `autoflush=False` means that objects are not automatically flushed to the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models.
# This Base class will be inherited by our SQLAlchemy models.
Base = declarative_base()