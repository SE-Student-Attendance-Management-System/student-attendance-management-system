# Student Attendance Management System (SAMS)

A web-based application to manage student information, courses/classes, attendance, attendance calculations, reports, and role-specific dashboards for Administrators, Faculty, and Students.

> **Project status:** Requirements and design documents are available. The exact implementation stack must be confirmed by the team and recorded in [`docs/technology-stack-and-git-workflow.md`](docs/technology-stack-and-git-workflow.md).

## Project goals

- Centralize attendance records and reduce manual effort.
- Provide role-based access to student, faculty, and administrator functions.
- Keep attendance data accurate and prevent duplicate session records.
- Allow students to access their own attendance history and percentage.
- Provide authorized users with attendance reports and summaries.

## User roles

| Role | Responsibilities |
|---|---|
| **Administrator** | Manage student, faculty, and course/class information and authorized system-level records. |
| **Faculty** | View assigned classes, mark attendance, manage attendance records as permitted, and access relevant reports. |
| **Student** | View their own attendance records, history, percentage, and relevant summaries. |

Access to functions must be enforced server-side according to the approved SRS and business rules.

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
| Dashboard | REQ-14–REQ-15 | Display role-specific dashboards and relevant attendance summaries. |

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

The SRS allows Python with Django/Flask or Java with Spring Boot, and requires persistent database storage. SAD v1.2 leaves the specific framework and DBMS to be finalized.

The team should review and approve the proposed stack recorded in [`docs/technology-stack-and-git-workflow.md`](docs/technology-stack-and-git-workflow.md) before implementation. Do not treat an option in that document as selected until the team's final approval record is completed.

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
- Attendance history and percentage calculation.
- Reports, filters, and dashboards.
- Security, validation, reliability, and performance targets.

Test results must be recorded after execution. Keep actual results and pass/fail statuses blank until a test has been run.

## Setup

The final stack and runtime versions are still to be confirmed by the team. Once approved, this section should be updated with accurate installation instructions, required environment variables, database creation/migration steps, test commands, and run commands. Do not put passwords, API keys, or other secrets into this repository.

## Team

- **Anirudh M** — Project Manager / QA Lead
- **Ravitejas** — Test Engineer
- **Rahul Devendra Kagawad** — Developer

Project organization: `SE-Student-Attendance-Management-System`
