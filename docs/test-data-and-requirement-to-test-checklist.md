# SAMS Test Data Inventory and Requirement-to-Test Checklist

- **Repository:** `SE-Student-Attendance-Management-System/student-attendance-management-system`
- **Issue:** [#7 — Prepare Test Data and Requirement-to-Test Checklist](https://github.com/SE-Student-Attendance-Management-System/student-attendance-management-system/issues/7)
- **Prepared:** 27 October 2026 (Updated: 12 November 2026 for Part 3 QA Documentation Corrections)
- **Baseline reviewed:** `main` at `d9618ef1ba99ba0a448a39140e69d25aaddda1dc`
- **Requirements baseline:** SRS v1.0
- **Test baseline:** `Student_Attendance_Management_System_Test_Plan_v1.1.docx` (115 Formal Cases)
- **Status:** Completed Part 3 QA execution results, updated test cases, and full RTM. Cross-reference deliverables:
  - [`docs/part-3-test-cases-and-traceability-matrix.md`](part-3-test-cases-and-traceability-matrix.md)
  - [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md)
  - [`docs/part-3-defect-report.md`](part-3-defect-report.md)
  - [`docs/part-3-final-qa-summary.md`](part-3-final-qa-summary.md)

## 1. Purpose and status rules

This document inventories the synthetic data needed to test SAMS and maps SRS requirements REQ-01–REQ-15 to the case IDs listed in Test Plan v1.1. It also records implementation/test-coverage observations and ambiguities to discuss with the Project Manager / QA Lead.

Use the following distinctions throughout:

- **Planned case:** listed in Test Plan v1.1; this defines the formal acceptance scenario baseline (115 cases).
- **Automated coverage observed:** a relevant test method exists in the reviewed `main` source (183 tests across 9 modules on `d9618ef`).
- **Not implemented / not observed / blocked:** unexecuted due to host environment limitations (10 blocked cases).
- **Execution result:** recorded with evidence in the Part 3 QA execution report.

Use **synthetic data only**. Do not use real student details, production accounts, or real passwords in test fixtures or committed documents. Any passwords in local fixtures should be test-only values and should be created through Django's user-creation helpers so password hashing is applied.

## 2. Test-data inventory

### 2.1 User accounts and role/access coverage

Create these accounts in a disposable test database or via test fixtures. The exact usernames are examples; the role and relationships are the important parts.

| Test key | Example username | Role | Linked profile / assignment | Purpose |
|---|---|---|---|---|
| U-ADMIN-01 | `admin_qa_01` | Administrator | No student/faculty profile required | Authorized student and course/class management; system-wide reports where implemented |
| U-FAC-01 | `faculty_qa_01` | Faculty | Linked to faculty profile `FAC101`; assigned `CS101 / A / 2026-27` | Allowed assigned-class workflows |
| U-FAC-02 | `faculty_qa_02` | Faculty | Linked to `FAC102`; assigned `CS202 / B / 2026-27` only | Verify data isolation between faculty members and assigned-class restrictions |
| U-FAC-03 | `faculty_qa_03` | Faculty | Faculty profile exists but has no class section | Empty assigned-class state and attempts to access unassigned classes |
| U-STU-01 | `student_qa_01` | Student | Linked to student record `USN000001` | Student's own records and attendance history |
| U-STU-02 | `student_qa_02` | Student | Linked to `USN000002` | Cross-student access denial; user must not retrieve U-STU-01's data |
| U-STU-03 | `student_qa_03` | Student | Linked to `USN000004` | Student with no attendance records; zero-record behavior |

For each account test, preserve the distinctions among unauthenticated requests, an authenticated user with the wrong role (expected HTTP 403 for protected views under the current repository convention), and a role-authorized request. Student-to-student isolation should be tested by changing a URL identifier or request parameter, not only by hiding navigation links.

### 2.2 Student profile test data

| Student key | USN | Name | Email | Phone | Course | Semester | Notes |
|---|---|---|---|---|---|---:|---|
| S-01 | `1MS21CS001` | Alice Student | `alice@example.com` | `9876543210` | Computer Science | 5 | Normal valid student |
| S-02 | `1MS21CS002` | Bob Student | `bob@example.com` | `9876543211` | Computer Science | 5 | Same class section as S-01 |
| S-03 | `1MS21CS003` | Carol Student | `carol@example.com` | `9876543212` | Information Science | 5 | Different course/section |
| S-04 | `1MS21CS004` | Dave Student | `dave@example.com` | `9876543213` | Computer Science | 5 | Enrolled in CS101/A, zero attendance records |
| S-BOUND-01 | `A12345678901234` | Exactly 15 Alphanumeric USN | `bound15@example.com` | `1234567890` | Computer Science | 1 | Maximum valid USN length (15 chars) |
| S-BOUND-02 | `USN_MAX_NAME_100` | Aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaz | `maxname@example.com` | `1234567890` | Computer Science | 8 | Maximum name length (100 chars) |

### 2.3 Field boundaries and negative validation datasets

| Field | Boundary / rule | Test values | Handling / expected outcome |
|---|---|---|---|
| Student ID / USN | Required, unique, alphanumeric, maximum 15 characters | Valid short value; valid value exactly 15 characters; 16-character value; duplicate of an existing USN; blank; punctuation/non-alphanumeric value | The UI-facing identifier is USN; do not confuse it with the database's internal primary key. |
| Student Name | Required, maximum 100 characters | Normal name; exactly 100 characters; 101 characters; blank/whitespace-only value | Check persistence and display of the 100-character boundary without UI breakage. |
| Email | Required, maximum 100 characters | Valid email; malformed email; duplicate email; valid email at the 100-character boundary if constructible; value above 100 characters | Keep format and maximum-length tests separate. Confirm whether duplicate email is a required business rule or an existing model constraint. |
| Phone Number | Optional, maximum 15; numeric/string per SRS | Omitted/blank; valid 10-digit example; 15-character boundary permitted by agreed format; over 15 characters; alphabetic/mixed value according to the clarified format rule | SRS calls the field optional and describes its type as Numeric/String. Confirm exact accepted format before treating one format as required. |
| Course/Program | Required, maximum 50 characters, string | Normal program; 50-character boundary; 51 characters; blank | Verify against the SRS, not only the model field definition. |
| Student Semester | Required, numeric, length 2 | Valid low and high agreed values; blank; non-numeric value; 0; 100 | SRS specifies two numeric characters but does not clearly state the accepted academic-semester range in the field table. Current model validators use 1–99; confirm the product rule before treating range tests as final. |
| Faculty ID | Required, alphanumeric, maximum 15 | Valid ID; 15-character boundary; 16 characters; duplicate; missing related faculty | Also verify assignment to an existing, active faculty profile. |
| Faculty name / email / department | Required; lengths 100 / 100 / 100 | Normal values; maximum-length values; over-limit values; malformed email | Email format should be checked independently of length. |
| Course ID | Required, unique, alphanumeric, maximum 20 | Normal value; exactly 20 alphanumeric characters; 21 alphanumeric characters; duplicate; blank; value containing punctuation/underscore | Use a purely alphanumeric over-limit string to test length alone. The Test Plan's `THIS_IS_A_VERY_LONG_ID_123` contains underscores, so it mixes the character-set and length conditions. |
| Course Name | Required, string, maximum 100 | Normal value; 100-character boundary; 101 characters; blank | Verify persistence after create/update. |
| Class/Section | Required, string, maximum 20 | Normal value; boundary; over-limit; blank; duplicate for the same course and academic term | In the implementation, uniqueness is represented by course + section + academic term. |
| Course Semester | Required, numeric, length 2 | Valid low/high values; blank; non-numeric; out-of-range values after PM confirms range | Course semester and class academic term are different concepts in the current model. |
| Academic term | Current model uses a required string with maximum 20 characters | `2026-27`; blank; boundary; duplicate combination | This field exists in the implementation's ClassSection model; confirm the accepted format as a team convention. |
| Attendance status | Institutional policy strictly restricts statuses to Present/Absent | `PRESENT`; `ABSENT`; unsupported statuses (e.g. `EXCUSED`, `LATE`) rejected at request boundaries | Confirmed: SAMS data model and services strictly restrict attendance status choices to PRESENT and ABSENT. |
| Attendance session | One class section, date and session number identify a session in the model | Valid date/session; duplicate section+date+session number; invalid date at the input boundary | Keep dates deterministic and use the same timezone/database settings as the test environment. |

### 2.4 Course, class-section, faculty-assignment and enrollment data

| Test key | Course | Section / term | Assigned faculty | Enrollments | Purpose |
|---|---|---|---|---|---|
| C-01 | `CS101` — Database Systems, semester 3 | `A / 2026-27` | `FAC101` | S-01, S-02, S-04 | Student management and attendance cases in one assigned section |
| C-02 | `CS202` — Data Analytics, semester 3 | `B / 2026-27` | `FAC102` | S-01, S-03 | Another course, another faculty member, and multi-course filtering |
| C-03 | `CS303` — Computer Networks, semester 4 | `C / 2026-27` | `FAC101` | At least one valid student | A second class for the same faculty member and section-specific update cases |

### 2.5 Attendance Policy Business Rules Representation

> [!IMPORTANT]
> **Institutional Policy Representation:**
> 1. **75.0% Threshold Independently Per ClassSection:** Attendance percentages are calculated strictly independently for each enrolled class section. Below 75.0% triggers `Low Attendance` status; at or above 75.0% achieves `Good Standing`; zero recorded sessions displays `N/A`.
> 2. **Zero Cross-Course Aggregate Percentage:** No aggregate or overall attendance percentage across disparate courses is calculated or displayed on the student dashboard, resolving DEF-02.
> 3. **Supported Statuses:** Supported attendance statuses are strictly restricted to `PRESENT` and `ABSENT`. Disallowed values (such as `EXCUSED` or `LATE`) are rejected at request validation boundaries.

### 2.6 Report and performance datasets

- **Small deterministic dataset:** the records in sections 2.2–2.5 for correctness, empty states and filtering.
- **Date-filter dataset:** records before, inside and after the selected date range.
- **No-match dataset/query:** a syntactically valid but non-existent student identifier; a valid future date range with no attendance records.
- **Performance dataset:** at least 100 attendance rows for normal data-processing checks and a 500-row report dataset for the Test Plan's report-generation target (measured: 26.41 ms avg / 0.0128s).
- **Class-size dataset:** 50 students in one class section to exercise list rendering and attendance input at the size called out by Test Plan v1.1.

## 3. Requirement-to-test checklist (RTM audit)

The following planned case IDs and counts are transcribed from Test Plan v1.1 Section 13. Counts sum to the document's stated total of 115 test cases (49 unit, 30 integration, 36 system cases).

Final Part 3 execution status across all 115 cases: **92 PASS, 13 PARTIAL, 10 BLOCKED / NOT EXECUTED, 0 FAIL**.

| SRS requirement | Feature | Test Plan v1.1 case IDs | Planned count | Final Part 3 QA Execution Status & Evidence |
|---|---|---|---:|---|
| **REQ-01** | Authenticate Registered Users | `UT-01-01`, `UT-01-02`, `UT-01-03`, `UT-01-04`, `IT-01-01`, `IT-01-02`, `ST-01-01`, `ST-01-02` | 8 | PASS: 6, PARTIAL: 2, BLOCKED: 0. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-02** | Provide Role-Based Access Control | `UT-02-01`, `UT-02-02`, `UT-02-03`, `IT-02-01`, `IT-02-02`, `ST-02-01`, `ST-02-02`, `ST-02-03` | 8 | **PASS (8/8)**. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-03** | Add and Update Student Records | `UT-03-02`, `UT-03-03`, `UT-03-04`, `UT-03-05`, `IT-03-01`, `IT-03-02` | 6 | **PASS (6/6)**. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-04** | Search and View Student Records | `UT-04-01`, `UT-04-02`, `UT-04-03`, `UT-04-04`, `IT-04-01`, `IT-04-02`, `ST-04-01`, `ST-04-02` | 8 | **PASS (8/8)**. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-05** | Create and Update Courses and Classes | `UT-05-02`, `UT-05-03`, `UT-05-04`, `IT-05-01`, `IT-05-02`, `ST-05-01`, `ST-05-02` | 7 | **PASS (7/7)**. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-06** | Assign Faculty and Display Assigned Classes | `UT-06-01`, `UT-06-02`, `UT-06-03`, `UT-06-04`, `IT-06-01`, `IT-06-02`, `ST-06-01`, `ST-06-02` | 8 | **PASS (8/8)**. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-07** | Mark Student Attendance in Assigned Classes | `UT-07-01`, `UT-07-02`, `IT-07-03`, `UT-07-04`, `IT-07-05`, `ST-07-06`, `ST-07-07`, `UT-07-08` | 8 | PASS: 3, PARTIAL: 3, BLOCKED: 2. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-08** | Record Present/Absent Attendance Status | `UT-08-01`, `UT-08-02`, `IT-08-03`, `IT-08-04`, `IT-08-05`, `ST-08-06`, `UT-08-07`, `ST-08-08` | 8 | PASS: 1, PARTIAL: 3, BLOCKED: 4. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-09** | Prevent Duplicates and Allow Authorized Modification | `IT-09-01`, `ST-09-02`, `UT-09-03`, `UT-09-04`, `IT-09-05`, `ST-09-06`, `UT-09-07`, `ST-09-08` | 8 | PASS: 5, PARTIAL: 2, BLOCKED: 1. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-10** | View Attendance History and Records | `ST-10-01`, `ST-10-02`, `UT-10-01`, `IT-10-01`, `UT-10-02`, `ST-10-03`, `IT-10-02`, `UT-10-03` | 8 | PASS: 4, PARTIAL: 2, BLOCKED: 2. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-11** | Calculate and Display Attendance Percentage (Independent Per-Class) | `UT-11-01`, `UT-11-02`, `UT-11-03`, `UT-11-04`, `IT-11-01`, `IT-11-02`, `ST-11-01`, `ST-11-02` | 8 | PASS: 6, PARTIAL: 1, BLOCKED: 1. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-12** | Generate Attendance Reports | `ST-12-02`, `ST-12-03`, `UT-12-01`, `IT-12-01`, `ST-12-04`, `ST-12-05` | 6 | **PASS (6/6)**. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-13** | Filter Attendance Reports | `UT-13-01`, `UT-13-02`, `UT-13-03`, `IT-13-04`, `IT-13-05`, `ST-13-06`, `ST-13-07`, `ST-13-08` | 8 | **PASS (8/8)**. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-14** | Display Role-Specific Dashboards | `UT-14-01`, `UT-14-02`, `UT-14-03`, `IT-14-04`, `IT-14-05`, `ST-14-06`, `ST-14-07`, `ST-14-08` | 8 | **PASS (8/8)**. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |
| **REQ-15** | Display Role-Based Attendance Summaries | `UT-15-01`, `UT-15-02`, `UT-15-03`, `IT-15-04`, `IT-15-05`, `ST-15-06`, `ST-15-07`, `ST-15-08` | 8 | **PASS (8/8)**. Verified on `main` at `d9618ef`. See [`docs/part-3-test-execution-report.md`](part-3-test-execution-report.md) |

## 4. Ambiguity and clarification register

| Query ID | Finding / observation | Suggested resolution |
|---|---|---|
| RTM-01 | Test Plan Section 13 lists UT-03-02 through UT-03-05 but omits UT-03-01. | Treated as intentional; 115 cases total confirmed. |
| RTM-02 | Test Plan Section 13 lists UT-05-02 through UT-05-04 but omits UT-05-01. | Treated as intentional; 115 cases total confirmed. |
| RTM-03 | Test Plan Section 13 lists 8 cases for REQ-08 but states count 7 in row. | Typo in Test Plan text; exactly 8 cases verified. |
| RTM-04 | Course ID alphanumeric character set boundary. | Pure alphanumeric over-limit string used. |
| RTM-05 | ST-04-01 student name search scope. | Implemented and verified case-insensitively in `test_student_search.py`. |
| RTM-06 | Access matrix for student search/detail. | Verified: Student role receives 403 Forbidden. |
| RTM-07 | Student semester numeric range. | Implementation validates 1–99. |
| RTM-08 | ST-11-02 corrupted database status handling. | Deferred per institutional policy; marked as Blocked. |
| RTM-09 | Business rule BR-08 mapped to report authorization. | Verified in `test_reports.py` and `test_security.py`. |
| RTM-10 | Issue dependency references. | Stabilized across sprints. |
| RTM-11 | Standardizing on USN. | Verified: USN used across UI and forms. |
| RTM-12 | 500-row report performance. | Benchmarked: 26.41 ms avg (well below 5.0 s target). |
| RTM-13 | REQ-11 & REQ-15 attendance scope. | Verified: strictly independent per class with 75.0% threshold (DEF-02 resolved). |

## 5. Execution recording checklist

All 115 Test Plan cases have been executed or classified with evidence on `main` (`d9618ef1ba99ba0a448a39140e69d25aaddda1dc`):
- [x] Case ID and requirement/business rule recorded.
- [x] Build identifier recorded: `main` @ `d9618ef1ba99ba0a448a39140e69d25aaddda1dc`.
- [x] Environment recorded: SQLite in-memory (local, 182 pass, 1 error) and PostgreSQL 16 (CI Run ID `41309345461`).
- [x] Expected result and actual observed result recorded.
- [x] Final evidence-based status recorded: 92 PASS, 13 PARTIAL, 10 BLOCKED / NOT EXECUTED, 0 FAIL.
- [x] Historical defects DEF-01 and DEF-02 verified resolved.

## 6. Reviewed repository files and scope boundaries

The Part 3 QA audit of `main` at `d9618ef1ba99ba0a448a39140e69d25aaddda1dc` reviewed:
- `attendance/models.py`
- `attendance/forms.py`
- `attendance/views.py`
- `attendance/urls.py`
- `attendance/services.py`
- `attendance/templates/`
- `attendance/static/attendance/css/styles.css`
- `attendance/test*.py` (all 9 test modules, 183 automated tests)
- `docs/part-3-*.md` deliverables
