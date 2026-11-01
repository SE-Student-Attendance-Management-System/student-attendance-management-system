# Issue #40 — Attendance Integration Test Report

- **Repository:** `SE-Student-Attendance-Management-System/student-attendance-management-system`
- **Issue:** [#40 — Test attendance integration and resolve defects](https://github.com/SE-Student-Attendance-Management-System/student-attendance-management-system/issues/40)
- **Branch reviewed:** `test/40-attendance-integration`
- **Scope:** REQ-07 through REQ-11 (40 cases from Test Plan v1.1)
- **Environment:** Windows, Python virtual environment, Django 5.2.18, PostgreSQL
- **Evidence basis:** Test execution output and source/template inspection supplied during Issue #40 work
- **Document status:** Execution/coverage report; does not replace or modify the approved Test Plan v1.1.

## 1. Execution summary

| Execution | Recorded result |
|---|---|
| `python manage.py test attendance.tests attendance.test_authorization attendance.test_faculty_assignment -v 2` | 59 tests passed |
| `python manage.py test attendance -v 2` | 183 tests passed |
| `python manage.py check` | System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `git diff --check` | Clean; no output |
| Database | PostgreSQL; transaction support confirmed |
| Browser/manual end-to-end testing | No execution evidence supplied; not claimed as passed |

The 59-test focused run is a subset of the full attendance suite. Do not add the two counts as separate unique tests.

## 2. Status definitions

- **Pass (automated):** A relevant automated test was executed successfully and its assertions exercise the stated scenario.
- **Partial:** Related automated assertions exist, but they do not establish every step or condition in the formal Test Plan case.
- **Blocked / not executed:** No sufficient execution evidence for the formal scenario was supplied.
- **Fail:** An executed test contradicted its expected result. No such failure was reported in the executions recorded here.

Source-code or template inspection alone is not a test execution and cannot justify Pass.

## 3. Requirement-to-test execution matrix

Expected-result summaries are concise descriptions of the formal Test Plan v1.1 scenarios. Consult the approved plan for complete steps and test data.

### REQ-07 — Mark attendance in assigned classes

| Test case | Expected-result summary | Actual result / evidence | Status |
|---|---|---|---|
| UT-07-01 | Faculty can view assigned class sections. | `test_faculty_sees_own_assigned_classes` executed; verifies assigned-class visibility, not the complete marking operation. | Partial |
| UT-07-02 | Unassigned faculty cannot mark attendance. | `test_br03_unassigned_faculty_denied_marking_attendance` executed; authorization denial asserted. | Pass (automated) |
| IT-07-03 | Attendance can be created for an enrolled student in an assigned session. | `test_mark_attendance_for_enrolled_student` executed; asserts PRESENT status, marking actor, and record count. | Pass (automated service scenario) |
| UT-07-04 | Empty/invalid enrollment scenario is handled as specified. | `test_reject_attendance_for_unenrolled_student` executed; rejects an unenrolled student without creating a record. Does not establish the formal empty-list UI case. | Partial |
| IT-07-05 | Integrated marking workflow persists the expected attendance. | Service-level creation is covered; no separate evidence for every formal integration step was supplied. | Partial |
| ST-07-06 | Faculty completes the attendance workflow through the system UI. | No browser/manual end-to-end execution evidence supplied. Template inspection is not execution. | Blocked / not executed |
| ST-07-07 | Faculty cannot mark attendance for an unassigned section/session. | `test_faculty_cannot_mark_attendance_for_unassigned_section_session` executed; GET/POST denied and existing record remains unchanged. | Pass (automated) |
| UT-07-08 | Invalid class/section identifier format is rejected as specified. | No directly matching executed test evidence supplied. | Blocked / not executed |

### REQ-08 — Record Present/Absent status

| Test case | Expected-result summary | Actual result / evidence | Status |
|---|---|---|---|
| UT-08-01 | Status selection control offers supported choices. | Mark template inspected: status dropdown is populated from `status_choices`; no dedicated rendered-form execution evidence supplied. | Partial |
| UT-08-02 | Missing status is rejected. | Template has a required select and invalid-status injection tests exist; no direct executed missing-status form test identified. | Partial |
| IT-08-03 | PRESENT status is stored for an enrolled student. | `test_mark_attendance_for_enrolled_student` executed; asserts stored PRESENT status. | Pass (automated service scenario) |
| IT-08-04 | ABSENT status is stored through the specified workflow. | Modification test changes PRESENT to ABSENT and asserts persistence; the exact formal marking-page scenario is not independently evidenced. | Partial |
| IT-08-05 | Invalid session date is rejected. | No executed matching invalid-date test evidence supplied. | Blocked / not executed |
| ST-08-06 | Bulk attendance for 50 students meets the specified performance target. | No 50-student UI run or timing measurement supplied. | Blocked / not executed |
| UT-08-07 | Oversized Attendance ID is handled safely. | No matching executed boundary test evidence supplied. | Blocked / not executed |
| ST-08-08 | Database failure does not leave partial attendance changes and gives a safe message. | `test_mark_attendance_rolls_back_on_database_failure`, `test_update_attendance_rolls_back_if_audit_creation_fails`, and `test_update_view_handles_database_failure_safely` executed. These inject database errors; they do not establish a live database-disconnection test. | Partial |

### REQ-09 — Prevent duplicates and allow authorized modification

| Test case | Expected-result summary | Actual result / evidence | Status |
|---|---|---|---|
| IT-09-01 | Duplicate attendance for the same student/session is prevented. | `test_duplicate_attendance_is_rejected` and `test_concurrent_duplicate_attendance_creates_only_one_record` executed; one record remains under duplicate/concurrent attempts. | Pass (automated) |
| ST-09-02 | UI presents the existing record in the expected modify/edit workflow. | Mark template displays existing records and an Edit link; update template displays current status. No browser workflow execution supplied. | Partial |
| UT-09-03 | Authorized status modification updates the record. | `test_update_attendance_creates_audit_record` executed; PRESENT changes to ABSENT and persists. | Pass (automated service scenario) |
| UT-09-04 | Modification audit captures old/new status and actor. | Same test asserts old status, new status, changed-by actor, and audit count. | Pass (automated) |
| IT-09-05 | Integrated duplicate prevention and modification workflow behaves correctly. | Duplicate prevention and service-level modification/audit tests passed separately; full formal end-to-end sequence not evidenced. | Partial |
| ST-09-06 | Unassigned faculty cannot modify another faculty member's attendance. | `test_br05_unassigned_faculty_denied_modifying_attendance` and `test_faculty_cannot_modify_attendance_record_for_unassigned_section` executed; denial, unchanged status, and no audit asserted. | Pass (automated) |
| UT-09-07 | Student cannot modify attendance. | `test_br05_student_denied_modifying_attendance` executed; denial, unchanged status, and no audit asserted. | Pass (automated) |
| ST-09-08 | Rapid consecutive modifications are handled correctly. | No dedicated rapid-consecutive-modification execution evidence supplied. | Blocked / not executed |

### REQ-10 — View attendance history

| Test case | Expected-result summary | Actual result / evidence | Status |
|---|---|---|---|
| ST-10-01 | Student sees their own attendance history, not another student's records. | `test_student_sees_only_own_history` executed; response context records are scoped to the authenticated student. | Pass (automated) |
| ST-10-02 | Student cannot manipulate request parameters to view another student's history. | `test_student_attendance_history_ignores_query_parameter_tampering` executed; context and rendered response are checked for isolation. | Pass (automated) |
| UT-10-01 | Empty history displays the expected message. | `test_empty_history_shows_message` executed; asserts “No attendance records found.” | Pass (automated) |
| IT-10-01 | Newly recorded attendance appears in student history. | History and attendance creation are tested, but no single executed test was identified that creates a record and verifies it through the history workflow. | Partial |
| UT-10-02 | History dates use the required display format. | No direct executed date-format assertion supplied. | Blocked / not executed |
| ST-10-03 | Unauthenticated user cannot access attendance history. | `test_unauthenticated_user_is_redirected_to_login` executed; redirect asserted. | Pass (automated) |
| IT-10-02 | History reflects a later attendance modification. | Modification and history are tested separately; no direct executed test proving the modified value appears on the history page was identified. | Partial |
| UT-10-03 | History pagination handles 100+ records as specified. | No 100+ record pagination execution evidence supplied. | Blocked / not executed |

### REQ-11 — Calculate/display attendance percentage

| Test case | Expected-result summary | Actual result / evidence | Status |
|---|---|---|---|
| UT-11-01 | All-PRESENT records produce 100%. | `test_attendance_percentage_is_100_when_all_records_are_present` executed; summary and rendered percentage asserted. | Pass (automated) |
| UT-11-02 | All-ABSENT records produce 0%. | `test_attendance_percentage_is_zero_when_all_records_are_absent` executed; summary and rendered percentage asserted. | Pass (automated) |
| UT-11-03 | Mixed PRESENT/ABSENT records produce the correct percentage. | `test_attendance_percentage_handles_mixed_records` executed; 1 of 2 produces 50%. | Pass (automated) |
| UT-11-04 | No records do not cause division by zero and show no percentage. | `test_no_attendance_records_have_no_percentage` executed; percentage is `None` and empty-state text asserted. | Pass (automated) |
| IT-11-01 | Student dashboard calculates attendance independently for each class. | `test_student_dashboard_independent_class_attendance_calculation` executed; checks independent per-section calculations after adding an absent session. | Pass (automated integration-style test) |
| IT-11-02 | Percentage calculations remain scoped to the relevant class section. | `test_attendance_percentages_are_scoped_to_each_class_section` executed; section A and B percentages are isolated. | Pass (automated) |
| ST-11-01 | Student dashboard displays attendance summary as specified. | `test_student_dashboard_metrics_context` executed, but this alone does not establish every formal system/UI step. | Partial |
| ST-11-02 | Unsupported/corrupted status is handled according to the approved business rule. | Unsupported status injection is tested at request boundaries; no corrupted persisted-status scenario or approved deterministic expected outcome is evidenced. | Blocked / not executed |

## 4. Coverage totals

| Status | Count |
|---|---:|
| Pass (automated) | 19 |
| Partial | 11 |
| Blocked / not executed | 10 |
| Fail | 0 |
| **Total** | **40** |

“Pass (automated)” means the mapped automated scenario was executed and its assertions passed; it does not mean a manual system test was completed. Partial and blocked cases must not be reported as passed.

## 5. Additional regression and integrity evidence

The full attendance suite also includes tests beyond the 40 formal cases:

- Assigned faculty can mark attendance; unassigned faculty and students are denied.
- Admin and assigned faculty modification authorization.
- Unsupported status injection is rejected by marking and update endpoints.
- Attendance update rolls back if audit creation fails.
- Database error messages do not expose sensitive database details.
- Concurrent duplicate attendance attempts result in one record.
- Student history rejects POST and is protected against query-parameter tampering.
- Dashboard section calculations are isolated.
- Faculty dashboard visibility is limited to assigned sections.

The full suite reported 183 tests passed. The focused subset reported 59 tests passed. No failing test output was reported.

## 6. UI/template inspection (not execution evidence)

`attendance/templates/attendance/attendance_mark.html` was inspected. It displays existing records with Edit links, lists unrecorded students with a required status dropdown populated from `status_choices`, includes a CSRF token, and shows empty-state messages.

`attendance/templates/attendance/attendance_update.html` was inspected. It displays student/course/section/date/current status, preselects the current status in a required dropdown, includes a CSRF token, and provides Save Changes and Back links.

These inspections support Partial assessments for UI cases. They do not prove that a user completed the workflow in a browser.

## 7. Defects and retesting

- No failing test was reported in the focused or full attendance test runs recorded above.
- Issue #39 transaction consistency/error handling was integrated before this test run. Rollback and safe-error tests passed as part of the attendance suite.
- No new defect is asserted because no reproducible failing execution was supplied.
- Passing automated regression tests do not establish that every manual/system scenario is defect-free.
- If a formal case fails during later execution, create or update a defect issue with reproduction steps, expected/actual result, severity/priority, environment, and related requirement/test-case ID. Record the retest separately after the fix.

## 8. Outstanding work / blocked cases

1. Execute the UI workflow in a browser with synthetic test accounts: faculty login, assigned class/session, mark Present/Absent, submit, revisit, edit, and verify persisted status/audit.
2. Execute and capture the 50-student bulk case with actual elapsed time and dataset details.
3. Execute invalid date, missing status, identifier boundary, and pagination boundary scenarios using the exact Test Plan inputs.
4. Confirm the expected result for ST-11-02 with the Product Owner/QA Lead before testing corrupted persisted data.
5. Execute the end-to-end student history update scenario after attendance creation and modification.
6. Attach evidence (test output, screenshots, or logs) to the relevant test case records. Keep blocked cases blocked until executed.

## 9. Reproduction commands and recorded results

```powershell
python manage.py test attendance.tests attendance.test_authorization attendance.test_faculty_assignment -v 2
# Ran 59 tests — OK

python manage.py test attendance -v 2
# Ran 183 tests — OK

python manage.py check
# System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run
# No changes detected

git diff --check
# No output; clean
```

The test database was recreated by Django for the test run and destroyed after completion. The configured database was PostgreSQL, with transaction support confirmed.

## 10. Scope and limitations

- This report covers the 40 Test Plan v1.1 cases mapped to REQ-07 through REQ-11.
- It does not certify all 115 cases in Test Plan v1.1.
- It does not alter the approved SRS or Test Plan.
- It does not claim browser/manual execution, 50-student performance, 100+ pagination, or corrupted persisted-status behavior without evidence.
- Test results apply to the branch/code state that was tested. Record the exact commit SHA when committing this report so the evidence can be tied to a reproducible revision.
