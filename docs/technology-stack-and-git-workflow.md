# Student Attendance Management System

## Technology Stack and Git Workflow

| Document field | Value |
|---|---|
| Project | Student Attendance Management System (SAMS) |
| Organization | SE-Student-Attendance-Management-System |
| Document owner | Anirudh M — Project Manager / QA Lead |
| Version | 1.0 — Working decision record |
| Date | 14 October 2026 |
| Status | Draft — technology choices require team agreement |
| Related backlog item | Issue #6 — [SETUP] Finalize Technology Stack and Git Workflow |

## 1. Purpose

This document records the implementation technology decision and the Git collaboration workflow for the Student Attendance Management System. It is intended to keep the team aligned during implementation and provide a consistent process for feature development, testing, code review, and integration.

The project requirements and scope remain those defined in the approved SRS. This document does not introduce new product features or change SRS requirements.

## 2. Constraints from the Project Documents

The following constraints are taken from the project's root-level SRS v1.0 and SAD v1.2:

- The system is a web-based application accessed using a standard web browser.
- The SRS permits a backend implemented using **Python with Django or Flask**, or **Java with Spring Boot**.
- A database must provide persistent storage for users, students, faculty, courses/classes, and attendance records.
- The SAD selects a **layered architecture**, separating presentation, application/service logic, data access, and persistent storage.
- Logical API interfaces follow a REST-style HTTP approach.
- HTTP/HTTPS is used for browser-to-application communication; HTTPS should protect credentials and attendance-related data in environments where it is supported.
- Role-based access is required for Administrator, Faculty, and Student users.
- The SAD leaves the exact backend framework and relational DBMS to be finalized before implementation.

The current Test Plan v1.1 is the basis for testing and retains the requirements and test cases. Test execution results must be recorded only after the tests are actually run.

## 3. Technology Selection Record

**Do not treat a choice as final until all three team members have discussed and agreed to it.** The SRS and SAD permit the options below but do not identify a chosen implementation stack.

| Area | Allowed / required by project documents | Team decision | Decision status |
|---|---|---|---|
| Backend framework | Python with Django/Flask, or Java with Spring Boot | **To be recorded after team discussion** | Pending |
| Programming language | Python for Django/Flask, or Java for Spring Boot | **To be recorded after framework selection** | Pending |
| Database | Persistent relational database | **DBMS to be selected by the team** | Pending |
| Frontend | Web UI accessed through a standard browser; exact frontend framework is not specified in the SRS/SAD | **To be agreed if a frontend framework is needed** | Pending |
| API style | Logical REST-style HTTP APIs, as described in SAD v1.2 | Retain REST-style interfaces unless the team documents a justified change | Baseline design |
| Transport | HTTP/HTTPS; use HTTPS for protected data where supported | Configure according to the development/deployment environment | Implementation decision |
| Architecture | Layered architecture: presentation, application/services, data access, relational database | Retain the SAD v1.2 architecture | Selected in SAD |

### 3.1 Final Approval Record

Complete this subsection after the technology discussion.

- **Backend framework:** ____________________________________
- **Programming language:** ____________________________________
- **Relational DBMS:** ____________________________________
- **Frontend approach/framework, if applicable:** ____________________________________
- **Development/runtime version(s):** ____________________________________
- **Date agreed:** ____________________________________
- **Team members who agreed:** Anirudh M / Ravitejas / Rahul Devendra Kagawad
- **Notes or rationale:** ____________________________________

## 4. Architecture Alignment

The implementation should remain consistent with SAD v1.2:

1. The presentation layer handles login, role-specific interfaces, student/course screens, attendance interfaces, and reporting views.
2. Application services implement authentication and authorization, student/course management, attendance processing, reporting, and dashboards.
3. The data-access layer separates database operations from business logic.
4. The relational database stores the persistent system records.
5. Authorization must be enforced on the server side. Hiding a button or screen is not sufficient protection by itself.
6. Attendance changes must be validated, duplicate records prevented, and database operations handled consistently.
7. API details and the schema may be finalized during implementation, but they must remain traceable to the SRS and SAD.

## 5. Git and GitHub Workflow

The team will use the existing GitHub repository and the project board **Student Attendance Management System — Sprint Board**.

### 5.1 Main Branch

- `main` is the stable integration branch.
- Team members should not push routine feature work directly to `main`.
- Changes should be integrated through pull requests (PRs).

### 5.2 Branch Naming

Create a feature branch from the latest `main` for each development issue. Use a descriptive name and, where convenient, include the issue number.

Examples:

- `feature/11-login-session`
- `feature/14-student-records`
- `feature/20-course-management`
- `fix/25-attendance-validation`

Branch names are examples; the issue number and feature description should match the actual work.

### 5.3 Standard Development Steps

1. Open the assigned GitHub Issue and confirm its description, acceptance criteria, SRS references, assignee, estimate, and sprint.
2. Update the issue to **In Progress** when active work begins.
3. Update the local copy of `main` and create a feature branch from it.
4. Implement the assigned work and run the relevant checks/tests locally.
5. Commit changes with a concise, meaningful message. For example: `Implement login session handling (#11)`.
6. Push the feature branch to GitHub.
7. Open a PR targeting `main`, describe the change, list the verification performed, and link the issue. The PR may include `Closes #<issue-number>` when merging it should close that issue.
8. Move the issue to **In Review** when the PR or other reviewable work is ready for review.
9. The repository owner or designated reviewer reviews the change. Resolve requested changes and ensure the required GitHub Actions checks pass.
10. Merge only after required review and checks are complete. Verify the integrated behavior, then mark the issue **Done**.

### 5.4 Pull Request and Review Rules

- Every implementation PR must target `main`.
- The assigned contributor raises the PR; the repository owner/reviewer reviews and merges it, as required by the course deliverables.
- Reviewers should check requirement alignment, correctness, validation, security, maintainability, and relevant tests.
- Do not bypass required human review by relying on GitHub Actions alone.
- If the repository has branch protection or rulesets configured, follow those requirements.
- If a change affects the approved SRS/SAD/Test Plan, document and discuss the deviation before treating it as part of the implementation.

### 5.5 GitHub Actions

GitHub Actions should run relevant automated checks on pushes and pull requests. The exact commands must be configured after the team finalizes the stack. Checks may include dependency installation, build/compile, linting, and automated tests, where supported by the selected project setup.

A passing workflow does not replace pull-request review or manual/system testing.

## 6. GitHub Project Status Conventions

The Kanban board tracks progress; the Sprint field tracks planned timing.

| Status | Meaning | When to use it |
|---|---|---|
| Backlog | Identified work not yet selected or ready | Work is recorded but not yet planned/ready |
| Ready | Work is defined and can be started | Scope, assignee, and dependencies are clear |
| In progress | Active work has begun | The assignee is currently working on it |
| In review | Work is ready for review | A PR or other reviewable deliverable is awaiting review |
| Done | Work is accepted and completed | Required review, merge (for code), and verification are complete |

Each assignee is responsible for keeping their issue status and progress notes accurate. The Project Manager monitors overall progress, checks for blockers and overdue work, and coordinates review and integration.

## 7. Definition of Done

A backlog item can be marked Done when the applicable points below are satisfied:

- The stated acceptance criteria are met.
- The implementation follows the approved SRS and SAD and does not silently introduce scope changes.
- Relevant automated checks and applicable Test Plan cases have been run; results reflect actual execution.
- The pull request is reviewed and merged for code changes.
- Any discovered defects are recorded and handled according to the agreed plan.
- Relevant documentation is updated when necessary.
- The integrated feature has been verified.

For planning-only tasks that do not change code, completion means the agreed decision or deliverable is documented and reviewed by the team; a code PR is not required unless the team chooses to manage that document change through a PR.

## 8. Related Project Documents

- **Student-Attendance-Management-System-SRS_final.docx** — SRS v1.0, including the permitted backend technologies and functional/non-functional requirements.
- **Student_Attendance_Management_System_SAD_V1.docx** — SAD v1.2, including the layered architecture, component responsibilities, API design, security, and open implementation decisions.
- **Student_Attendance_Management_System_Test_Plan_v1.1.docx** — current test plan and test-case references.

## 9. Change History

| Version | Date | Owner | Change summary |
|---|---|---|---|
| 1.0 | 14 October 2026 | Anirudh M | Initial technology-selection and Git workflow record prepared for team review. Technology and database choices remain pending until agreed by the team. |
