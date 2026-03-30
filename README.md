<div align="center">
  <h1>GAIT Analysis: Real-Time Biometric Mood Detection System</h1>
  <p>An enterprise-grade, real-time platform for human mood detection through biometric gait analysis, integrating IoT sensors, machine learning, and a high-performance web dashboard.</p>
</div>

---

## Overview

The **GAIT Analysis Mood Detection System** utilizes advanced pressure sensors and Inertial Measurement Units (IMUs) to analyze complex walking patterns in real time. Powered by a high-throughput **FastAPI WebSocket server** and a sophisticated **Next.js frontend**, the platform provides near-instantaneous visualization of foot pressure distribution (spatial heatmaps) and structural orientation. 

Concurrently, a specialized **RandomForest** machine learning pipeline operates as a background process to continuously evaluate streaming gait features and predict the subject's corresponding emotional state (e.g., Angry, Sad, Happy) with low latency.

### Core Capabilities

- **Real-Time IoT Streaming:** Interfaces natively with ESP32 microcontrollers via low-latency sockets at approximately 100Hz. The system sequentially processes 16 pressure sensor inputs and 6-DOF IMU data for comprehensive foot analytics.
- **Biometric Heatmaps:** Computes and renders high-fidelity spatial heatmaps using Radial Basis Function (RBF) interpolation techniques for granular pressure visualization.
- **Orientation Tracking:** Consistently calculates real-time foot orientation metrics (tilt, delta X, delta Y) derived directly from robust accelerometer and gyroscope data streams.
- **Predictive Machine Learning Pipeline:** Employs a buffered streaming architecture to extract gait features dynamically. Predictions are executed by a pre-trained scikit-learn classification model, yielding the most probable emotional state.
- **Dynamic Observability Dashboard:** A modern, highly responsive Next.js web application built upon TailwindCSS v4, delivering real-time metrics, interactive canvas displays, and comprehensive system state observability.

---

## System Architecture

The repository is modularized into two primary applications alongside a data acquisition pipeline:

```text
Mood-Detection-Using-GAIT-Analysis/
├── Mood-Detection/           # Python FastAPI Backend & Machine Learning Pipeline
│   ├── server.py             # Primary FastAPI application and WebSocket orchestrator
│   ├── run_pipeline.py       # ML Pipeline execution and batch processing
│   ├── src/                  # Feature engineering and predictive logic modules
│   └── notebooks/            # Jupyter notebooks for model training and EDA
├── frontend/                 # Next.js Web Application (React 19)
│   ├── src/app/              # Next.js App router configurations
│   ├── src/components/       # UI Components (HeatmapCanvas, MoodCard, StreamControls)
│   └── package.json          # Node dependency definitions
└── Data Collection/          # specialized scripts for raw ESP32 data aggregation
```

---

## Getting Started

### Prerequisites
- **Node.js** (v18 or higher)
- **Python** (v3.9 or higher)
- Appropriately configured ESP32 hardware streaming continuous CSV telemetry to `192.168.4.1:3333` (configurable within `server.py`).

### 1. Backend Initialization

Navigate to the backend directory to provision the Python environment and install required dependencies.

```bash
cd Mood-Detection
pip install -r requirements.txt
```

Launch the FastAPI ASGI server:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```
> The backend HTTP API will initialize at `http://localhost:8000`, continuously listening on WebSocket endpoints `/ws/stream` and `/ws/mood`.

### 2. Frontend Initialization

In an alternate terminal session, navigate to the frontend directory to resolve Node modules.

```bash
cd frontend
npm install
```

Boot the Next.js development server:

```bash
npm run dev
```

> The visualization dashboard will be accessible via a standard web browser at [http://localhost:3000](http://localhost:3000).

---

## Machine Learning Pipeline

The mood prediction infrastructure operates within a dedicated background thread to preserve main-loop latency, systematically collecting temporal batches (2400 ticks) from the active IoT stream.

1. **Feature Engineering:** Raw IMU and pressure data streams are parsed into deterministic temporal and spatial features (`src/feature_engineering.py`).
2. **Prediction:** A hyperparameter-tuned `RandomForest` classifier continuously evaluates the extracted feature subspace to classify the highest-probability dominant mood (`src/predict.py`).
3. **Training & Validation:** Comprehensive model training cycles, evaluation metrics, and exploratory data analysis environments reside within the `Mood-Detection/notebooks` directory.

---

## Technology Stack

- **Frontend:** Next.js 16, React 19, TailwindCSS v4, TypeScript
- **Backend:** FastAPI, Uvicorn, WebSockets, Python 3
- **Data Science:** Pandas, NumPy, Scikit-Learn, SciPy (Rbf Interpolation)
- **Hardware Integration:** ESP32 Microcontrollers, IMU (Accelerometer/Gyroscope), FSR (Force Sensitive Resistors)

---

## License

This project is licensed under the MIT License. It is open for exploration, structural modification, and integration into subsequent biometric research or commercial implementations.
