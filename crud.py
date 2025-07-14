# crud.py
# This file contains the Create, Read, Update, Delete (CRUD) operations
# that interact directly with the database using SQLAlchemy.

from sqlalchemy.orm import Session
from sqlalchemy import func
import models 
import numpy as np # Import numpy for numerical operations (e.g., Z-score)

# --- Create Operations ---

def create_telemetry_data(db: Session, telemetry: models.TelemetryDataCreate):
    """
    Creates a new telemetry data record in the database.

    Args:
        db: The SQLAlchemy database session.
        telemetry: A Pydantic model containing the telemetry data to create.

    Returns:
        The created TelemetryData ORM object.
    """
    db_telemetry = models.TelemetryData(
        timestamp=telemetry.timestamp,
        device_id=telemetry.device_id,
        metric_name=telemetry.metric_name,
        metric_value=telemetry.metric_value,
        unit=telemetry.unit
    )
    db.add(db_telemetry)
    db.commit() # Commit the transaction to save changes
    db.refresh(db_telemetry) # Refresh the instance to load any new data from the database (e.g., auto-generated ID)
    return db_telemetry

# --- Read Operations ---

def get_all_telemetry_data(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieves all telemetry data records from the database with pagination.

    Args:
        db: The SQLAlchemy database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of TelemetryData ORM objects.
    """
    return db.query(models.TelemetryData).offset(skip).limit(limit).all()

def get_telemetry_by_device(db: Session, device_id: str, skip: int = 0, limit: int = 100):
    """
    Retrieves telemetry data records for a specific device.

    Args:
        db: The SQLAlchemy database session.
        device_id: The ID of the device to filter by.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of TelemetryData ORM objects.
    """
    return db.query(models.TelemetryData).filter(models.TelemetryData.device_id == device_id).offset(skip).limit(limit).all()

def get_recent_telemetry_by_device(db: Session, device_id: str, count: int = 10):
    """
    Retrieves the most recent telemetry data points for a specific device.

    Args:
        db: The SQLAlchemy database session.
        device_id: The ID of the device to filter by.
        count: The number of most recent records to retrieve.

    Returns:
        A list of TelemetryData ORM objects, ordered by timestamp descending.
    """
    return db.query(models.TelemetryData)\
             .filter(models.TelemetryData.device_id == device_id)\
             .order_by(models.TelemetryData.timestamp.desc())\
             .limit(count)\
             .all()

def get_metric_summary_for_device(db: Session, device_id: str, metric_name: str):
    """
    Calculates a basic summary (min, max, avg) for a specific metric from a device.

    Args:
        db: The SQLAlchemy database session.
        device_id: The ID of the device.
        metric_name: The name of the metric.

    Returns:
        A dictionary with 'min_value', 'max_value', 'avg_value', or None if no data.
    """
    result = db.query(
        func.min(models.TelemetryData.metric_value).label('min_value'),
        func.max(models.TelemetryData.metric_value).label('max_value'),
        func.avg(models.TelemetryData.metric_value).label('avg_value')
    ).filter(
        models.TelemetryData.device_id == device_id,
        models.TelemetryData.metric_name == metric_name
    ).first()

    if result and result.min_value is not None:
        return {
            "device_id": device_id,
            "metric_name": metric_name,
            "min_value": result.min_value,
            "max_value": result.max_value,
            "avg_value": result.avg_value
        }
    return None


def get_telemetry_for_plotting(db: Session, device_id: str, metric_name: str, limit: int = 200):
    """
    Retrieves a limited number of telemetry data points for plotting.
    Ordered by timestamp ascending.

    Args:
        db: The SQLAlchemy database session.
        device_id: The ID of the device.
        metric_name: The name of the metric.
        limit: The maximum number of records to retrieve for the plot.

    Returns:
        A list of TelemetryData ORM objects.
    """
    return db.query(models.TelemetryData)\
             .filter(
                 models.TelemetryData.device_id == device_id,
                 models.TelemetryData.metric_name == metric_name
             )\
             .order_by(models.TelemetryData.timestamp.asc())\
             .limit(limit)\
             .all()

def get_anomalies(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieves all detected anomalies with pagination.
    """
    return db.query(models.Anomaly).order_by(models.Anomaly.timestamp.desc()).offset(skip).limit(limit).all()

def create_anomaly(db: Session, anomaly_data: dict):
    """
    Creates a new anomaly record in the database.
    """
    db_anomaly = models.Anomaly(**anomaly_data)
    db.add(db_anomaly)
    db.commit()
    db.refresh(db_anomaly)
    return db_anomaly

# --- Anomaly Detection Logic (Z-score based) ---
def detect_anomaly_zscore(
    db: Session,
    telemetry_record: models.TelemetryData,
    window_size: int = 50, # Number of previous data points to consider
    z_score_threshold: float = 2.5 # Threshold for Z-score
) -> models.Anomaly | None:
    """
    Detects anomalies using a simple Z-score method.
    Fetches a window of previous data for the same device and metric,
    calculates mean and std dev, then checks if the new value is an outlier.

    Args:
        db: The SQLAlchemy database session.
        telemetry_record: The new telemetry data point to check.
        window_size: The number of previous data points to consider for mean/std dev.
        z_score_threshold: The Z-score threshold for anomaly detection.

    Returns:
        An Anomaly ORM object if an anomaly is detected, otherwise None.
    """
    # Fetch recent data for the same device and metric, excluding the current record
    recent_data = db.query(models.TelemetryData.metric_value)\
                    .filter(
                        models.TelemetryData.device_id == telemetry_record.device_id,
                        models.TelemetryData.metric_name == telemetry_record.metric_name,
                        models.TelemetryData.id != telemetry_record.id # Exclude the current record if it's already committed
                    )\
                    .order_by(models.TelemetryData.timestamp.desc())\
                    .limit(window_size)\
                    .all()

    values = np.array([d.metric_value for d in recent_data])

    if len(values) < 5: # Need at least a few points to calculate meaningful stats
        return None

    mean = np.mean(values)
    std_dev = np.std(values)

    if std_dev == 0: # Avoid division by zero if all values in window are identical
        return None
    
    z_score = abs((float(telemetry_record.metric_value) - mean) / std_dev)

    if z_score > z_score_threshold:
        anomaly_data = {
            "telemetry_id": telemetry_record.id,
            "device_id": telemetry_record.device_id,
            "metric_name": telemetry_record.metric_name,
            "metric_value": telemetry_record.metric_value,
            "timestamp": telemetry_record.timestamp,
            "anomaly_type": f"High Z-score ({z_score:.2f})",
            "threshold_used": z_score_threshold
        }
        return create_anomaly(db, anomaly_data) # Create and return the anomaly
    return None

