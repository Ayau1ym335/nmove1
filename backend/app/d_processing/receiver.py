import os
import uuid
import numpy as np
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# This must match exactly what the ESP32 packs
IMU_DTYPE = np.dtype([
    ('header',    'u1'),       # 1 byte
    ('timestamp', 'f8'),       # 8 bytes (double)
    ('acc1',      'f4', (3,)), # 12 bytes (thigh accelerometer x,y,z)
    ('gyro1',     'f4', (3,)), # 12 bytes (thigh gyroscope x,y,z)
    ('acc2',      'f4', (3,)), # 12 bytes (shin accelerometer x,y,z)
    ('gyro2',     'f4', (3,)), # 12 bytes (shin gyroscope x,y,z)
])  # total = 57 bytes per sample

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)


@app.post("/api/upload-session")
async def upload_session(file: UploadFile = File(...)):
    raw = await file.read()

    # Validate the file size is a multiple of one packet
    packet_size = IMU_DTYPE.itemsize  # 57 bytes
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="Empty file received")
    if len(raw) % packet_size != 0:
        raise HTTPException(
            status_code=400,
            detail=f"File size {len(raw)} bytes is not a multiple of packet size {packet_size}. "
                   f"Data may be corrupted or truncated."
        )

    # Parse binary → numpy structured array
    data = np.frombuffer(raw, dtype=IMU_DTYPE)

    # Basic sanity checks
    n_samples = len(data)
    duration_sec = float(data['timestamp'][-1] - data['timestamp'][0])
    sample_rate = n_samples / duration_sec if duration_sec > 0 else 0

    # Save as .npy (fast to reload later with np.load)
    session_id = str(uuid.uuid4())[:8]
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(SESSIONS_DIR, f"session_{timestamp_str}_{session_id}.npy")
    np.save(save_path, data)

    return JSONResponse({
        "status": "ok",
        "session_id": session_id,
        "samples": n_samples,
        "duration_seconds": round(duration_sec, 2),
        "sample_rate_hz": round(sample_rate, 1),
        "saved_to": save_path,
    })


@app.get("/api/sessions")
def list_sessions():
    """List all saved session files."""
    files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".npy")]
    result = []
    for f in sorted(files):
        path = os.path.join(SESSIONS_DIR, f)
        data = np.load(path)
        result.append({
            "filename": f,
            "samples": len(data),
            "duration_seconds": round(float(data['timestamp'][-1] - data['timestamp'][0]), 2),
        })
    return result


@app.get("/api/sessions/{filename}")
def get_session(filename: str):
    """Load a session and return summary stats per axis."""
    path = os.path.join(SESSIONS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Session not found")

    data = np.load(path)

    def axis_stats(arr):
        # arr shape: (N, 3)
        return {
            "x": {"mean": round(float(arr[:, 0].mean()), 4), "std": round(float(arr[:, 0].std()), 4)},
            "y": {"mean": round(float(arr[:, 1].mean()), 4), "std": round(float(arr[:, 1].std()), 4)},
            "z": {"mean": round(float(arr[:, 2].mean()), 4), "std": round(float(arr[:, 2].std()), 4)},
        }

    return {
        "filename": filename,
        "samples": len(data),
        "duration_seconds": round(float(data['timestamp'][-1] - data['timestamp'][0]), 2),
        "thigh": {
            "acc":  axis_stats(data['acc1']),
            "gyro": axis_stats(data['gyro1']),
        },
        "shin": {
            "acc":  axis_stats(data['acc2']),
            "gyro": axis_stats(data['gyro2']),
        },
    }