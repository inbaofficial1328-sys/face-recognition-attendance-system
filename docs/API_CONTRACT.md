# Face Recognition Attendance System
# Shared API Contract

Version: 1.0
Status: Draft

Backend: Python + FastAPI
Frontend: HTML + CSS + JavaScript
Database: SQLite

## Base URL

http://127.0.0.1:8000/api/v1

## Authentication

All protected API endpoints require authentication.

User roles:
- ADMIN
- HOD
- TEACHER
- STUDENT

## API Modules

1. Authentication
2. Student Management
3. Teacher Management
4. Departments and Classes
5. Subjects and Timetables
6. Substitute Teacher Assignments
7. Face Enrollment and Recognition
8. Period-wise Attendance
9. Manual Attendance Corrections
10. Leave Management
11. Student Dashboard
12. Attendance Eligibility
13. HOD Approvals
14. Reports and Exports
15. Academic Semester Configuration

## Shared Rules

- Students can access only their own records.
- Teachers can modify attendance only for authorized sessions.
- Admin and HOD can assign substitute teachers.
- Attendance corrections close at the end of the assigned day.
- All attendance modifications require an audit trail.
- OD, approved leave, holidays and cancelled periods
  follow the confirmed database policies.
- Fine applies at 75% attendance or below.
- Exam restriction applies at 65% attendance or below.

## Standard API Response

Successful responses return the requested data.

Error responses follow this structure:

{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}

## 1. Authentication API

### POST /auth/login

Access: Public

Request:
```json
{
  "login_id": "STU001",
  "password": "example-password"
}
```

Successful response (200):
```json
{
  "access_token": "example-jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "login_id": "STU001",
    "role": "STUDENT"
  }
}
```

Invalid credentials (401):
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid login credentials"
  }
}
```

### GET /auth/me

Access: Authenticated users

Header:
Authorization: Bearer ACCESS_TOKEN

Successful response (200):
```json
{
  "id": 1,
  "login_id": "STU001",
  "role": "STUDENT"
}
```

### POST /auth/logout

Access: Authenticated users

Header:
Authorization: Bearer ACCESS_TOKEN

Successful response (200):
```json
{
  "message": "Logged out successfully"
}
```

Implementation note:
Logout must invalidate the current session or token.
A client-side token deletion alone is not server-side logout.

### Authentication Security Rules

- Store passwords using a secure password-hashing algorithm.
- Never return passwords or password hashes in API responses.
- Use HTTPS outside local development.
- Enforce role permissions on the backend.
- Apply login rate limiting.
- Use short-lived access tokens.
- Define token expiry and revocation before implementation.
- Return the standard API error format for authentication errors.

## 2. Student Management API

All endpoints use the base URL:
http://127.0.0.1:8000/api/v1

### POST /students

Access: ADMIN

Purpose: Register a new student and create their login account.

Request:
```json
{
  "login_id": "STU001",
  "password": "temporary-password",
  "student_id": "STU001",
  "registration_number": "REG2026001",
  "umis_number": "UMIS2026001",
  "full_name": "Demo Student",
  "date_of_birth": "2005-06-15",
  "blood_group": "O+",
  "phone_number": "9000000000",
  "class_id": 1
}
```

Successful response (201):
```json
{
  "id": 1,
  "student_id": "STU001",
  "registration_number": "REG2026001",
  "full_name": "Demo Student",
  "class_id": 1,
  "face_enrolled": false
}
```

The password must be hashed before storage and must
never appear in the response.

### GET /students

Access: ADMIN, authorized HOD

Purpose: List students within the user's permitted scope.

Optional query parameters:
- class_id
- department_id
- search
- page
- page_size

Successful response (200):
```json
{
  "items": [
    {
      "id": 1,
      "student_id": "STU001",
      "full_name": "Demo Student",
      "class_id": 1,
      "face_enrolled": false
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### GET /students/{student_id}

Access: ADMIN, authorized HOD, owning STUDENT

Purpose: Retrieve a student profile.

Here, student_id is the database primary key.

Successful response (200):
```json
{
  "id": 1,
  "student_id": "STU001",
  "registration_number": "REG2026001",
  "umis_number": "UMIS2026001",
  "full_name": "Demo Student",
  "date_of_birth": "2005-06-15",
  "blood_group": "O+",
  "phone_number": "9000000000",
  "class_id": 1,
  "face_enrolled": false
}
```

Sensitive profile fields must be restricted
according to the authenticated user's permissions.

### PATCH /students/{student_id}

Access: ADMIN

Purpose: Update permitted student profile fields.

Request example:
```json
{
  "phone_number": "9111111111"
}
```

Successful response (200):
Returns the updated student profile.

### DELETE /students/{student_id}

Access: ADMIN

Purpose: Deactivate a student account.

Successful response (200):
```json
{
  "message": "Student account deactivated successfully"
}
```

Do not physically delete historical attendance records.

### Student Management Rules

- Only ADMIN can create or deactivate student accounts.
- HOD access is restricted to authorized departments.
- Students may view only their own profiles.
- Students cannot edit their attendance or identity details.
- Student ID, registration number and UMIS number
  must be unique.
- Validate all submitted profile fields.
- Never expose passwords or password hashes.
- Deactivated students cannot log in.
- Deactivation must preserve historical attendance.
- Face enrollment is handled by a separate API.
- All endpoints enforce permissions on the backend.
- Unauthorized requests return 403.
- Unauthenticated requests return 401.
- Missing student records return 404.
```

## 3. Teacher Management API

Base URL: /api/v1

### POST /teachers

Access: ADMIN

Purpose: Register a teacher and create their login account.

Request:
```json
{
  "login_id": "TCH001",
  "password": "temporary-password",
  "employee_id": "EMP001",
  "full_name": "Demo Teacher",
  "department_id": 1
}
```

Successful response (201):
```json
{
  "id": 1,
  "employee_id": "EMP001",
  "full_name": "Demo Teacher",
  "department_id": 1
}
```

### GET /teachers

Access: ADMIN, authorized HOD

Purpose: List teachers within the permitted scope.

Optional query parameters:
- department_id
- search
- page
- page_size

Successful response (200):
```json
{
  "items": [
    {
      "id": 1,
      "employee_id": "EMP001",
      "full_name": "Demo Teacher",
      "department_id": 1
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### GET /teachers/{teacher_id}

Access: ADMIN, authorized HOD, owning TEACHER

Purpose: Retrieve a teacher profile.

Here, teacher_id refers to the database primary key.

Successful response (200):
```json
{
  "id": 1,
  "employee_id": "EMP001",
  "full_name": "Demo Teacher",
  "department_id": 1
}
```

### PATCH /teachers/{teacher_id}

Access: ADMIN

Purpose: Update a teacher's permitted profile fields.

Request example:
```json
{
  "department_id": 2
}
```

Successful response (200):
Returns the updated teacher profile.

### DELETE /teachers/{teacher_id}

Access: ADMIN

Purpose: Deactivate a teacher account.

Successful response (200):
```json
{
  "message": "Teacher account deactivated successfully"
}
```

Historical attendance and teacher assignment records
must be preserved.

### GET /teachers/me/sessions

Access: TEACHER

Purpose: Retrieve the authenticated teacher's assigned
timetable sessions.

Optional query parameters:
- date
- class_id

Successful response (200):
```json
{
  "items": [
    {
      "timetable_session_id": 1,
      "class_id": 1,
      "subject_id": 1,
      "period_number": 2,
      "start_time": "10:00",
      "end_time": "10:50",
      "is_substitute": false
    }
  ]
}
```

### Teacher Management Rules

- Only ADMIN can register or deactivate teachers.
- HODs can view teachers within their department.
- Teachers can view their own profiles and assignments.
- Teacher permissions depend on actual timetable
  assignments and authorized substitutions.
- Teacher deactivation must preserve historical records.
- Employee IDs must be unique.
- Passwords must be securely hashed.
- Never expose passwords or password hashes.
- Unauthenticated requests return 401.
- Unauthorized requests return 403.
- Missing teacher records return 404.
```

## 4. Department, Class and Subject APIs

Base URL: /api/v1

### POST /departments
Access: ADMIN

Request:
{
  "name": "B.Sc. Data Science",
  "code": "BSC_DS",
  "hod_user_id": 2
}

Response (201):
{
  "id": 1,
  "name": "B.Sc. Data Science",
  "code": "BSC_DS",
  "hod_user_id": 2
}

### GET /departments
Access: ADMIN, HOD, TEACHER, STUDENT

Response (200):
{
  "items": [
    {
      "id": 1,
      "name": "B.Sc. Data Science",
      "code": "BSC_DS"
    }
  ]
}

### PATCH /departments/{department_id}
Access: ADMIN

Purpose:
Update department information or HOD assignment.

### POST /classes
Access: ADMIN

Request:
{
  "department_id": 1,
  "class_name": "B.Sc. Data Science - Year 2",
  "academic_year": "2026-2027",
  "section": "A"
}

Response (201):
{
  "id": 1,
  "department_id": 1,
  "class_name": "B.Sc. Data Science - Year 2",
  "academic_year": "2026-2027",
  "section": "A"
}

### GET /classes
Access: Authenticated users

Optional query parameters:
- department_id
- academic_year

Response (200):
{
  "items": [
    {
      "id": 1,
      "department_id": 1,
      "class_name": "B.Sc. Data Science - Year 2",
      "academic_year": "2026-2027",
      "section": "A"
    }
  ]
}

Results must be restricted according to user role.

### GET /classes/{class_id}
Access: Authenticated users

Purpose:
Retrieve an authorized class.

### PATCH /classes/{class_id}
Access: ADMIN

Purpose:
Update class details.

### POST /subjects
Access: ADMIN

Request:
{
  "subject_code": "DS201",
  "subject_name": "Python Programming",
  "department_id": 1
}

Response (201):
{
  "id": 1,
  "subject_code": "DS201",
  "subject_name": "Python Programming",
  "department_id": 1
}

### GET /subjects
Access: Authenticated users

Optional query parameters:
- department_id
- class_id

Response (200):
{
  "items": [
    {
      "id": 1,
      "subject_code": "DS201",
      "subject_name": "Python Programming",
      "department_id": 1
    }
  ]
}

### PATCH /subjects/{subject_id}
Access: ADMIN

Purpose:
Update subject information.

### General Rules

- Only ADMIN can create or modify departments,
  classes and subjects.
- HODs can access information within their
  authorized departments.
- Teachers can access information needed for
  their assigned teaching sessions.
- Students can access information related
  to their own enrollment.
- Department codes must be unique.
- Subject codes must be unique.
- Class and subject references must be validated.
- Historical attendance references must be preserved.
- Return 401 for unauthenticated requests.
- Return 403 for unauthorized requests.
- Return 404 for missing or inaccessible records,
  according to the authorization policy.