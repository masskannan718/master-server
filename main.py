import shutil
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"active": "True 🌍", "system": "Puyal OS Master Server"}

@app.get("/storage-status")
def get_storage_status():
    total, used, free = shutil.disk_usage("/")
    return {
        "status": "Success 🚀",
        "root_disk": {
            "total_gb": round(total / (2**30), 2),
            "used_gb": round(used / (2**30), 2),
            "free_gb": round(free / (2**30), 2)
        }
    }
