import os
import sqlite3
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MasterServer")

ADMIN_KEY = os.getenv("ADMIN_SECRET_KEY", "default_master_admin_secret_key_32_chars")
WORKER_KEY = os.getenv("WORKER_SECRET_KEY", "default_master_worker_secret_key_32_chars")
DB_PATH = "data/master_state.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            status TEXT DEFAULT 'QUEUED',
            generated_code TEXT,
            apk_url TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            tunnel_url TEXT NOT NULL,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

app = FastAPI(title="Master Orchestrator")

def verify_admin(x_admin_secret: str = Header(None)):
    if x_admin_secret != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid Admin Secret Key")

def verify_worker(x_worker_secret: str = Header(None)):
    if x_worker_secret != WORKER_KEY:
        raise HTTPException(status_code=401, detail="Invalid Worker Secret Key")

class WorkerRegisterRequest(BaseModel):
    worker_id: str
    tunnel_url: str

class CreateJobRequest(BaseModel):
    prompt: str

class UpdateJobStatusRequest(BaseModel):
    status: str
    generated_code: Optional[str] = None
    apk_url: Optional[str] = None

@app.get("/health/live")
def health_check():
    return {"status": "healthy", "service": "Master Server", "timestamp": datetime.utcnow().isoformat()}

@app.post("/bridge/register-worker", dependencies=[Depends(verify_worker)])
def register_worker(data: WorkerRegisterRequest):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO workers (id, tunnel_url, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET tunnel_url=excluded.tunnel_url, updated_at=excluded.updated_at
    """, (data.worker_id, data.tunnel_url, now))
    conn.commit()
    conn.close()
    return {"message": "Worker registered successfully"}

@app.post("/jobs/create", dependencies=[Depends(verify_admin)])
def create_job(job: CreateJobRequest):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO jobs (prompt, status, created_at, updated_at) VALUES (?, 'QUEUED', ?, ?)", (job.prompt, now, now))
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"job_id": job_id, "status": "QUEUED"}

@app.get("/jobs/next", dependencies=[Depends(verify_worker)])
def get_next_job():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, prompt, status FROM jobs WHERE status = 'QUEUED' ORDER BY id ASC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"job": None}
    return {"job": {"id": row[0], "prompt": row[1], "status": row[2]}}

@app.post("/jobs/{job_id}/update", dependencies=[Depends(verify_worker)])
def update_job(job_id: int, data: UpdateJobStatusRequest):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs 
        SET status = ?, generated_code = COALESCE(?, generated_code), apk_url = COALESCE(?, apk_url), updated_at = ?
        WHERE id = ?
    """, (data.status, data.generated_code, data.apk_url, now, job_id))
    conn.commit()
    conn.close()
    return {"job_id": job_id, "updated_status": data.status}

@app.get("/jobs/{job_id}", dependencies=[Depends(verify_admin)])
def get_job(job_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, prompt, status, result, created_at, updated_at FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": row[0],
        "prompt": row[1],
        "status": row[2],
        "result": row[3],
        "created_at": row[4],
        "updated_at": row[5]
    }
