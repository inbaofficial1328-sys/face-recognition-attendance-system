from fastapi import FastAPI

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.departments import router as departments_router
from backend.app.api.v1.academic_classes import router as academic_classes_router
from backend.app.api.v1.students import router as students_router
from backend.app.api.v1.staff import router as staff_router
from backend.app.api.v1.teacher_assignments import router as teacher_assignments_router
from backend.app.api.v1.attendance_sessions import router as attendance_sessions_router
from backend.app.api.v1.attendance_records import router as attendance_records_router
from backend.app.api.v1.attendance_corrections import (
    router as attendance_corrections_router,
)

app = FastAPI(
    title="Face Recognition Attendance System",
    description="College attendance management REST API",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(departments_router)
app.include_router(academic_classes_router)
app.include_router(students_router)
app.include_router(staff_router)
app.include_router(teacher_assignments_router)
app.include_router(attendance_sessions_router)
app.include_router(attendance_records_router)
app.include_router(attendance_corrections_router)

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
