
# Database Schema
Version: 1.0 — Initial Design

Database: SQLite for development and demonstration.

## 1. Users
- id: Primary key
- login_id: Unique
- password_hash
- role: ADMIN, HOD, TEACHER, STUDENT
- is_active
- created_at

## 2. Departments
- id: Primary key
- name
- code: Unique
- hod_user_id: Foreign key to Users

## 3. Classes
- id: Primary key
- department_id: Foreign key
- class_name
- academic_year
- section

## 4. Students
- id: Primary key
- user_id: Foreign key to Users, unique
- student_id: Unique college identifier
- registration_number: Unique
- umis_number: Unique
- full_name
- date_of_birth
- blood_group
- phone_number
- class_id: Foreign key
- face_enrolled: Boolean

## 5. Teachers
- id: Primary key
- user_id: Foreign key to Users, unique
- employee_id: Unique
- full_name
- department_id: Foreign key

## 6. Subjects
- id: Primary key
- subject_code
- subject_name
- department_id

## 7. Semesters
- id: Primary key
- name
- start_date
- end_date
- allowed_leave_days: Default 15
- fine_threshold: 75
- exam_restriction_threshold: 65
- fine_amount: Configurable

## 8. Timetable Sessions
- id: Primary key
- class_id: Foreign key
- subject_id: Foreign key
- teacher_id: Foreign key
- semester_id: Foreign key
- weekday
- period_number
- start_time
- end_time

## 9. Attendance
- id: Primary key
- student_id: Foreign key
- timetable_session_id: Foreign key
- attendance_date
- status: PRESENT, ABSENT, OD
- recognition_confidence: Nullable
- marked_by_user_id: Nullable foreign key
- marked_at
- updated_at

Unique constraint:
(student_id, timetable_session_id, attendance_date)

## 10. Attendance Audit Logs
- id: Primary key
- attendance_id: Foreign key
- changed_by_user_id: Foreign key
- previous_status
- new_status
- reason
- changed_at

## 11. Leave Requests
- id: Primary key
- student_id: Foreign key
- semester_id: Foreign key
- start_date
- end_date
- requested_days
- status: PENDING, APPROVED, REJECTED
- approved_by_user_id: Nullable foreign key

## 12. Eligibility Approvals
- id: Primary key
- student_id: Foreign key
- semester_id: Foreign key
- approved_by_user_id: Foreign key
- approval_status
- reason
- approved_at

## Business Rules
- Attendance is recorded separately for every conducted period.
- Teachers may correct only their assigned sessions.
- Corrections close at the end of the attendance day.
- All corrections require an audit record.
- Students can view only their own information.
- Approved leave allowance is 15 days per semester.
- Overall attendance determines examination eligibility.
- Attendance at or below 75% triggers a fine.
- Attendance at or below 65% triggers exam restrictions.
- HOD eligibility approval does not modify attendance.
- Unknown or out-of-class faces cannot mark attendance.
- OD periods are excluded from the attendance denominator.
- OD does not consume the 15-day semester leave allowance.
- A period cannot be counted as both OD and approved leave.

## Holiday and Cancelled-Period Policy
- Official college holidays are excluded from attendance calculations.
- Officially cancelled periods are excluded from conducted periods.
- Holidays and cancelled periods do not consume approved leave.
- Only authorized administrators can declare college holidays.
- Period cancellations must be recorded by authorized staff.
- Every cancellation must include a reason and timestamp.
- Attendance percentages must be recalculated when a
  holiday or period cancellation is officially recorded.

## Leave Calculation Policy
- Every student receives 15 approved leave days per semester.
- Full-day approved leave consumes 1 leave day.
- Approved partial-day leave consumes 0.5 leave day.
- Only periods covered by approved leave are excluded
  from the attendance calculation.
- Leave exceeding the 15-day allowance is not excused.
- OD does not consume the approved leave allowance.
- Leave and OD must not be counted twice for the same period.

## Pending Design Details
- OD treatment in attendance calculations.
- Half-day leave and period-level leave conversion.
- Holiday and cancelled-period handling.
- Teacher substitution authorization.
- Semester enrollment and historical class transfers.
- Attendance-day timezone and correction deadline.
- Face biometric storage and retention policy.

## Substitute Teacher Authorization

- Both Admin and HOD can assign substitute teachers.
- HODs can authorize substitutions only within their department.
- Every substitution applies to a specific class,
  subject, date and period.
- The substitute teacher receives attendance permissions
  only for the authorized session.
- The original teacher's attendance-editing permission
  is suspended for that substituted session.
- Substitute teachers can correct attendance only
  until the end of the assigned day.
- Every substitution requires an authorization record.
- All attendance corrections require an audit trail.

## Substitute Teacher Assignments
- id: Primary key
- timetable_session_id: Foreign key
- assignment_date
- original_teacher_id: Foreign key
- substitute_teacher_id: Foreign key
- authorized_by_user_id: Foreign key
- reason
- created_at