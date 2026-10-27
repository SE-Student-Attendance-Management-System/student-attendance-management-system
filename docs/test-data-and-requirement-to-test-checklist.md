# SAMS Test Data Inventory and Requirement-to-Test Checklist

- **Repository:** `SE-Student-Attendance-Management-System/student-attendance-management-system`
- **Issue:** [#7 — Prepare Test Data and Requirement-to-Test Checklist](https://github.com/SE-Student-Attendance-Management-System/student-attendance-management-system/issues/7)
- **Prepared:** 27 October 2026
- **Baseline reviewed:** `main` at `0fdf874eeb59d07d04c0c9dc39be5a86390c8683`
- **Requirements baseline:** SRS v1.0
- **Test baseline:** `Student_Attendance_Management_System_Test_Plan_v1.1.docx`
- **Status:** Test-data plan and source/code audit only. This document does not claim any test was executed.

## 1. Purpose and status rules

This document inventories the synthetic data needed to test SAMS and maps SRS requirements REQ-01–REQ-15 to the case IDs listed in Test Plan v1.1. It also records implementation/test-coverage observations and ambiguities to discuss with the Project Manager / QA Lead.

Use the following distinctions throughout:

- **Planned case:** listed in Test Plan v1.1; this does not mean an automated test exists.
- **Automated coverage observed:** a relevant test method exists in the reviewed `main` source. The code has not necessarily been executed in the current session.
- **Not implemented / not observed:** the reviewed `main` source does not yet provide the relevant feature or a directly relevant test.
- **Execution result:** leave the Test Plan's `Actual Result` and `Test Result` columns blank until the case is run and evidence is recorded. Do not infer Pass from the presence of test code.

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

### 2.2 Student profiles

Use unique values for every unique field, including USN and email. Values below are illustrative test data, not existing database records.

| Test key | USN | Name | Example email | Program | Semester | Phone | Attendance purpose |
|---|---|---|---|---|---:|---|---|
| S-01 | `USN000001` | Alice Example | `alice.qa01@example.test` | CSE | 3 | `9876500001` | Five recorded sessions in CS101/A; four Present and one Absent (80%) |
| S-02 | `USN000002` | Bob Example | `bob.qa02@example.test` | ECE | 3 | blank | Four recorded sessions in CS101/A; all Absent (0%); optional phone omitted |
| S-03 | `USN000003` | Casey Example | `casey.qa03@example.test` | CSE | 3 | `9876500003` | Four recorded sessions in CS202/B; all Present (100%) |
| S-04 | `USN000004` | Drew Example | `drew.qa04@example.test` | CSE | 3 | blank | Enrolled in CS101/A but has no AttendanceRecord rows for that class; zero-record percentage/history case |
| S-05 | `USN000005` | Jordan Example | `jordan.qa05@example.test` | ECE | 4 | blank | A student without a linked login account, for admin-managed profile cases if permitted by the approved data model |

Use S-01/S-02 to compare students in the same section, S-01/S-03 for course and faculty filtering, S-04 for empty history/no attendance data, and S-05 to verify that a student profile without a linked login is handled safely by administrative features.

### 2.3 Field-boundary and invalid-input data

Use separate test inputs so each validation test isolates one condition rather than combining several failures in the same value.

| Field | SRS Appendix B rule | Test values / conditions | Notes |
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
| Attendance status | SRS business rule expects Present/Absent | `PRESENT`; `ABSENT`; unsupported status such as `EXCUSED` through a controlled negative test | Do not seed invalid persisted statuses in routine fixtures. The expected handling of corrupted data needs a deterministic product decision. |
| Attendance session | One class section, date and session number identify a session in the model | Valid date/session; duplicate section+date+session number; invalid date at the input boundary | Keep dates deterministic and use the same timezone/database settings as the test environment. |

Boundary tests are data requirements, not claims that all these cases are currently covered or that the rules have been approved beyond the stated SRS and issue acceptance criteria.

### 2.4 Course, class-section, faculty-assignment and enrollment data

| Test key | Course | Section / term | Assigned faculty | Enrollments | Purpose |
|---|---|---|---|---|---|
| C-01 | `CS101` — Database Systems, semester 3 | `A / 2026-27` | `FAC101` | S-01, S-02, S-04 | Student management and attendance cases in one assigned section |
| C-02 | `CS202` — Data Analytics, semester 3 | `B / 2026-27` | `FAC102` | S-01, S-03 | Another course, another faculty member, and multi-course filtering |
| C-03 | `CS303` — Computer Networks, semester 4 | `C / 2026-27` | `FAC101` | At least one valid student | A second class for the same faculty member and section-specific update cases |

Required negative/edge data:

- Attempt to create a duplicate Course ID (for example, `CS101`).
- Attempt to duplicate `C-01`'s course + section + academic-term combination.
- Attempt to assign an inactive faculty profile.
- Attempt direct GET and POST management operations as Faculty, Student and unauthenticated user.
- Verify `faculty_qa_01` sees only their own assigned sections, `faculty_qa_02` sees only theirs, and `faculty_qa_03` sees an empty-state message.
- Use duplicate names for two students when testing the Test Plan's name-search case; do not assume name search is approved scope until the query below is resolved.

### 2.5 Attendance sessions and records

Use deterministic session dates so report date filtering produces repeatable results. The example values below are a suggested fixture set; the final execution dataset should remain consistent across unit and integration runs.

| Session group | Section | Dates | Student / status pattern | Expected calculation use |
|---|---|---|---|---|
| A-1 | CS101/A | 1, 8, 15, 22 and 27 October 2026 | S-01: Present, Present, Present, Present, Absent | 4/5 = 80% |
| A-2 | CS101/A | 1, 8, 15 and 22 October 2026 | S-02: Absent on each recorded session | 0/4 = 0% |
| B-1 | CS202/B | 2, 9, 16 and 23 October 2026 | S-03: Present on each recorded session | 4/4 = 100% |
| A-3 | CS101/A | Existing sessions, but no attendance rows for S-04 | S-04 has no AttendanceRecord rows | Empty history / zero recorded sessions; ensure no divide-by-zero |

For attendance-integrity tests, add these scenarios in a disposable database:

- Duplicate AttendanceRecord for the same student and session must be rejected.
- An un-enrolled student must not be recorded for a section.
- Assigned faculty can mark and modify; unassigned faculty and students cannot.
- Invalid status must be rejected.
- A status modification creates the expected audit record; an unchanged status should not create a spurious audit entry if that is the implemented contract.
- A transaction failure must not leave a partial attendance or audit update; coordinate with issue #39 for the agreed coverage and branch integration.

### 2.6 Report and performance datasets

- **Small deterministic dataset:** the records in sections 2.2–2.5 for correctness, empty states and filtering.
- **Date-filter dataset:** records before, inside and after the selected date range; for example, select 1–22 October 2026 and include an applicable record on 23 or 27 October to verify exclusion at the upper boundary.
- **No-match dataset/query:** a syntactically valid but non-existent student identifier; a valid future date range with no attendance records; and a combination of valid filters with no matching records.
- **Performance dataset:** at least 100 attendance rows for normal data-processing checks and a 500-row report dataset for the Test Plan's report-generation target of less than or equal to 5 seconds under documented normal conditions.
- **Class-size dataset:** 50 students in one class section to exercise list rendering and attendance input at the size called out by Test Plan v1.1.
- Generate large datasets deterministically and keep the generator/fixture separate from manual execution notes. Record data volume, environment, database, and elapsed time for a performance result; do not mark performance passed without an actual timing measurement.

## 3. Requirement-to-test checklist (RTM audit)

The following planned case IDs and counts are transcribed from Test Plan v1.1 Section 13. Counts sum to the document's stated total of 115 test cases (49 unit, 30 integration, 36 system cases). The test-plan columns `Actual Result` and `Test Result` must remain blank until each case is executed.

| SRS requirement | Feature | Test Plan v1.1 case IDs | Planned count | Current implementation / test audit (source inspection only) |
|---|---|---|---:|---|
| REQ-01 | Authenticate registered users | UT-01-01, UT-01-02, UT-01-03, UT-01-04, IT-01-01, IT-01-02, ST-01-01, ST-01-02 | 8 | Authentication cases exist in `attendance/tests.py`; execution is not recorded in this document. |
| REQ-02 | Role-based access | UT-02-01, UT-02-02, UT-02-03, IT-02-01, IT-02-02, ST-02-01, ST-02-02, ST-02-03 | 8 | Role/view and service-level authorization tests exist in `attendance/test_authorization.py`; dashboard and faculty-assignment checks also exist. Execution is not recorded here. |
| REQ-03 | Add/update student records | UT-03-02, UT-03-03, UT-03-04, UT-03-05, IT-03-01, IT-03-02 | 6 | Student create/update views, form and routes were not present in the reviewed `main` code. Dedicated automated student-management tests were not observed. Case ID UT-03-01 is absent; see clarification register. |
| REQ-04 | Search/view student records | UT-04-01, UT-04-02, UT-04-03, UT-04-04, IT-04-01, IT-04-02, ST-04-01, ST-04-02 | 8 | Student search/detail routes and views were not present in the reviewed `main` code. Dedicated automated student-search tests were not observed. The planned name-search scenario needs scope clarification. |
| REQ-05 | Create/update courses/classes | UT-05-02, UT-05-03, UT-05-04, IT-05-01, IT-05-02, ST-05-01, ST-05-02 | 7 | `attendance/test_course_views.py` contains tests for listing, creation, duplicate Course ID, duplicate section, invalid section, update/persistence, faculty reassignment, inactive faculty and non-admin access. Explicit Course ID boundary/character-set tests and each plan case's one-to-one mapping should be checked during #17. UT-05-01 is absent; see register. |
| REQ-06 | Assign faculty and display assigned classes | UT-06-01, UT-06-02, UT-06-03, UT-06-04, IT-06-01, IT-06-02, ST-06-01, ST-06-02 | 8 | `attendance/test_faculty_assignment.py` covers own assigned classes, isolation from another faculty member, and the no-assignment state. Course-view and authorization tests cover assignment/reassignment and access restrictions. Confirm all Test Plan cases have explicit traceability during #17. |
| REQ-07 | Mark attendance in assigned classes | UT-07-01, UT-07-02, IT-07-03, UT-07-04, IT-07-05, ST-07-06, ST-07-07, UT-07-08 | 8 | Attendance service and authorization tests exist. Issue #31 is still open/assigned to Rahul; verify prerequisite changes are integrated before relying on the full feature. |
| REQ-08 | Record Present/Absent status | UT-08-01, UT-08-02, IT-08-03, IT-08-04, IT-08-05, ST-08-06, UT-08-07, ST-08-08 | 8 | Attendance service tests cover valid and invalid status and persistence-level records; verify the exact Test Plan mapping and run tests. |
| REQ-09 | Prevent duplicates and allow authorized modification | IT-09-01, ST-09-02, UT-09-03, UT-09-04, IT-09-05, ST-09-06, UT-09-07, ST-09-08 | 8 | Attendance uniqueness, modification/audit and access tests exist in the reviewed code. Issue #39 transaction consistency is open/assigned to Rahul; coordinate and verify the integrated behavior. |
| REQ-10 | View attendance history | ST-10-01, ST-10-02, UT-10-01, IT-10-01, UT-10-02, ST-10-03, IT-10-02, UT-10-03 | 8 | Student attendance-history view/routes were not present in the reviewed `main` code. This is the objective of issue #32, subject to attendance prerequisites. |
| REQ-11 | Calculate/display attendance percentage | UT-11-01, UT-11-02, UT-11-03, UT-11-04, IT-11-01, IT-11-02, ST-11-01, ST-11-02 | 8 | A dedicated percentage calculation/display feature was not observed in the reviewed code. Issue #33 depends on available history and stored attendance. ST-11-02's acceptable outcome is ambiguous; see register. |
| REQ-12 | Generate attendance reports | ST-12-02, ST-12-03, UT-12-01, IT-12-01, ST-12-04, ST-12-05 | 6 | Report-generation views/routes were not present in the reviewed `main` code. ST-12-05 describes report filtering (REQ-13) despite being listed under REQ-12; see register. |
| REQ-13 | Filter attendance reports | UT-13-01, UT-13-02, UT-13-03, IT-13-04, IT-13-05, ST-13-06, ST-13-07, ST-13-08 | 8 | Report-filter views/routes were not present in the reviewed `main` code. Validate authorization on the server side in addition to filter correctness when implemented. |
| REQ-14 | Display role-specific dashboards | UT-14-01, UT-14-02, UT-14-03, IT-14-04, IT-14-05, ST-14-06, ST-14-07, ST-14-08 | 8 | `home` role context and tests for administrator/faculty/student dashboard access exist. Full role-specific feature completeness and the 3-second performance target still require execution/evidence. |
| REQ-15 | Display role-based attendance summaries | UT-15-01, UT-15-02, UT-15-03, IT-15-04, IT-15-05, ST-15-06, ST-15-07, ST-15-08 | 8 | The reviewed `home` view shows assigned classes/student enrollments, but a database-backed attendance-summary implementation was not observed. Related summary cases should remain blocked until that behavior exists. |

**Audit status:** This matrix is a documentation/source review. No test has been marked Pass or Fail here because no execution output was collected as part of this issue's preparation.

## 4. Gaps and inconsistent mappings to clarify with the PM / QA Lead

| Ref | Finding from source review | Recommended decision / action |
|---|---|---|
| RTM-01 | REQ-03 lists six cases, but the IDs jump from UT-03-02 to UT-03-05; UT-03-01 is not listed in the RTM or student case excerpt reviewed. | Confirm whether UT-03-01 was intentionally retired or omitted. Do not invent a replacement case ID without approval. |
| RTM-02 | REQ-05 lists seven cases, but UT-05-01 is not listed; its displayed cases start at UT-05-02. | Confirm whether the missing ID is intentional or the case was omitted. Preserve traceability and count after the decision. |
| RTM-03 | ST-12-05 is listed under REQ-12 and counted among its six cases, but its description explicitly tests filtering by Student ID and cites REQ-13. | Reclassify or cross-reference ST-12-05 under REQ-13 with PM approval, then reconcile counts so the documented total remains accurate. Do not silently edit the approved plan. |
| RTM-04 | UT-05-03 uses `THIS_IS_A_VERY_LONG_ID_123`, which contains underscores as well as excess length, while the SRS calls Course ID alphanumeric. | Use a 21-character alphanumeric-only value for the length test and a separate punctuation case for character-set validation. |
| RTM-05 | ST-04-01 tests student-name search and multiple matches; issue #15 describes search using a supported identifier and does not explicitly confirm name-search scope. | Confirm whether name-based search is in approved scope. If not, align the test case with the approved identifier requirements. |
| RTM-06 | The Test Plan describes Student as unable to search other students in IT-04-02, while other REQ-04 scenarios describe authorized users as Admin/Faculty. Issue #15 uses the broader phrase “authorized user.” | Approve an explicit access matrix for search/list/detail actions (Admin, Faculty, Student) before implementing #15. Preserve the SRS rule that students may access only their own attendance information; do not assume it automatically grants student access to arbitrary profiles. |
| RTM-07 | SRS Appendix B describes Student Semester as a two-digit numeric field but does not clearly state the allowed academic-semester range in the field table. Current model validators accept 1–99. | Confirm the intended valid academic-semester range. Test the boundaries only after the rule is agreed; record the currently implemented 1–99 validator as an implementation fact, not automatically as the approved business rule. |
| RTM-08 | ST-11-02 permits alternatives for corrupted/unsupported status (ignore the record or map it according to institutional logic), rather than defining one expected result. | Product Owner/PM should choose one deterministic behavior and update the expected result before the case is executed. |
| RTM-09 | The Test Plan's business-rule table maps BR-08 to ST-12-03, while ST-13-07 also denies Student access to report filters and issue #35 explicitly requires authorization to remain enforced during filtering. | Consider also cross-referencing ST-13-07 to BR-08 and verify authorization for filtered-report endpoints, subject to PM approval of the test-plan edit. |
| RTM-10 | Issue dependency references #22/#23/#24/#25 do not match their actual repository records; #22 is the technology/workflow PR, #23 the initial data-model PR, #24 the core data-model PR, and #25 CI. | Correct the dependency references in #32–#35 after PM confirmation. The likely feature order is #31 → #32 → #33 → #34 → #35, with the data model/course/faculty prerequisites and issue #39 transaction work verified first. |
| RTM-11 | Test Plan examples use both “Student ID” and “USN.” The current model uses `Student.usn` for the unique institution-facing identifier and an internal primary key for database relations. | Standardize test data and UI/API cases on USN when referring to the SRS Student ID / USN; use the internal primary key only where an implementation-level test specifically needs it. |
| RTM-12 | The Test Plan calls for 500-row report timing and a 50-student class; current report features are not yet present in the reviewed `main` code. | Keep performance cases blocked until reporting is implemented; measure in the documented supported environment and record actual elapsed time and dataset size. |

## 5. Execution recording checklist

For each Test Plan case selected for execution, record the following only after running it:

- [ ] Case ID and requirement/business rule.
- [ ] Build identifier: branch and commit SHA.
- [ ] Environment/database and test-data fixture version.
- [ ] Expected result copied from the approved Test Plan (or approved revision).
- [ ] Actual observed result and relevant output/evidence.
- [ ] Pass / Fail / Blocked outcome based on evidence.
- [ ] Defect issue link and reproduction steps for a failure.
- [ ] Retest result after a fix, where applicable.

A blocked test is not a failure or a pass; record the missing prerequisite and responsible owner. Never fill the source Test Plan's `Actual Result` or `Test Result` columns while preparing data or mapping coverage only.

## 6. Reviewed repository files and scope boundaries

The audit of `main` at `0fdf874eeb59d07d04c0c9dc39be5a86390c8683` inspected:

- `README.md`
- `attendance/models.py`
- `attendance/forms.py`
- `attendance/views.py`
- `attendance/urls.py`
- `attendance/services.py`
- `attendance/permissions.py`
- `attendance/tests.py`
- `attendance/test_authorization.py`
- `attendance/test_course_views.py`
- `attendance/test_faculty_assignment.py`
- `.github/workflows/ci.yml`
- `Student-Attendance-Management-System-SRS_final.docx`
- `Student_Attendance_Management_System_Test_Plan_v1.1.docx`

This issue's deliverable is documentation and a source-based coverage audit. It does not implement student features, change the approved SRS/Test Plan, modify test results, or certify any execution. Follow-up development/testing belongs to the relevant assigned issues after dependency and scope questions are resolved.
