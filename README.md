Student Attendance Management System

Overview

A web-based system for managing and tracking student attendance. It
provides centralized attendance records with role-based access for
Administrators, Faculty, and Students.

Features

User authentication and role-based authorization

Student management

Course and class management

Faculty assignment

Attendance marking and modification

Attendance percentage calculation

Attendance history and viewing

Attendance reports with filters

Role-specific dashboards

User Roles

Administrator - Manage students, faculty, courses, and classes.

Faculty - View assigned classes - Mark and manage attendance -
Generate attendance reports

Student - View personal attendance records, history, and percentage

Requirements

The system is designed as a web application and requires: - A supported
web browser - Application/server environment - Database server - Network
connection

The SRS specifies Python (Django/Flask) or Java (Spring Boot) as
possible backend technologies. The final technology stack is determined
during implementation.

Main Requirements

Prevent duplicate attendance records.

Apply role-based access control.

Protect attendance data from unauthorized access.

Calculate attendance percentage from stored records.

Allow authorized users to generate and filter reports.

Project Structure

The final repository structure depends on the selected implementation
technology.

student-attendance-management-system/
├── README.md
├── source/
├── tests/
├── database/
└── documentation/

Testing

Testing should cover: - Authentication and authorization -
Student/course/class management - Attendance marking and modification -
Duplicate prevention - Attendance calculation - Reports and dashboards -
Security and validation

Project Information

Version: 1.0

Team: Team 1

Institution: PES University, Bangalore

Department: Computer Science and Engineering

Status

The project requirements are defined in the Software Requirements
Specification (SRS), Version 1.0. Implementation and final technology
choices are completed during the design and implementation phase.