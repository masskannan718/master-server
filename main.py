import shutil
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"active": "True 🌍", "system": "Puyal OS Master Server"}

@app.get("/storage-status")
def get_storage_status():
    # ரெண்டர் சர்வருக்கு உள்ளே உள்ள ரூட் ஸ்டோரேஜ் விவரங்கள்
    total, used, free = shutil.disk_usage("/")
    
    # /data ஃபோல்டர் ஸ்டோரேஜ் விவரங்கள்
    try:
        d_total, d_used, d_free = shutil.disk_usage("/data")
        data_disk = {
            "total_gb": round(d_total / (2**30), 2),
            "used_gb": round(d_used / (2**30), 2),
            "free_gb": round(d_free / (2**30), 2),
        }
    except:
        data_disk = "Not mounted separately"

    return {
        "status": "Success 🚀",
        "root_disk": {
            "total_gb": round(total / (2**30), 2),
            "used_gb": round(used / (2**30), 2),
            "free_gb": round(free / (2**30), 2)
        },
        "data_disk": data_disk
    }
