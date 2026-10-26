import shutil
import subprocess
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

@app.get("/storage-inspect")
def inspect_storage():
    try:
        # ரெண்டர் சர்வருக்கு உள்ளே எந்தெந்த ஃபோல்டர்கள் அதிக இடத்தை பிடிக்கின்றன என சோதிக்க
        cmd = "du -h --max-depth=2 / 2>/dev/null | sort -hr | head -n 25"
        output = subprocess.check_output(cmd, shell=True, text=True)
        return {
            "status": "Success 🔍",
            "largest_directories": output.splitlines()
        }
    except Exception as e:
        return {"status": "Error", "detail": str(e)}
