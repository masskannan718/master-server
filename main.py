
import shutil

@app.get("/storage-status")
def get_storage_status():
    total, used, free = shutil.disk_usage("/")
    return {
        "total_gb": round(total / (2**30), 2),
        "used_gb": round(used / (2**30), 2),
        "free_gb": round(free / (2**30), 2),
    }
