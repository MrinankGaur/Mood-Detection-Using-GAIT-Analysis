import asyncio
import json
import logging
import os
import sys
import threading
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from scipy.interpolate import Rbf

# Integrate ML pipeline paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "Mood-Detection"))
from src import feature_engineering as feature_mod
from src import predict as predict_mod
from run_pipeline import load_module_from_path, test_reader

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
logger = logging.getLogger("server")

app = FastAPI(title="GAIT Analysis Realtime Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 1. State and Data Structures
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.stream_connections: list[WebSocket] = []
        self.mood_connections: list[WebSocket] = []

    async def connect_stream(self, websocket: WebSocket):
        await websocket.accept()
        self.stream_connections.append(websocket)

    def disconnect_stream(self, websocket: WebSocket):
        if websocket in self.stream_connections:
            self.stream_connections.remove(websocket)

    async def connect_mood(self, websocket: WebSocket):
        await websocket.accept()
        self.mood_connections.append(websocket)

    def disconnect_mood(self, websocket: WebSocket):
        if websocket in self.mood_connections:
            self.mood_connections.remove(websocket)

    async def broadcast_stream(self, data: dict):
        # We send as JSON string
        message = json.dumps(data)
        for connection in self.stream_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

    async def broadcast_mood(self, data: dict):
        message = json.dumps(data)
        for connection in self.mood_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


# ==========================================
# 2. Fast Math Pre-computation (from visualise.py)
# ==========================================
BASELINE_R = np.array([0.010, 3.505, 9.362])
BASELINE_L = np.array([0.232, -2.589, 9.760])

right_foot_coords = np.array(
    [(284, 84), (379, 177), (320, 154), (272, 159), (362, 285), (301, 289), (346, 364), (294, 442)]
)
left_foot_coords = np.array(
    [(140, 84), (44, 175), (104, 153), (152, 158), (62, 284), (123, 289), (77, 363), (130, 441)]
)
all_coords = np.vstack((right_foot_coords, left_foot_coords))

# We downscale the grid from 100x100 to 50x50 to reduce WebSocket payload size across network
# The frontend canvas will automatically smooth and scale it back up
GRID_SIZE = 50
grid_x, grid_y = np.mgrid[0:563 : complex(0, GRID_SIZE), 0:430 : complex(0, GRID_SIZE)]


def precompute_rbf_matrix(sources, grid_x, grid_y, epsilon=40):
    xi = np.column_stack([grid_y.ravel(), grid_x.ravel()])
    di = np.sqrt(((xi[:, None, :] - sources[None, :, :]) ** 2).sum(axis=-1))
    matrix = np.exp(-((di / epsilon) ** 2))
    return matrix


logger.info("Pre-calculating RBF matrix for heatmap (Grid: %dx%d)...", GRID_SIZE, GRID_SIZE)
RBF_MATRIX = precompute_rbf_matrix(all_coords, grid_x, grid_y)


def update_orientation_data(acc, baseline, invert=False):
    delta = acc - baseline
    dx, dy = delta[0] / 9.8, delta[1] / 9.8
    if invert:
        dx, dy = -dx, -dy
    mag = np.sqrt(dx**2 + dy**2) + 1e-9
    if mag > 0.95:
        dx, dy = dx * 0.95 / mag, dy * 0.95 / mag
    tilt = np.degrees(np.arctan2(np.sqrt(delta[0] ** 2 + delta[1] ** 2), abs(baseline[2])))
    return dx, dy, tilt


# ==========================================
# 3. Data Processing Threads
# ==========================================
# Global state to pass between threads
latest_sensor_data = None
prediction_buffer = []
BACKGROUND_TASK_RUNNING = False
IS_COLLECTING = False
BATCH_SIZE = 2400

# Load header from datacollection.py
dc_path = ROOT / "Data Collection" / "datacollection.py"
datacollection = load_module_from_path("datacollection", dc_path)


def ml_pipeline_worker():
    """Runs in background thread, monitors the prediction_buffer."""
    global prediction_buffer
    logger.info("ML Pipeline background worker started.")

    while BACKGROUND_TASK_RUNNING:
        if not IS_COLLECTING:
            time.sleep(0.5)
            continue

        if len(prediction_buffer) >= BATCH_SIZE:
            # Pop the first BATCH_SIZE items
            batch = prediction_buffer[:BATCH_SIZE]
            prediction_buffer = prediction_buffer[BATCH_SIZE:]

            logger.info("Processing ML batch of %d rows...", BATCH_SIZE)
            try:
                df = pd.DataFrame(batch, columns=datacollection.header)
                numeric_cols = [c for c in datacollection.header if c not in ("timestamp", "mood")]
                df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

                preprocessed = feature_mod.process_raw_data(df)
                feat_df = pd.DataFrame(preprocessed, columns=predict_mod.columns)
                preds = predict_mod.model.predict(feat_df)

                pred_label = Counter(preds).most_common(1)[0][0]
                logger.info(f"== Mod Prediction == -> {pred_label.upper()}")

                # Broadcast mood via asyncio back to main loop
                asyncio.run(
                    manager.broadcast_mood(
                        {"type": "mood_prediction", "mood": pred_label, "timestamp": datetime.utcnow().isoformat()}
                    )
                )

            except Exception as e:
                logger.error("Batch prediction failed: %s", e)

        time.sleep(0.1)


async def async_stream_readings(esp32_ip="192.168.4.1", port=3333):
    """Async generator to read data from ESP32 natively without blocking the event loop."""
    logger.info(f"Connecting to ESP32 at {esp32_ip}:{port}...")
    try:
        reader, writer = await asyncio.open_connection(esp32_ip, port)
        logger.info("Connected to ESP32!")
    except Exception as e:
        logger.error(f"Failed to connect to ESP32: {e}")
        return

    sample = 0
    socket_buffer = ""
    while BACKGROUND_TASK_RUNNING:
        if not IS_COLLECTING:
            await asyncio.sleep(0.5)
            continue
            
        try:
            # Check if reader has data without blocking forever if not collecting
            try:
                data = await asyncio.wait_for(reader.read(2048), timeout=1.0)
            except asyncio.TimeoutError:
                continue
                
            if not data:
                break
            socket_buffer += data.decode()
            while "\n" in socket_buffer:
                line, socket_buffer = socket_buffer.split("\n", 1)
                values = line.split(",")
                if len(values) != 28:
                    continue
                timestamp = format(sample * 0.01, ".2f")
                row = [timestamp] + values + [None]
                yield row
                sample += 1
        except Exception as e:
            logger.error(f"ESP32 stream error: {e}")
            break

    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


async def sensor_stream_worker():
    """Async task that fakes or reads sensor data and sends over WS at ~60fps."""
    global prediction_buffer, BACKGROUND_TASK_RUNNING
    logger.info("Sensor streaming loop started.")

    frame_count = 0
    fps_start = time.time()

    async for row in async_stream_readings():
        if not BACKGROUND_TASK_RUNNING:
            break

        prediction_buffer.append(row)

        try:     
            # Row shape: timestamp, 16xpressure, 3xRightAcc, 3xRightGyro, 3xLeftAcc, 3xLeftGyro, mood
            values = np.array([float(x) for x in row[1:29]])  # excluding timestamp and mood
            pressure_vals = values[0:16]

            # 1. Heatmap Data (Fast! CPU)
            z_flat = RBF_MATRIX @ pressure_vals
            # We round to reduce JSON size over WS
            z_rounded = np.round(z_flat).astype(int).tolist()

            # 2. Orientation Data
            dxr, dyr, tr = update_orientation_data(values[16:19], BASELINE_R)
            dxl, dyl, tl = update_orientation_data(values[22:25], BASELINE_L, invert=True)

            payload = {
                "type": "sensor_frame",
                "heatmap": z_rounded, # 2500 int values
                "grid_size": GRID_SIZE,
                "right": {"dx": float(dxr), "dy": float(dyr), "tilt": float(tr)},
                "left": {"dx": float(dxl), "dy": float(dyl), "tilt": float(tl)},
                "buffer_count": len(prediction_buffer)
            }

            # Broadcast to all connected clients
            await manager.broadcast_stream(payload)
            frame_count += 1

            if frame_count % 300 == 0:
                elapsed = time.time() - fps_start
                logger.info(f"Streaming at {300/elapsed:.1f} FPS")
                fps_start = time.time()

        except Exception as e:
            logger.error("Error formatting frame data: %s", e)

        # Yield to event loop, rate is now driven naturally by ESP32 rather than artificial sleep
        await asyncio.sleep(0)


# ==========================================
# 4. FastAPI Lifecycle & Endpoints
# ==========================================
@app.on_event("startup")
async def startup_event():
    global BACKGROUND_TASK_RUNNING
    BACKGROUND_TASK_RUNNING = True

    # Start ML worker thread (blocking CPU-heavy tasks)
    thread = threading.Thread(target=ml_pipeline_worker, daemon=True)
    thread.start()

    # Start asyncio streaming loop
    asyncio.create_task(sensor_stream_worker())


@app.on_event("shutdown")
def shutdown_event():
    global BACKGROUND_TASK_RUNNING, IS_COLLECTING
    BACKGROUND_TASK_RUNNING = False
    IS_COLLECTING = False


@app.get("/")
def read_root():
    return {"status": "ok", "message": "GAIT Analysis API running. Connect via WebSockets."}


@app.get("/api/state")
def get_state():
    return {"is_collecting": IS_COLLECTING}


@app.post("/api/start")
def start_collection():
    global IS_COLLECTING, prediction_buffer
    IS_COLLECTING = True
    prediction_buffer.clear()
    return {"status": "started"}


@app.post("/api/stop")
def stop_collection():
    global IS_COLLECTING
    IS_COLLECTING = False
    return {"status": "stopped"}


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await manager.connect_stream(websocket)
    try:
        while True:
            # Keep pinging to keep alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_stream(websocket)


@app.websocket("/ws/mood")
async def websocket_mood(websocket: WebSocket):
    await manager.connect_mood(websocket)
    try:
        # Upon connection, maybe send an initial empty mood state
        await websocket.send_text(json.dumps({"type": "mood_prediction", "mood": "waiting..."}))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_mood(websocket)
