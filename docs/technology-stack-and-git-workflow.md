# Student Attendance Management System (SAMS)
## Technology Stack and Git Workflow

| Document field | Value |
|---|---|
| Project | Student Attendance Management System (SAMS) |
| Organization | `SE-Student-Attendance-Management-System` |
| Document owner | Anirudh M — Project Manager / QA Lead |
| Version | 1.1 — Working decision record |
| Date | 17 October 2026 |
| Status | Draft — team technology decision pending |
| Related backlog item | Issue #6 — `[SETUP] Finalize Technology Stack and Git Workflow` |

## 1. Purpose

This document records the technology options, the recommended implementation stack for team discussion, and the agreed process for Git collaboration. It is intended to keep implementation, testing, review, and integration consistent across the team.

The approved SRS remains the authority for project scope and requirements. This document does not add product features or change REQ-01 through REQ-15.

## 2. Constraints from the project documents

The root-level SRS v1.0 and SAD v1.2 establish the following:

- SAMS is a web application accessed through a standard web browser.
- The permitted backend options are Python with Django/Flask or Java with Spring Boot.
- A persistent database is required for users, students, faculty, courses/classes, and attendance information.
- The architecture follows a layered structure: presentation, application/services, data access, and persistent storage.
- The SAD specifies logical REST-style HTTP APIs.
- Role-based authorization is required for Administrator, Faculty, and Student.
- Passwords must not be stored in plain text, and protected data should use HTTPS where supported.
- The exact backend framework and relational DBMS must be recorded after the team makes its decision.

The Test Plan v1.1 provides the testing basis. Actual results and pass/fail values must be recorded only after tests are executed.

## 3. Recommended stack for team discussion

The following is a **recommendation, not a finalized team decision**. The team should review it with the mentor and complete Section 3.1 before treating it as selected.

| Area | Proposed choice | Reason / status |
|---|---|---|
| Programming language | Python | Matches one of the options permitted by the SRS. |
| Backend framework | Django | Provides routing, sessions, form handling, authentication support, and ORM capabilities for a compact web application. **Proposed; team approval required.** |
| Database | PostgreSQL | Relational database suitable for foreign keys, uniqueness constraints, and transactions. **Proposed; team approval required.** |
| Frontend | Django templates, HTML, CSS, Bootstrap, and JavaScript | Keeps the UI in the same application and avoids requiring a separate frontend framework. **Proposed.** |
| API implementation | Django REST Framework where needed for the logical REST-style APIs | Provides serializers, request validation, and structured API responses. **Proposed; confirm against the final API plan.** |
| Version control and collaboration | Git and GitHub | Repository, issues, project board, branches, pull requests, and reviews. |
| Automated checks | GitHub Actions | Run the checks supported by the selected stack on pushes and pull requests. |
| Manual API verification | Postman or equivalent | Exercise API requests and inspect responses, where APIs are exposed. |
| UML documentation | draw.io | Maintain architecture and UML diagrams. |

If the team selects another permitted backend or a different relational DBMS, update this table and document the rationale before implementation proceeds.

### 3.1 Final team approval record

Complete this section after discussion.

- **Backend framework:** Pending team agreement
- **Programming language:** Pending framework decision
- **Relational DBMS:** Pending team agreement
- **Frontend approach:** Pending team agreement
- **API implementation approach:** Pending team agreement
- **Runtime/tool versions:** Record the versions used by the team
- **Date agreed:** Pending
- **Team members who agreed:** Anirudh M / Ravitejas / Rahul Devendra Kagawad
- **Rationale or constraints:** Record the team's actual rationale here

## 4. Architecture alignment

Implementation should remain consistent with SAD v1.2:

1. **Presentation layer:** login, role-specific interfaces, student/course screens, attendance interfaces, reports, and dashboards.
2. **Application/service layer:** authentication and authorization, student/course management, attendance processing, reporting, and dashboard functions.
3. **Data-access layer:** separates database operations from business logic and supports consistent persistence.
4. **Relational database:** stores system records and relationships.
5. **Server-side authorization:** protected operations must check the authenticated user's role and relevant class assignment; hiding a UI control alone is not sufficient.
6. **Attendance integrity:** validate status and session information, prevent duplicate attendance, and handle updates consistently.
7. **Traceability:** API contracts, database structures, and implementation choices must remain traceable to the SRS and SAD.

## 5. Git and GitHub workflow

The team will use the existing repository and the GitHub Project board **Student Attendance Management System — Sprint Board**.

### 5.1 Main branch

- `main` is the stable integration branch.
- Routine feature work should not be pushed directly to `main`.
- Changes should be integrated through pull requests (PRs), subject to the repository's rules and course requirements.

### 5.2 Branch naming

Create a branch from the latest `main` for each development issue. Use a descriptive name; include the issue number when practical.

Examples:

- `feature/11-login-session`
- `feature/14-student-records`
- `feature/20-course-management`
- `fix/25-attendance-validation`
- `docs/tech-stack-git-workflow`

These are examples; use the actual issue number and work description.

### 5.3 Standard workflow

1. Open the assigned issue and confirm its description, acceptance criteria, SRS references, assignee, estimate, and sprint.
2. Move the issue to **In Progress** when active work begins.
3. Update local `main` and create a branch.

   ```bash
   git switch main
   git pull origin main
   git switch -c feature/<issue-number>-short-description
   ```

4. Implement the change and run relevant checks/tests locally.
5. Commit with a meaningful message.

   ```bash
   git add <files>
   git commit -m "Describe the change"
   ```

6. Push the branch.

   ```bash
   git push -u origin feature/<issue-number>-short-description
   ```

7. Open a PR targeting `main`. Describe the change, link the issue, and state what verification was performed.
8. Move the issue to **In Review** when the PR or other reviewable deliverable is ready.
9. The repository owner or designated reviewer checks requirement alignment, correctness, security, maintainability, relevant tests, and automated results.
10. Resolve review feedback and merge only after the required review and checks pass.
11. Verify the integrated behavior, then mark the issue **Done**.

For document-only/planning work, a PR can be used when the team agrees to review the document through GitHub. The issue should not be marked Done until the decision/deliverable is reviewed and recorded.

### 5.4 Pull request rules

- Implementation PRs target `main`.
- The assigned contributor raises the PR; the repository owner/designated reviewer reviews and merges it in line with the course deliverables.
- Link the PR to its issue. Use `Closes #<issue-number>` only when merging the PR should close that issue.
- Do not use force pushes to bypass a rejected update or overwrite teammates' work.
- Do not bypass human review by relying on GitHub Actions alone.
- If a change alters the approved SRS, SAD, or Test Plan, discuss and document the deviation before adopting it.

### 5.5 GitHub Actions

Configure automated checks after the technology stack is finalized. Appropriate checks may include dependency installation, build/compile, linting, and automated tests, where supported. A passing workflow does not replace pull-request review or manual/system testing.

## 6. GitHub Project status conventions

The Kanban board tracks **progress**. The Sprint field tracks **when the work is planned**.

| Status | Meaning | When to use it |
|---|---|---|
| Backlog | Identified work not yet selected or ready | Work is recorded but not yet planned/ready |
| Ready | Work is defined and can be started | Scope, assignee, and dependencies are clear |
| In Progress | Active work has begun | The assignee is currently working on it |
| In Review | Work is ready for review | A PR or other reviewable deliverable is awaiting review |
| Done | Work is accepted and completed | Required review, merge for code, and verification are complete |

Each assignee keeps their issue status and progress notes accurate. The Project Manager monitors overall progress, checks blockers, and coordinates review and integration.

## 7. Definition of Done

A backlog item may be marked Done when applicable conditions are satisfied:

- The acceptance criteria are met.
- The work follows the approved SRS and SAD without silently adding scope.
- Relevant automated checks and applicable Test Plan cases have been run; results reflect actual execution.
- Code changes have been reviewed and merged.
- Discovered defects are recorded and handled according to the agreed plan.
- Relevant documentation is updated.
- The integrated behavior is verified.

For planning-only tasks, completion means the agreed decision or deliverable is documented and reviewed; a code PR is not inherently required unless the team chooses to use one.

## 8. Related documents

- `Student-Attendance-Management-System-SRS_final.docx` — SRS v1.0.
- `Student_Attendance_Management_System_SAD_V1.docx` — SAD v1.2.
- `Student_Attendance_Management_System_Test_Plan_v1.1.docx` — current test plan.
- `Test Plan Document - Version 1.docx` — earlier test plan, retained for historical continuity.

## 9. Change history

| Version | Date | Owner | Change summary |
|---|---|---|---|
| 1.0 | 14 October 2026 | Anirudh M | Initial technology-selection and Git workflow record; decisions pending team agreement. |
| 1.1 | 17 October 2026 | Anirudh M | Added explicit proposed stack for discussion, implementation alignment, command examples, PR guidance, status conventions, and Definition of Done. Technology decisions remain pending until agreed by the team. |
