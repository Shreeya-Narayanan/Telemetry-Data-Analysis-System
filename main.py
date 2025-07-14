# main.py
# This is the main FastAPI application file.
# It brings together the database, models, and API endpoints.
# --- Dependencies (FastAPI's way of managing shared resources) ---
#List in imports is used for type hinting

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request # Added Request
from fastapi.responses import StreamingResponse, HTMLResponse # Added StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles # Added StaticFiles
from sqlalchemy.orm import Session
from typing import List
import matplotlib.pyplot as plt # Import matplotlib
import io # Import io for BytesIO
import numpy as np # Import numpy  

# Import modules for database, models, and CRUD operations
import crud, models, database

# --- Lifespan Event Handler ---
# This context manager handles startup and shutdown events for the application.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Initializes the database tables on startup.
    """
    print("Application startup: Creating database tables...")
    database.Base.metadata.create_all(bind=database.engine)
    print("Database tables created (if they didn't exist).")
    yield # Application runs
    print("Application shutdown: Cleaning up resources (if any)...")
    # Add any cleanup logic here if needed, e.g., closing external connections
    # For SQLite, closing the engine isn't strictly necessary as it's file-based,
    # but for other databases, you might close connection pools.


# Create the FastAPI application instance
app = FastAPI(
    title="Telemetry Data Analysis API",
    description="API for ingesting, storing, and retrieving telemetry data.",
    version="0.1.0",
    lifespan=lifespan
)


# --- Static Files Configuration ---
# Mount the "static" directory to serve static files (like index.html)
# If index.html is in the root, you can mount the root directory.
# Ensure 'index.html' is in the same directory as main.py for this to work.
app.mount("/static", StaticFiles(directory="."), name="static") # Mounts the current directory as /static


# Dependency to get a database session
# This function will be used by FastAPI's Dependency Injection system
# to provide a database session for each request.
def get_db():
    """
    Provides a SQLAlchemy database session for a request.
    Ensures the session is closed after the request is processed.
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@app.post("/telemetry/", response_model=models.TelemetryDataResponse)
def create_telemetry_data(telemetry: models.TelemetryDataCreate, db: Session = Depends(get_db)):
    """
    Ingest new telemetry data.

    - timestamp: The UTC timestamp of the telemetry event (ISO 8601 format).
    - device_id: Identifier for the device sending the telemetry.
    - metric_name: The name of the metric (e.g., 'temperature', 'humidity', 'cpu_usage').
    - metric_value: The numerical value of the metric.
    - unit: The unit of the metric (e.g., 'Celsius', 'Percentage').
    """
    try:
        # Call the CRUD function to create a new telemetry record
        db_telemetry = crud.create_telemetry_data(db=db, telemetry=telemetry)
        return db_telemetry
    except Exception as e:
        # Generic error handling for database operations
        raise HTTPException(status_code=500, detail=f"Failed to ingest telemetry data: {e}")

@app.get("/telemetry/", response_model=List[models.TelemetryDataResponse])
def read_all_telemetry_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all telemetry data with pagination.

    - skip: Number of records to skip (for pagination).
    - limit: Maximum number of records to return.
    """
    telemetry_data = crud.get_all_telemetry_data(db, skip=skip, limit=limit)
    return telemetry_data

@app.get("/telemetry/device/{device_id}", response_model=List[models.TelemetryDataResponse])
def read_telemetry_by_device(device_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve telemetry data for a specific device.

    - device_id: The ID of the device to filter by.
    - skip: Number of records to skip (for pagination).
    - limit: Maximum number of records to return.
    """
    telemetry_data = crud.get_telemetry_by_device(db, device_id=device_id, skip=skip, limit=limit)
    if not telemetry_data:
        raise HTTPException(status_code=404, detail="No telemetry data found for this device.")
    return telemetry_data

@app.get("/telemetry/recent/{device_id}", response_model=List[models.TelemetryDataResponse])
def read_recent_telemetry_by_device(device_id: str, count: int = 10, db: Session = Depends(get_db)):
    """
    Retrieve the most recent telemetry data points for a specific device.

    - device_id: The ID of the device to filter by.
    - count: The number of most recent records to retrieve.
    """
    telemetry_data = crud.get_recent_telemetry_by_device(db, device_id=device_id, count=count)
    if not telemetry_data:
        raise HTTPException(status_code=404, detail="No recent telemetry data found for this device.")
    return telemetry_data

@app.get("/telemetry/summary/{device_id}/{metric_name}", response_model=dict)
def get_metric_summary(device_id: str, metric_name: str, db: Session = Depends(get_db)):
    """
    Get a basic summary (min, max, avg) for a specific metric from a device.
    """
    summary = crud.get_metric_summary_for_device(db, device_id=device_id, metric_name=metric_name)
    if not summary:
        raise HTTPException(status_code=404, detail="No data found for this metric or device.")
    return summary

@app.get("/anomalies/", response_model=List[models.AnomalyResponse])
def read_anomalies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all detected anomalies.
    """
    anomalies = crud.get_anomalies(db, skip=skip, limit=limit)
    return anomalies

@app.get("/plot/{device_id}/{metric_name}")
async def get_telemetry_plot(device_id: str, metric_name: str, db: Session = Depends(get_db)):
    """
    Generates and returns a Matplotlib plot of telemetry data for a specific device and metric.
    Highlights detected anomalies on the plot.
    """
    telemetry_data = crud.get_telemetry_for_plotting(db, device_id=device_id, metric_name=metric_name)
    anomalies = db.query(models.Anomaly)\
                  .filter(models.Anomaly.device_id == device_id, models.Anomaly.metric_name == metric_name)\
                  .order_by(models.Anomaly.timestamp.asc())\
                  .all()

    if not telemetry_data:
        raise HTTPException(status_code=404, detail="No telemetry data found for plotting.")

    # Extract timestamps and metric values
    timestamps = [d.timestamp for d in telemetry_data]
    metric_values = [d.metric_value for d in telemetry_data]

    # Extract anomaly timestamps and values
    anomaly_timestamps = [a.timestamp for a in anomalies if a.timestamp in timestamps] # Only plot anomalies that are in the fetched telemetry data
    anomaly_values = [a.metric_value for a in anomalies if a.timestamp in timestamps]

    # Create the plot
    plt.figure(figsize=(10, 6)) # Set figure size
    plt.plot(timestamps, metric_values, marker='o', linestyle='-', markersize=4, label=f'{metric_name} Trend')

    # Highlight anomalies
    if anomaly_timestamps:
        plt.scatter(anomaly_timestamps, anomaly_values, color='red', s=100, marker='X', label='Anomaly', zorder=5)

    plt.title(f'{metric_name} Trend for {device_id}')
    plt.xlabel('Time (UTC)')
    plt.ylabel(f'{metric_name} Value')
    plt.grid(True)
    plt.xticks(rotation=45, ha='right') # Rotate x-axis labels for better readability
    plt.tight_layout() # Adjust layout to prevent labels from overlapping
    plt.legend()

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0) # Rewind the buffer to the beginning
    plt.close() # Close the plot to free up memory

    # Return the image as a StreamingResponse
    return StreamingResponse(buf, media_type="image/png")

# --- Serve the Frontend HTML ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serves the main frontend HTML page.
    """
    with open("index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)



