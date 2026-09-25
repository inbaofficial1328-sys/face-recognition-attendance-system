from fastapi import FastAPI

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.admin import router as admin_router

app = FastAPI(
    title="Face Recognition Attendance System",
    description="College attendance management REST API",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(admin_router)

@app.get("/")
async def root():
    return {
        "application": "Face Recognition Attendance System",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "Attendance Backend",
    }

from backend.app.api.v1.admin import router as admin_router