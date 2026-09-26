from backend.app.db.database import Base

# Import models so SQLAlchemy registers their tables.
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.models.department import Department
from backend.app.models.academic_class import AcademicClass
from backend.app.models.teacher_assignment import TeacherAssignment
from backend.app.models.attendance_session import AttendanceSession
from backend.app.models.attendance_record import AttendanceRecord
from backend.app.models.attendance_correction import AttendanceCorrection