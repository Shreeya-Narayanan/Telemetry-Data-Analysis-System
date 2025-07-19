# Telemetry Data Analysis and Anomaly Detection System

This project is a full-stack application designed to ingest, store, analyze, and visualize real-time telemetry data from various simulated devices. It features a robust FastAPI backend, a dynamic web frontend, and a basic anomaly detection mechanism.

## ✨ Key Features

* **FastAPI Backend:** A high-performance RESTful API for telemetry data ingestion and retrieval.
* **Data Persistence:** Utilizes SQLAlchemy ORM with SQLite for efficient and reliable data storage.
* **Pydantic Validation:** Ensures data integrity and type safety for all incoming telemetry data.
* **Z-score Anomaly Detection:** Implements a statistical method to automatically identify unusual data points in real-time.
* **Dynamic Visualization:** Generates and serves time-series plots using Matplotlib, highlighting detected anomalies.
* **Responsive Web Dashboard:** A user-friendly HTML/CSS/JavaScript frontend for real-time data monitoring and anomaly display.
* **Device Simulator:** A dedicated Python script to simulate continuous telemetry data streams to the API.

## 🚀 Technologies Used

* **Backend:** Python 3.9+ (FastAPI, SQLAlchemy, Uvicorn, Matplotlib, NumPy)
* **Database:** SQLite
* **Frontend:** HTML, CSS (Tailwind CSS), JavaScript
* **Development Tools:** pip, uvicorn

## ▶️ How to Run

1.  **Start the FastAPI Backend:**
    Open your first terminal window, navigate to your project's root directory, and run:
    ```bash
    uvicorn main:app --reload
    ```
    The API will be accessible at `http://127.0.0.1:8000`.

2.  **Start the Telemetry Data Simulator:**
    Open a second terminal window, navigate to the directory containing `telemetry_simulator.py`, and run:
    ```bash
    python telemetry_simulator.py
    ```
    This script will continuously send simulated telemetry data to your running FastAPI application.

3.  **Access the Dashboard:**
    Open your web browser and navigate to:
    ```
    [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
    ```
    You will see the telemetry dashboard with live plots and detected anomalies.

## 📊 Anomaly Detection

The system employs a Z-score based anomaly detection method. For each incoming telemetry data point, it calculates its Z-score relative to a window of recent historical data for the same device and metric. If the Z-score exceeds a predefined threshold (default 2.5), the data point is flagged as an anomaly and stored in the database. These anomalies are then highlighted on the plots and listed in the dashboard.

## 🛣️ Future Enhancements

* **Asynchronous Processing:** Integrate a message queue (e.g., Redis, RabbitMQ) to decouple data ingestion from database writes, improving scalability and resilience.
* **Advanced Anomaly Detection:** Explore more sophisticated algorithms (e.g., Isolation Forest, ARIMA) for improved accuracy.
* **Authentication & Authorization:** Implement user login and access control for the API.
* **Database Migration:** Transition to a production-ready database like PostgreSQL for better concurrency and scalability.
