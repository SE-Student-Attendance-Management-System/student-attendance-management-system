# Part 3 — Test Execution & Evidence Report

- **Project:** Student Attendance Management System (SAMS)
- **Repository:** `SE-Student-Attendance-Management-System/student-attendance-management-system`
- **Evaluation Milestone:** Part 3 – Testing & Quality Assurance
- **Tested Branch:** `main`
- **Tested Commit SHA:** `d9618ef1ba99ba0a448a39140e69d25aaddda1dc`
- **Local Test Execution Environment:** Windows 11 Pro, Python 3.12.10, Django 5.2.18, SQLite in-memory (`config.test_settings`)
- **Remote CI Execution Environment:** Ubuntu Linux, GitHub Actions Run ID `41309345461`, PostgreSQL 16 container (`postgres:16`)
- **Date:** 07 November 2026 (Updated: 12 November 2026 for Independent Audit Corrections)

## 1. Executive Summary & Verification Methodology

This document provides verifiable evidence of the test execution conducted for **Part 3 – Testing & Quality Assurance**.

> [!IMPORTANT]
> **Testing Methodology & Environment Disclosure:**
> All automated test runs, functional workflows, and performance latency benchmarks were conducted programmatically via Django's test execution framework and test client (`django.test.Client`).
> Testing verified HTTP response status codes, redirect targets, session cookies, database model persistence, transaction rollback, and HTML context dictionaries. **No manual browser testing, physical browser clicking, or headless browser automation (Selenium/Playwright) was performed.**

### Three-Tier Scope Accounting Reconciliation

1. **115 Formal Acceptance Test Scenarios (STP v1.1):**
   - **PASS:** 92 (80.0%)
   - **PARTIAL:** 13 (11.3%)
   - **BLOCKED / NOT EXECUTED:** 10 (8.7%)
   - **FAIL:** 0 (0.0%)
   - **Total:** Exactly 115 unique test IDs evaluated.
2. **183 Automated Django Test Methods:**
   - Exactly 183 automated test methods exist across 9 test modules on `main` (verified by AST parsing).
   - Latest local SQLite execution on `d9618ef`: 182 Passed, 0 Failed, 1 Error (`sqlite3.OperationalError: database table is locked` in `AttendanceConcurrencyTests.test_concurrent_duplicate_attendance_creates_only_one_record`), Exit Code: 1.
3. **40 Issue #40 Integration Scenarios:**
   - Evaluated under Issue #40 covering REQ-07 through REQ-11. Original classification: **19 PASS, 11 PARTIAL, 10 BLOCKED** (with Table 3 listing 12 partial / 9 blocked and Section 8 detailing `UT-08-02` as blocked). Fully reconciled as a proper subset of the 115 acceptance baseline.

--- 

## 2. Complete Automated Regression Test Suite Inventory (183 Tests)

The automated regression test suite on `main` contains **183 discrete test methods** across 9 test modules, verified via Abstract Syntax Tree (AST) parsing:

| Module Path | Test Count | Functional Domain & Architectural Layer |
|---|---:|---|
| `attendance/tests.py` | **37** | Unit, service, and integration tests for authentication, attendance marking, update audit, transactions, and history. |
| `attendance/test_authorization.py` | **19** | Strict role-based access control (Admin vs Faculty vs Student), Business Rules BR-01 to BR-05, and permission helpers. |
| `attendance/test_course_views.py` | **13** | Course and ClassSection management, unique course code validation, faculty assignment, semester boundaries, and non-admin access denial. |
| `attendance/test_dashboards.py` | **20** | Role-specific dashboards (Admin, Faculty, Student), empty states, independent 75% attendance policy calculations (DEF-02), and response times. |
| `attendance/test_faculty_assignment.py` | **3** | Faculty assigned class visibility, data isolation between faculty, and unassigned faculty empty state. |
| `attendance/test_reports.py` | **33** | Attendance report generation, role-scoping, date/course/section/USN filtering, Appendix B fields, validation errors, and 500-row performance benchmark. |
| `attendance/test_security.py` | **27** | Authentication redirects, session invalidation, CSRF protection, URL query tampering prevention, cross-student peer isolation, and direct service invocation guards. |
| `attendance/test_student_management.py` | **16** | Admin student CRUD, required fields validation, 15-char USN enforcement, malformed email/phone rejection, and duplicate prevention. |
| `attendance/test_student_search.py` | **15** | Case-insensitive USN exact search, partial name search, detail view rendering at maximum field lengths, and peer isolation. |
| **Total Automated Tests** | **183** | **Exact sum verified via AST parsing** |

### Mapping Architecture of Automated Tests to Formal Acceptance Cases

- **Many-to-One Relationships:** In multiple instances, several automated tests verify distinct technical boundary conditions for a single formal case. For example, `test_required_fields_cannot_be_blank`, `test_malformed_email_and_phone_are_rejected`, and `test_usn_must_be_alphanumeric_and_at_most_15_characters` in `test_student_management.py` together validate formal case `UT-03-02` and `UT-03-03`.
- **One-to-Many Relationships:** High-level security integration tests, such as `test_unauthenticated_requests_to_all_protected_endpoints_redirect_to_login`, systematically iterate through 16 protected URL endpoints, simultaneously verifying `ST-02-01`, `ST-10-03`, `ST-12-03`, `ST-13-07`, and `ST-14-07`.
- **One-to-One Relationships:** Targeted business rule tests, such as `test_duplicate_attendance_is_rejected` (`IT-09-01`) or `test_normal_sized_report_generation_under_five_seconds` (`ST-12-04`), map directly to one formal scenario.

--- 

## 3. Reconciliation of Issue #40 Integration Test Scenarios (40 Cases)

### 3.1 Investigation of Earlier vs. Later Classifications (19 PASS vs. 27 PASS)

In `docs/issue-40-attendance-integration-test-report.md` Section 4, the official coverage totals were recorded as:
- **Pass (automated):** 19
- **Partial:** 11
- **Blocked / not executed:** 10
- **Total:** 40

In subsequent sprint summaries, a preliminary classification of **27 PASS / 3 PARTIAL / 10 BLOCKED** was discussed. An independent audit reveals that **exactly eight test cases** were considered for promotion from PARTIAL to PASS:

| Case ID | Issue #40 Original Status | Proposed Status | Audited Final Status | Technical Audit Finding & Justification |
|---|---|---|---|---|
| `UT-07-01` | Partial | PASS | **PARTIAL** | Verifies assigned-class visibility in faculty assignment tests; full interactive marking form UI flow remains unexecuted. |
| `UT-07-04` | Partial | PASS | **PARTIAL** | Rejection of unenrolled student verified at service level; empty-list UI notice in browser remains unexecuted. |
| `UT-08-01` | Partial | PASS | **PARTIAL** | Template inspected with status dropdown (PRESENT/ABSENT); dedicated rendered form submission test remains partial. |
| `ST-08-08` | Partial | PASS | **PARTIAL** | Injected DatabaseError rollback verified in tests; physical TCP/database connection drop during commit was unexecuted. |
| `ST-09-02` | Partial | PASS | **PARTIAL** | Templates inspected with edit links; full browser edit workflow remains unexecuted. |
| `IT-10-01` | Partial | PASS | **PARTIAL** | Attendance marking and student history pass separately; single combined end-to-end integration test remains unexecuted. |
| `IT-10-02` | Partial | PASS | **PARTIAL** | Attendance modification and student history pass separately; single combined update-and-view integration test remains unexecuted. |
| `ST-11-01` | Partial | PASS | **PARTIAL** | Context metrics tested in dashboard tests; formal end-to-end system UI steps remain partial. |

> [!CAUTION]
> **Audit Decision:** Because standalone execution evidence for the full browser/physical conditions of these 8 cases was not supplied, they are **not silently promoted to PASS**. The conservative classification of **PARTIAL** is strictly maintained for all eight cases.

### 3.2 Authoritative 40-Case Reconciliation Matrix (REQ-07 through REQ-11)

| Case ID | Req ID | Scenario Summary | Issue #40 Recorded Status | Part 3 Final Status | Reconciliation & Technical Justification |
|---|---|---|---|---|---|
| `UT-07-01` | **REQ-07** | Verify faculty can view the list of their assigned classes to mark attendance (REQ-07). | Partial | **PARTIAL** | Assigned class section visibility verified in tests; full interactive marking form UI partial. |
| `UT-07-02` | **REQ-07** | Verify faculty cannot mark attendance for classes not assigned to them (BR-03). | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/test_authorization.py:test_br03_unassigned_faculty_denied_marking_attendance`). |
| `IT-07-03` | **REQ-07** | Verify system retrieves the correct enrolled students for a selected assigned class. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_mark_attendance_for_enrolled_student`). |
| `UT-07-04` | **REQ-07** | Verify UI behavior when an assigned class has zero enrolled students. | Partial | **PARTIAL** | Rejection of unenrolled student verified at service level; empty roster UI notice partial. |
| `IT-07-05` | **REQ-07** | Verify database API returns correct class records based on a specific Faculty ID. | Partial | **PARTIAL** | Service-level creation covered; full formal integration sequence via UI partial. |
| `ST-07-06` | **REQ-07** | Verify end-to-end navigation from login to the Mark Attendance interface. | Blocked / not executed | **BLOCKED / NOT EXECUTED** | Interactive browser GUI automation harness (Selenium/Playwright) is not installed in the workspace environment. |
| `ST-07-07` | **REQ-07** | System: Verify faculty cannot mark attendance for a class not assigned to them (BR-03). | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/test_security.py:test_faculty_cannot_mark_attendance_for_unassigned_section_session`). |
| `UT-07-08` | **REQ-07** | Verify system handles invalid class ID formats gracefully during attendance marking. | Blocked / not executed | **BLOCKED / NOT EXECUTED** | No dedicated automated test submitting malformed section IDs to attendance marking view exists. |
| `UT-08-01` | **REQ-08** | Verify UI allows faculty to select 'Present' or 'Absent' status for a student (REQ-08). | Partial | **PARTIAL** | Template inspected with status dropdown (PRESENT/ABSENT); dedicated rendered form test partial. |
| `UT-08-02` | **REQ-08** | Verify validation error if a mandatory attendance status is missing before saving. | Partial | **BLOCKED / NOT EXECUTED** | Reconciled with Issue #40 Section 8: no dedicated test submitting an empty status choice exists. |
| `IT-08-03` | **REQ-08** | Verify system successfully saves a 'Present' status to the database. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_mark_attendance_for_enrolled_student`). |
| `IT-08-04` | **REQ-08** | Verify system successfully saves an 'Absent' status to the database. | Partial | **PARTIAL** | Modification test changes PRESENT to ABSENT and asserts persistence; initial direct marking page test partial. |
| `IT-08-05` | **REQ-08** | Verify database rejects attendance records containing invalid date formats. | Blocked / not executed | **BLOCKED / NOT EXECUTED** | No dedicated automated test submitting invalid date format to session form exists. |
| `ST-08-06` | **REQ-08** | Verify bulk saving of attendance statuses for an entire class. | Blocked / not executed | **BLOCKED / NOT EXECUTED** | Dedicated 50-student UI form submission test unexecuted (500-row report benchmark tested instead). |
| `UT-08-07` | **REQ-08** | Verify boundary limits of the Attendance ID data type before database insertion. | Blocked / not executed | **BLOCKED / NOT EXECUTED** | Dedicated parameter boundary test on attendance record ID unexecuted. |
| `ST-08-08` | **REQ-08** | Verify system behavior if the database connection drops during an attendance save operation. | Partial | **PARTIAL** | Injected database rollback tested (test_mark_attendance_rolls_back_on_database_failure); live physical database disconnection during commit not executed. |
| `IT-09-01` | **REQ-09** | Verify system prevents duplicate attendance records for the same student, class, and date (REQ-09, BR-06). | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_duplicate_attendance_is_rejected`). |
| `ST-09-02` | **REQ-09** | Verify UI handles duplicate entry attempts gracefully. | Partial | **PARTIAL** | Template inspected with edit links; full browser edit workflow partial. |
| `UT-09-03` | **REQ-09** | Verify authorized faculty can modify an existing 'Present' record to 'Absent' (REQ-09). | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_update_attendance_creates_audit_record`). |
| `UT-09-04` | **REQ-09** | Verify authorized faculty can modify an existing 'Absent' record to 'Present' (REQ-09). | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_update_attendance_creates_audit_record & test_same_status_does_not_create_audit_record`). |
| `IT-09-05` | **REQ-09** | Verify database updates the existing record rather than inserting a new one upon modification. | Partial | **PARTIAL** | Duplicate prevention and modification/audit pass separately; full formal sequence partial. |
| `ST-09-06` | **REQ-09** | Verify faculty cannot modify attendance records for classes not assigned to them (BR-05). | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/test_security.py:test_faculty_cannot_modify_attendance_record_for_unassigned_section`). |
| `UT-09-07` | **REQ-09** | Verify students cannot modify any attendance records. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/test_authorization.py:test_br05_student_denied_modifying_attendance`). |
| `ST-09-08` | **REQ-09** | Verify data integrity after multiple rapid attendance modifications. | Blocked / not executed | **BLOCKED / NOT EXECUTED** | Dedicated high-concurrency race condition test for rapid successive updates unexecuted. |
| `ST-10-01` | **REQ-10** | Verify a student can successfully view their own attendance history. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_student_sees_only_own_history`). |
| `ST-10-02` | **REQ-10** | Verify access restriction for viewing another student's attendance (BR-04). | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/test_security.py:test_student_attendance_history_ignores_query_parameter_tampering`). |
| `UT-10-01` | **REQ-10** | Verify the display behavior when a student has no attendance records. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_empty_history_shows_message`). |
| `IT-10-01` | **REQ-10** | Verify attendance history updates in real-time when new data is submitted. | Partial | **PARTIAL** | History and attendance creation tested separately; single integrated test partial. |
| `UT-10-02` | **REQ-10** | Validate the date format in the attendance history UI. | Blocked / not executed | **BLOCKED / NOT EXECUTED** | Date formatting visually inspected in template; dedicated automated assertion unexecuted. |
| `ST-10-03` | **REQ-10** | Verify an unauthenticated user cannot access attendance records (BR-01). | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_unauthenticated_user_is_redirected_to_login`). |
| `IT-10-02` | **REQ-10** | Verify history reflects modifications made by authorized faculty (REQ-09). | Partial | **PARTIAL** | Modification and history tested separately; single integrated test partial. |
| `UT-10-03` | **REQ-10** | Verify UI behavior with a large volume of attendance records (pagination/scrolling). | Blocked / not executed | **BLOCKED / NOT EXECUTED** | Dedicated pagination boundary test with 100+ attendance records unexecuted. |
| `UT-11-01` | **REQ-11** | Verify attendance percentage calculation for perfect attendance. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_attendance_percentage_is_100_when_all_records_are_present`). |
| `UT-11-02` | **REQ-11** | Verify attendance percentage calculation for 0% attendance. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_attendance_percentage_is_zero_when_all_records_are_absent`). |
| `UT-11-03` | **REQ-11** | Verify attendance calculation for partial attendance with decimals. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_attendance_percentage_handles_mixed_records`). |
| `UT-11-04` | **REQ-11** | Verify calculation logic handles a divide-by-zero scenario. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_no_attendance_records_have_no_percentage`). |
| `IT-11-01` | **REQ-11** | Verify calculation updates automatically across modules when new attendance is marked. | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/test_dashboards.py:test_student_dashboard_independent_class_attendance_calculation`). |
| `IT-11-02` | **REQ-11** | Verify attendance calculation matches raw database records exactly (BR-07). | Pass (automated) | **PASS** | Automated test method fully verifies expected behavior (`attendance/tests.py:test_attendance_percentages_are_scoped_to_each_class_section`). |
| `ST-11-01` | **REQ-11** | Verify that the dashboard accurately reflects attendance summaries (REQ-15). | Partial | **PARTIAL** | Metrics context tested in dashboard tests; formal end-to-end system UI steps partial. |
| `ST-11-02` | **REQ-11** | Verify calculation handles invalid status gracefully. | Blocked / not executed | **BLOCKED / NOT EXECUTED** | Request boundaries reject invalid statuses; deterministic handling of pre-corrupted DB rows deferred per RTM-08. |

--- 

## 4. End-to-End Programmatic Functional Workflows (Zero Failures)

Three multi-step functional workflows were executed using `django.test.Client` in an isolated test environment:

### Workflow 1: Administrator Operations (`U-ADMIN-01`)
- **Steps Executed:**
  1. Authenticate with valid administrator credentials.
  2. Access Administrator Dashboard (`/dashboard/admin/`); verify 200 OK and metric counts.
  3. Create Course `CS404` and ClassSection `A / 2026-27` via POST; verify 302 redirect and database persistence.
  4. Create Student `USN999999` with email `student_wf@test.edu` via POST; verify persistence.
  5. Generate full system attendance report (`/attendance/reports/`); verify 200 OK and HTML table rendering.
- **Result:** **PASS (5/5 steps succeeded, 0 errors)**

### Workflow 2: Faculty Operations (`U-FAC-01`)
- **Steps Executed:**
  1. Authenticate with faculty credentials (`faculty_qa_01`).
  2. Access Faculty Dashboard (`/dashboard/faculty/`); verify 200 OK and assigned section display.
  3. Submit attendance session and marks for assigned section (`CS101 / A`) via POST; verify 302 redirect.
  4. Modify attendance status from PRESENT to ABSENT via POST; verify audit record creation.
  5. Generate section attendance report (`/attendance/reports/?class_section=...`); verify assigned data only.
- **Result:** **PASS (5/5 steps succeeded, 0 errors)**

### Workflow 3: Student Operations (`U-STU-01`)
- **Steps Executed:**
  1. Authenticate with student credentials (`student_qa_01`).
  2. Access Student Dashboard (`/dashboard/student/`); verify 200 OK and independent class percentage cards.
  3. Access Attendance History (`/attendance/history/`); verify 200 OK and own records display.
  4. Attempt query-parameter tampering (`/attendance/history/?student_id=...`); verify server ignores parameter and renders own records.
  5. Attempt access to Administrative views (`/dashboard/admin/`, `/attendance/manage/courses/`); verify 403 Forbidden.
- **Result:** **PASS (5/5 steps succeeded, 0 errors)**

--- 

## 5. Performance Latency Benchmarks (Local SQLite In-Memory)

> [!NOTE]
> **Execution Environment:** Windows 11 Pro workstation, Python 3.12.10, Django 5.2.18, SQLite in-memory (`config.test_settings`).
> Measured latencies represent in-process server-side request processing duration across 5 independent iterations per endpoint.

| Functional Area | Operation / Endpoint | Iterations | Average Latency | Maximum Latency | SRS 6.1 Target | Margin / Compliance |
|---|---|---:|---:|---:|---:|---|
| Authentication | Login Page GET (`/login/`) | 5 | 3.34 ms | 5.07 ms | <= 3,000 ms | **PASS** (99.89% faster) |
| Dashboards | Admin Dashboard GET (`/dashboard/admin/`) | 5 | 7.80 ms | 8.93 ms | <= 3,000 ms | **PASS** (99.74% faster) |
| Attendance Marking | Attendance Mark POST (`/attendance/mark/...`) | 5 | 14.01 ms | 17.48 ms | <= 2,000 ms | **PASS** (99.30% faster) |
| Reporting | Report Generation GET (500 rows) | 5 | 26.41 ms | 27.14 ms | <= 5,000 ms | **PASS** (99.47% faster) |

--- 

## 6. Latest Automated Test Suite Execution & Remote CI Audit

### 6.1 Latest Fresh Local Execution Record (Windows / SQLite In-Memory)

- **Exact Command:** `D:\SE Miniproject\student-attendance-management-system\.venv\Scripts\python.exe manage.py test --settings=config.test_settings`
- **Start Time:** 2026-11-07 05:14:05 UTC (10:44:05 Local)
- **End Time:** 2026-11-07 05:24:22 UTC (10:54:22 Local)
- **Duration:** 617.529 seconds (10 minutes 17.5 seconds)
- **Tests Discovered:** 183
- **Tests Passed:** 182
- **Tests Failed:** 0
- **Tests with Errors:** 1
- **Tests Skipped:** 0
- **Exit Code:** **1**

#### Detailed Concurrency Error Traceback
```text
ERROR: test_concurrent_duplicate_attendance_creates_only_one_record
(attendance.tests.AttendanceConcurrencyTests.test_concurrent_duplicate_attendance_creates_only_one_record)
----------------------------------------------------------------------
sqlite3.OperationalError: database table is locked
django.db.utils.OperationalError: database table is locked
----------------------------------------------------------------------
Ran 183 tests in 616.583s
FAILED (errors=1)
```

> [!CAUTION]
> **Technical Explanation of SQLite Concurrency Error:**
> In SQLite in-memory on Windows, concurrent writes from multiple threads (`concurrent.futures.ThreadPoolExecutor`) contend for SQLite's coarse-grained single-writer database lock. Under high thread contention, an insert query encountered `database table is locked`.
> While 182 of 183 tests passed cleanly, local testing on SQLite is **not 100% passing** without tuning SQLite timeout pragmas or running against PostgreSQL.

### 6.2 Remote PostgreSQL CI Execution Status

- **CI Platform:** GitHub Actions
- **Workflow Run ID:** `41309345461`
- **Workflow Name:** `CI / Test`
- **Target Commit SHA:** `d9618ef1ba99ba0a448a39140e69d25aaddda1dc`
- **Database Container:** `postgres:16`
- **Reported Status:** Success (183 passed in 3m 33s)
> [!WARNING]
> **CI Verification Limitation:** While GitHub Actions reported a green build (exit code 0), the exact individual test logs have not been downloaded and independently inspected in this workspace. The CI result is documented as reported by GitHub Actions, but cannot be certified until raw step logs are verified.

--- 

## 7. Browser & Responsive Usability Audit

### Workstation Browser Inventory
- **Google Chrome v156.0.8078.81:** Installed (`C:\Program Files\Google\Chrome\Application\chrome.exe`).
- **Microsoft Edge v156.0.4314.58:** Installed (`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`).
- **Mozilla Firefox:** **Not installed.** Untested.
- **Apple Safari:** **Not installed.** Untested.
- **Headless Browser Frameworks:** Neither Selenium nor Playwright is installed in `.venv`. All tests were programmatic HTTP/template assertions.

### Responsive Design & Viewport Review
- **Viewport Meta Tag:** All application templates extend `attendance/templates/base.html`, which defines `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.
- **CSS Layout:** `attendance/static/attendance/css/styles.css` uses flexbox, CSS variables, and relative units.
- **Documented Usability Limitation:** Static code inspection confirms that there are **0 dedicated CSS `@media` media queries** in `styles.css`. Viewports scale fluidly via flexbox wrapping, but dedicated device breakpoints are not defined. **No interactive mobile device or browser resizing testing was performed.**

--- 

## 8. Authoritative List of Blocked / Not Executed Scenarios (Exactly 10 Unique IDs)

The following 10 formal Test Plan v1.1 test cases were unexecuted due to host environment limitations or deferred institutional policy:

| # | Case ID | Req ID | Title / Scenario | Exact Blocker & Technical Rationale | Action Required to Execute |
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

## 9. Authoritative List of Partial Scenarios (Exactly 13 Unique IDs)

The following 13 formal Test Plan v1.1 test cases received partial automated verification, with specific formal steps requiring external infrastructure:

| # | Case ID | Req ID | Title / Scenario | Automated Evidence Present | Missing Infrastructure / Formal Step |
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
