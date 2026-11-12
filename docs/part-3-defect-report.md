# Part 3 — Defect & Resolution Report

- **Project:** Student Attendance Management System (SAMS)
- **Repository:** `SE-Student-Attendance-Management-System/student-attendance-management-system`
- **Evaluation Milestone:** Part 3 – Testing & Quality Assurance
- **Tested Branch:** `main`
- **Tested Commit SHA:** `d9618ef1ba99ba0a448a39140e69d25aaddda1dc`
- **Execution Date:** 07 November 2026 (Updated: 12 November 2026 for Independent Audit Corrections)
- **Test Suite Execution:** 183 automated tests discovered; 182 passed, 1 error on local SQLite; 3 programmatic workflows passed; 4 benchmark suites passed

--- 

## 1. Defect Logging Policy & Scope

This report documents all defects observed during sprint development, integration testing, and Part 3 Quality Assurance activities.

> [!CAUTION]
> **Defect-Free Disclaimer:** A clean execution run with zero test failures confirms that all tested assertions and scenarios functioned as expected. It does **not** constitute proof that the software is completely free of defects. Edge cases that were blocked or partially covered (such as live physical database disconnections or browser rendering quirks) may reveal defects during future staging or production operations.

--- 

## 2. Historical Sprint Defects & Retest Status

During earlier sprints, two primary functional defects were identified and resolved before Part 3 QA. Both were subjected to automated retesting on `main`:

### Defect DEF-01: Admin Assigned Sections Query Error on Attendance Sessions View
- **Issue Reference:** Issue #36 / PR #51
- **Severity:** Medium (Template / View logic flaw)
- **Description:** On the attendance sessions page (`/attendance/`), the view logic attempted to retrieve `admin_sections` for faculty users when rendering attendance session controls, leading to improper query scoping and potential context errors.
- **Resolution:** Updated `attendance/views.py` (`attendance_sessions`) to properly distinguish user roles: `admin_sections` is only populated for users with role `ADMIN`; faculty users strictly receive assigned sections via `request.user.faculty_profile.class_sections`.
- **Retest Evidence:** Verified in `attendance/test_dashboards.py`:
  - `test_admin_attendance_sessions_has_admin_sections_defect_01`: **PASS**
  - `test_faculty_attendance_sessions_admin_sections_is_none`: **PASS**
- **Status:** **RESOLVED & VERIFIED**

--- 

### Defect DEF-02: Overall Student Attendance Percentage Display Violating Institutional Policy
- **Issue Reference:** Issue #36 / PR #51
- **Severity:** High (Business rule compliance violation)
- **Description:** Earlier student dashboard implementations displayed an aggregate overall attendance rate calculated across all courses. Institutional policy dictates that student attendance must be evaluated **strictly independently for each enrolled class section**, with a minimum threshold of 75.0% per class section. Aggregating attendance across disparate courses obscured low attendance in individual subjects.
- **Resolution:** Overhauled student dashboard context in `attendance/views.py` (`home`) and template `attendance/templates/home.html`. Removed all overall/aggregate percentage cards. Each enrolled class is rendered as an independent attendance card showing:
  - Course Code & Name
  - Section & Academic Term
  - Total Sessions Held
  - Sessions Attended & Absent
  - Independent Attendance Percentage
  - Policy Status Badge (`Good Standing` for >= 75.0%, `Low Attendance` for < 75.0%, `N/A` for 0 sessions)
- **Retest Evidence:** Verified in `attendance/test_dashboards.py`:
  - `test_student_dashboard_independent_class_attendance_calculation`: **PASS**
  - `test_student_dashboard_attendance_policy_boundary_75_percent`: **PASS**
  - `test_student_dashboard_metrics_context`: **PASS**
- **Status:** **RESOLVED & VERIFIED**

--- 

## 3. Part 3 Quality Assurance Defect Log & Unresolved Investigations

During Part 3 test suite executions on synchronized `main` (`d9618ef`):
- **Total Automated Tests Discovered:** 183
- **Total Passed:** 182
- **Total Failed:** 0
- **Total Errors:** 1 (Local in-memory SQLite concurrency lock)
- **Total Programmatic Functional Workflows Executed:** 3 (Admin, Faculty, Student) — 0 Failures
- **Total Performance Latency Benchmarks Executed:** 4 suites (20 iterations total) — 0 Latency Breaches

### Investigation INV-01: SQLite In-Memory Database Lock in Concurrent Marking Test
- **Incident Reference:** Fresh execution on Windows / SQLite in-memory (`config.test_settings`)
- **Impacted Test:** `AttendanceConcurrencyTests.test_concurrent_duplicate_attendance_creates_only_one_record` in `attendance/tests.py`
- **Observed Output:** `sqlite3.OperationalError: database table is locked` / `django.db.utils.OperationalError: database table is locked`
- **Classification:** **Unresolved Test-Environment / Concurrency Investigation** (Not confirmed application code defect).
- **Technical Root-Cause Analysis:** SQLite enforces a coarse-grained, single-writer database lock. When multiple worker threads in `ThreadPoolExecutor` execute simultaneous inserts against `:memory:`, a thread contending for the lock fails with `database table is locked`.
- **Remediation & Verification Requirement:** PostgreSQL CI results (Run ID `41309345461`) reported success, but exact raw job step logs must be inspected to verify that PostgreSQL row-level locking handles this concurrency cleanly without deadlocks.

--- 

## 4. Unexecuted / Blocked Scenarios Subject to Future Testing (10 Scenarios)

The following 10 formal scenarios were identified as blocked or unexecuted due to host environment limitations or deferred institutional policy:

| # | Case ID | Req ID | Scenario | Technical Blocker | Required Remediation |
|---:|---|---|---|---|---|
| 1 | `ST-07-06` | **REQ-07** | Faculty completes attendance workflow through UI | Interactive browser GUI automation harness (Selenium/Playwright) is not installed in the workspace environment. | Configure headless browser driver and execute automated DOM form interaction. |
| 2 | `UT-07-08` | **REQ-07** | Invalid class/section identifier format rejected on marking endpoint | No dedicated automated test submitting malformed section IDs to attendance marking view exists. | Implement test submitting non-integer/alphanumeric section identifiers to the attendance marking URL. |
| 3 | `UT-08-02` | **REQ-08** | Missing status rejected on attendance submission | Reconciled with Issue #40 Section 8: no dedicated test submitting an empty status choice exists. | Implement test submitting an attendance payload where student status is empty/omitted. |
| 4 | `IT-08-05` | **REQ-08** | Invalid session date rejected | No dedicated automated test submitting invalid date format to session form exists. | Implement test submitting invalid date strings (e.g., '2026-02-31', 'invalid-date') to the marking view. |
| 5 | `ST-08-06` | **REQ-08** | Bulk attendance for 50 students performance | Dedicated 50-student UI form submission test unexecuted (500-row report benchmark tested instead). | Construct synthetic 50-student roster fixture and benchmark attendance POST latency. |
| 6 | `UT-08-07` | **REQ-08** | Oversized Attendance ID handled safely | Dedicated parameter boundary test on attendance record ID unexecuted. | Implement test passing 2^63 integer boundary values to attendance detail/update views. |
| 7 | `ST-09-08` | **REQ-09** | Rapid consecutive modifications handled correctly | Dedicated high-concurrency race condition test for rapid successive updates unexecuted. | Implement multithreaded test with threading barriers targeting simultaneous update POST requests. |
| 8 | `UT-10-02` | **REQ-10** | History dates use required display format | Date formatting visually inspected in template; dedicated automated assertion unexecuted. | Add programmatic assertion verifying rendered HTML matches 'DD Mon YYYY' date format specification. |
| 9 | `UT-10-03` | **REQ-10** | History pagination handles 100+ records | Dedicated pagination boundary test with 100+ attendance records unexecuted. | Seed 105 attendance records for a student and verify page 1/page 2 boundary navigation. |
| 10 | `ST-11-02` | **REQ-11** | Corrupted database status handled gracefully | Request boundaries reject invalid statuses; deterministic handling of pre-corrupted DB rows deferred per RTM-08. | Institutional policy decision required on whether corrupted status is mapped to Absent or excluded. |

--- 

## 5. Partially Covered Scenarios Subject to Live Staging Verification (13 Scenarios)

The following 13 formal scenarios received automated service or unit test coverage, but full end-to-end verification requires live infrastructure:

| # | Case ID | Req ID | Scenario | Automated Coverage | External Gap / Live Staging Requirement |
|---:|---|---|---|---|---|
| 1 | `IT-01-02` | **REQ-01** | Login with database server unavailable | `attendance/tests.py:test_update_view_handles_database_failure_safely` | Simulated db error response in services/views (attendance/tests.py:test_update_view_handles_database_failure_safely); live physical database server disconnection during login not executed. |
| 2 | `ST-01-02` | **REQ-01** | Data encryption during login (HTTPS) | `config/settings.py & attendance/test_security.py:CSRFProtectionSecurityTests` | CSRF cookies and secure cookie settings verified in settings; live TLS/HTTPS termination requires live web server. |
| 3 | `UT-07-01` | **REQ-07** | Faculty views assigned class sections | `attendance/test_faculty_assignment.py:test_faculty_sees_own_assigned_classes` | Assigned class section visibility verified in tests; full interactive marking form UI partial. |
| 4 | `UT-07-04` | **REQ-07** | Empty/invalid enrollment scenario | `attendance/tests.py:test_reject_attendance_for_unenrolled_student` | Rejection of unenrolled student verified at service level; empty roster UI notice partial. |
| 5 | `IT-07-05` | **REQ-07** | Integrated marking workflow persists attendance | `attendance/tests.py:test_assigned_faculty_can_mark_attendance` | Service-level creation covered; full formal integration sequence via UI partial. |
| 6 | `UT-08-01` | **REQ-08** | Status selection control offers supported choices | `attendance/templates/attendance/attendance_mark.html` | Template inspected with status dropdown (PRESENT/ABSENT); dedicated rendered form test partial. |
| 7 | `IT-08-04` | **REQ-08** | ABSENT status stored through specified workflow | `attendance/tests.py:test_update_attendance_creates_audit_record` | Modification test changes PRESENT to ABSENT and asserts persistence; initial direct marking page test partial. |
| 8 | `ST-08-08` | **REQ-08** | Database failure during attendance save | `attendance/tests.py:test_mark_attendance_rolls_back_on_database_failure` | Injected database rollback tested (test_mark_attendance_rolls_back_on_database_failure); live physical database disconnection during commit not executed. |
| 9 | `ST-09-02` | **REQ-09** | UI presents existing record in edit workflow | `attendance/templates/attendance/attendance_mark.html & attendance_update.html` | Template inspected with edit links; full browser edit workflow partial. |
| 10 | `IT-09-05` | **REQ-09** | Integrated duplicate prevention and modification | `attendance/tests.py:test_duplicate_attendance_is_rejected & test_update_attendance_creates_audit_record` | Duplicate prevention and modification/audit pass separately; full formal sequence partial. |
| 11 | `IT-10-01` | **REQ-10** | Newly recorded attendance appears in history | `attendance/tests.py:StudentAttendanceHistoryTests & AttendanceServiceTests` | History and attendance creation tested separately; single integrated test partial. |
| 12 | `IT-10-02` | **REQ-10** | History reflects later attendance modification | `attendance/tests.py:test_update_attendance_creates_audit_record & StudentAttendanceHistoryTests` | Modification and history tested separately; single integrated test partial. |
| 13 | `ST-11-01` | **REQ-11** | Student dashboard displays attendance summary | `attendance/test_dashboards.py:test_student_dashboard_metrics_context` | Metrics context tested in dashboard tests; formal end-to-end system UI steps partial. |
