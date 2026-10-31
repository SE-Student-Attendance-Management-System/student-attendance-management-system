# Student Attendance Management System (SAMS)

A web-based application to manage student information, courses/classes, attendance, attendance calculations, reports, and role-specific dashboards for Administrators, Faculty, and Students.

 **Project status:** **Project status:** The team has selected Python, Django, and PostgreSQL for the implementation. The application setup and core data models are being developed using this stack. Refer to `docs/technology-stack-and-git-workflow.md` for the team's recorded technology decision and Git workflow.

## Project goals

- Centralize attendance records and reduce manual effort.
- Provide role-based access to student, faculty, and administrator functions.
- Keep attendance data accurate and prevent duplicate session records.
- Allow students to access their own attendance history and attendance percentage for each enrolled class.
- Provide authorized users with attendance reports and summaries.

## User roles

| Role | Responsibilities |
|---|---|
| **Administrator** | Manage student, faculty, and course/class information and authorized system-level records. |
| **Faculty** | View assigned classes, mark attendance, manage attendance records as permitted, and access relevant reports. |
| **Student** | View their own attendance records, history, attendance percentages for each enrolled class, and relevant summaries. |

Access to functions is enforced server-side according to the approved SRS (REQ-02) and business rules (BR-01 to BR-05):
- **Unauthenticated requests** to protected routes are redirected (HTTP 302) to the login interface with the original target saved in `?next=`.
- **Authenticated users without permission** receive an immediate **HTTP 403 Forbidden** response.
- **Service-level authorization** restricts attendance marking (BR-03) and modification (BR-05) to Administrators and the specific assigned Faculty member.


## Functional scope and requirements

The following mapping summarizes the 15 functional requirements in SRS v1.0.

| Feature | Requirements | Scope |
|---|---|---|
| Authentication and authorization | REQ-01–REQ-02 | Authenticate registered users and enforce role-based access. |
| Student management | REQ-03–REQ-04 | Add/update, search, and view student records. |
| Course and class management | REQ-05–REQ-06 | Create/update courses/classes, assign faculty, and let faculty view assigned classes. |
| Attendance management | REQ-07–REQ-09 | Mark attendance, store status for a session, prevent duplicate records, and allow authorized modification. |
| Attendance viewing and calculation | REQ-10–REQ-11 | View attendance history and calculate/display attendance percentages. |
| Attendance reports | REQ-12–REQ-13 | Generate and filter reports by the criteria specified in the SRS. |
| Dashboard | REQ-14–REQ-15 | Display role-specific dashboards with system metrics for Admins, assigned class summaries for Faculty, and independent per-class attendance summaries with 75% threshold status for Students. |

Do not add product features beyond the approved SRS without discussing and documenting the scope change.

## Architecture

SAD v1.2 specifies a **layered architecture**:

1. **Presentation layer** — login, role-specific interfaces, student/course screens, attendance forms, reports, and dashboards.
2. **Application/service layer** — authentication and authorization, student/course management, attendance processing, reporting, and dashboards.
3. **Data-access layer** — separates database operations from business logic and supports consistent persistence.
4. **Relational database** — stores users, students, faculty assignments, courses/classes, attendance sessions, and attendance records.

The SAD includes logical REST-style APIs for authentication and attendance. The exact API implementation and database schema are to be finalized during implementation and must remain traceable to the SRS and SAD.

## Non-functional requirements

Implementation and verification should address the following requirements from SRS v1.0:

### Performance

- Major pages such as login and dashboard should load within **3 seconds** under normal operating conditions.
- Attendance marking and display of updated status should complete within **2 seconds** under normal network conditions.
- The application should support multiple simultaneous users without significant performance degradation.
- Reports should be generated within **5 seconds** for normal-sized datasets.

### Security and data integrity

- Require authentication for protected functions.
- Enforce server-side role-based access control.
- Restrict students to their own attendance information.
- Restrict faculty attendance management to assigned classes.
- Never store passwords in plain text.
- Prevent unauthorized attendance modification/deletion and duplicate records.
- Use HTTPS for client/server data transmission where supported.
- Invalidate authenticated sessions on logout.
- Validate attendance data and use consistent persistence operations.

### Usability, reliability and maintainability

- Provide a simple, consistent interface with minimal navigation for common actions.
- Show appropriate messages when validation or an operation fails.
- Keep accurate attendance records and avoid partial updates on failures.
- Use modular architecture and consistent coding standards.

### Scalability and portability

- Support growth in students, courses, classes, and users without major architectural changes.
- Support commonly used modern web browsers.

These requirements must be verified through tests and measured results; they should not be reported as satisfied before execution.


## Technology stack

The current local implementation uses:

- **Language:** Python
- **Web framework:** Django
- **Database:** PostgreSQL
- **Dependency management:** pip and a Python virtual environment

These are the technologies currently used by the implementation.
Refer to `docs/technology-stack-and-git-workflow.md` for the team's formal technology decision.

## Repository documents

| Document | Purpose |
|---|---|
| `Student-Attendance-Management-System-SRS_final.docx` | SRS v1.0 — approved requirements, business rules, interfaces, and NFRs. |
| `Student_Attendance_Management_System_SAD_V1.docx` | SAD v1.2 — layered architecture, component responsibilities, APIs, security and design decisions. |
| `Student_Attendance_Management_System_Test_Plan_v1.1.docx` | Test Plan v1.1 — testing approach, requirement traceability, and existing test cases. |
| `Test Plan Document - Version 1.docx` | Earlier test plan retained for historical reference. |
| `docs/technology-stack-and-git-workflow.md` | Technology selection record and Git collaboration workflow. |

## Development workflow

The team uses GitHub Issues and the **Student Attendance Management System — Sprint Board** to track backlog items, assignees, estimates, status, and sprint.

1. Confirm the assigned issue, requirements, acceptance criteria, estimate, and sprint.
2. Create a feature branch from the latest `main`.
3. Implement the change and run relevant local checks/tests.
4. Commit and push the feature branch.
5. Open a pull request targeting `main`, link the relevant issue, and describe verification performed.
6. Request review and resolve feedback; required automated checks should pass.
7. Merge only after required review and checks, then verify the integrated feature.
8. Update the issue to Done only when its acceptance criteria are met.

See [`docs/technology-stack-and-git-workflow.md`](docs/technology-stack-and-git-workflow.md) for branch naming, Git commands, PR conventions, Kanban statuses, and the Definition of Done.

## Testing

Test planning is based on Test Plan v1.1. Testing covers unit, integration, and system levels, including:

- Authentication and authorization.
- Student and course/class management.
- Attendance marking, duplicate prevention, and authorized modification.
- Attendance history and independent per-class percentage calculation.
- Reports, filters, and dashboards.
- Security, validation, reliability, and performance targets.

Test results must be recorded after execution. Keep actual results and pass/fail statuses blank until a test has been run.



## Setup

### Prerequisites

- Python installed and available in PowerShell.
- PostgreSQL installed and running.
- Git installed.
- The repository cloned locally.

### 1. Open the project directory

Open PowerShell in the project root directory.

### 2. Create and activate a virtual environment

If the virtual environment does not already exist:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file by copying the example:

```powershell
Copy-Item .env.example .env
```

Open `.env`:

```powershell
notepad .env
```

Set the values for your local environment:

```env
DJANGO_SECRET_KEY=replace-with-your-own-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=student_attendance
DB_USER=postgres
DB_PASSWORD=replace-with-your-postgres-password
DB_HOST=127.0.0.1
DB_PORT=5433
```

Replace the placeholder values with your actual local configuration. Keep passwords and secret keys private.

### 5. Create the PostgreSQL database

Connect to PostgreSQL using an account with permission to create databases:

```sql
CREATE DATABASE student_attendance;
```

If the database already exists, do not create it again. Ensure the database user configured in `.env` has the necessary permissions.

### 6. Apply database migrations

Ensure PostgreSQL is running and `.env` contains the correct connection details, then run:

```powershell
python manage.py migrate
```

### 7. Check the configuration

```powershell
python manage.py check
python manage.py migrate --check
```

### 8. Start the development server

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

Stop the server with `Ctrl+C`.

### 9. Run tests

```powershell
python manage.py test attendance
```

Use the team's formally approved technology decision and the actual local environment configuration when setting up another development machine.

**Security:** Never commit `.env` or store real database passwords or production secret keys in source-controlled files. Commit `.env.example` with placeholder values only.

## Team

- **Anirudh M** — Project Manager / QA Lead
- **Ravitejas** — Test Engineer
- **Rahul Devendra Kagawad** — Developer

Project organization: `SE-Student-Attendance-Management-System`
