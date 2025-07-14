# models.py
# This file defines the SQLAlchemy ORM models (for database interaction)
# and Pydantic models (for data validation and API request/response schemas).

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime

#func allows to use database functions like NOW(),SUM()
# Import the Base from database.py
from database import Base

# --- SQLAlchemy ORM Model ---
# This class defines the structure of the 'telemetry_data' table in the database.
class TelemetryData(Base):
    __tablename__ = "telemetry_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True) # Automatically set to current UTC time
    device_id = Column(String, index=True)
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    unit = Column(String, nullable=True) # Unit can be optional

# --- SQLAlchemy ORM Model for Anomaly Data ---
class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    telemetry_id = Column(Integer, ForeignKey("telemetry_data.id"), unique=True, index=True) # Link to the telemetry record
    device_id = Column(String, index=True)
    metric_name = Column(String, index=True)
    metric_value = Column(Float) # The value that was anomalous
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    anomaly_type = Column(String, nullable=True) # e.g., "High Z-score", "Sudden Drop"
    threshold_used = Column(Float, nullable=True) # The threshold that triggered the anomaly

# --- Pydantic Models for FastAPI ---
# These models define the data structure for API requests and responses,
# providing data validation and automatic documentation.

class TelemetryDataCreate(BaseModel):
    """
    Pydantic model for creating new telemetry data records.
    Used for the POST request body.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow) # Default to current UTC time if not provided
    device_id: str = Field(..., min_length=1, description="Unique identifier for the device.")
    metric_name: str = Field(..., min_length=1, description="Name of the telemetry metric (e.g., 'temperature').")
    metric_value: float = Field(..., description="Numerical value of the metric.")
    unit: str | None = Field(None, description="Unit of the metric (e.g., 'Celsius', 'Volts').")

    class Config:
        # Example for OpenAPI documentation
        json_schema_extra = {
            "example": {
                "timestamp": "2023-10-27T10:00:00Z",
                "device_id": "sensor-001",
                "metric_name": "temperature",
                "metric_value": 25.5,
                "unit": "Celsius"
            }
        }

class TelemetryDataResponse(BaseModel):
    """
    Pydantic model for returning telemetry data records.
    Used for API responses, includes the generated 'id'.
    """
    id: int
    timestamp: datetime
    device_id: str
    metric_name: str
    metric_value: float
    unit: str | None

    class Config:
        # This tells Pydantic to read data even if it's not a dict,
        # which is useful when mapping SQLAlchemy ORM objects.
        from_attributes = True


# --- New Pydantic Models for Anomaly Data ---
class AnomalyResponse(BaseModel):
    """
    Pydantic model for returning anomaly data records.
    """
    id: int
    telemetry_id: int
    device_id: str
    metric_name: str
    metric_value: float
    timestamp: datetime
    anomaly_type: str | None
    threshold_used: float | None

    class Config:
        from_attributes = True