
# Authentication and Authorization Contract
Version: 1.0

## Application Modules
1. Admin Module
2. Student Module

## User Roles

### ADMIN
- Manage students and teachers.
- Manage departments, classes, subjects and timetables.
- Configure semester dates and attendance policies.
- Manage authorized attendance corrections.
- Configure attendance fines.
- Access administrative reports.

### HOD
- View attendance within the assigned department.
- Review department attendance reports.
- Review and approve eligible examination exceptions.
- Record reasons for eligibility decisions.

### TEACHER
- View assigned classes, subjects and periods.
- Access attendance for assigned sessions.
- Correct Present, Absent and OD statuses.
- Make corrections only for assigned sessions,
  during the period or before that day's correction deadline.
- Provide a reason for every correction.

### STUDENT
- View personal profile.
- View overall attendance percentage.
- View subject-wise and period-wise attendance.
- View absence dates and assigned teachers.
- View approved leave balance.
- View fine and examination eligibility status.
- Cannot modify attendance records.

## Authentication

- Each user has a unique login ID.
- Passwords must be securely hashed.
- The backend verifies user credentials.
- Protected endpoints require authentication.
- Every protected endpoint enforces role permissions.
- Students can access only their own records.
- Authentication errors must not expose passwords
  or reveal whether an account exists.

## Attendance Authorization

Teacher attendance corrections require:
1. A valid authenticated teacher account.
2. An authorized timetable assignment.
3. A matching class, subject, date and period.
4. A correction submitted within the permitted deadline.
5. A recorded correction reason.

Every correction must preserve an audit trail.

## Security

- Never store plaintext passwords.
- Never commit real credentials or biometric records.
- Protect student personal information.
- Restrict access to face enrollment data.
- Maintain authentication and attendance audit logs.