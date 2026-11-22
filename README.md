# R. C. Patel IMRD — Student Management System (SMS)

A full-stack academic management system built with **Python**, **Flask**, **SQLite**, and modern web technologies for **R. C. Patel Educational Trust's Institute of Management, Research & Development, Shirpur**.

Designed for managing student profiles, course catalogs, grade evaluation (GPA calculation), daily class attendance, and role-based portal access (**Admin** and **Student**).

---

## 🔐 Authentication & Role-Based Access

The system features dual role-based logins with secure password hashing (`werkzeug.security`):

| Role | Username / ID | Password | Access Privileges |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full control: Admin Dashboard, Student CRUD, Course CRUD, Grading & Evaluation, Daily Attendance Register, CSV Export |
| **Student** | `student` *or* `MCA-2026-001` | `student123` | Student Academic Portal: Personal grades, GPA, earned credits, course catalog, attendance rate |

*Note: All students in the database have user accounts created automatically with their Roll Number (e.g. `MCA-2026-001`, `MCA-2026-002`) and password `student123`.*

---

## ✨ Features

- 🔐 **Dual Role Login System (`/login`)**
  - Administrator Login: Access to administrative operations and settings.
  - Student / User Login: Personalized view of academic records, grades, and attendance.
  - Quick 1-Click Demo Credentials autofill.
  - Automatic session protection and route security (`@login_required`, `@admin_required`).

- 📊 **Academic Dashboard (`/`)**
  - Real-time KPIs: Total students, active course catalog, active registrations, campus average score.
  - Department breakdown chart.
  - Leaderboard of top academic performers and recent registrations feed.

- 👨‍🎓 **Student Self-Service Portal (`/student/portal`)**
  - Real-time cumulative GPA calculation (4.0 scale).
  - List of enrolled subjects with marks, letter grades, and credits.
  - Attendance history and percentage.

- 👥 **Student Directory & Profiles (`/students`)**
  - Complete CRUD: Add, view, edit, and delete student records.
  - Live search by Name, Roll Number, or Email.
  - Filter by Department and Academic Year.
  - Auto-generated student login accounts.

- 📚 **Course Catalog Management (`/courses`)**
  - Course code, course name, department, credits, semester, and instructor details.
  - Loaded with pure **MCA** subjects (Theory & Practical Labs for MCA Sem 1 & Sem 3).

- 📝 **Enrollment & Automated Grade Evaluation (`/enrollments`)**
  - Register students into semester courses.
  - Grade evaluator that converts numerical scores (0–100) into letter grades (`A+` to `F`) and calculates weighted GPA.

- 📅 **Daily Attendance Tracker (`/attendance`)**
  - Course- and date-based attendance register (`Present`, `Absent`, `Late`, `Excused`).
  - "Quick Mark All Present" shortcut.

- 📥 **Data Export & REST API**
  - One-click `.CSV` spreadsheet download.
  - JSON REST API endpoints (`/api/stats`, `/api/students`, `/api/students/<id>`).

---

## 🛠️ Project Structure

```text
student_management_system/
├── app.py                     # Flask application routes, authentication & APIs
├── database.py                # SQLite schema with users, students, courses, enrollments & attendance
├── seed_data.py               # Database seeder with MCA courses and user credentials
├── test_app.py                # Automated test suite (8 tests covering auth & role guards)
├── requirements.txt           # Project dependencies
├── README.md                  # Documentation and setup guide
├── static/
│   ├── css/
│   │   └── style.css          # Custom responsive CSS design (cards, tables, badges, modals)
│   └── js/
│       └── app.js             # Modal management, grade previewer, attendance shortcuts
└── templates/
    ├── base.html              # Layout skeleton (dynamic sidebar navigation & top bar)
    ├── login.html             # High-end login page with Admin & Student tabs
    ├── student_portal.html    # Dedicated student view (grades, GPA, attendance)
    ├── dashboard.html         # Admin dashboard & analytics
    ├── students.html          # Student directory & registration modal
    ├── student_detail.html    # Detailed student profile & grade sheet
    ├── courses.html           # Course catalog & course creation modal
    ├── enrollments.html       # Course registration & grading interface
    └── attendance.html        # Daily attendance register
```

---

## 🚀 Quick Start Guide

### 1. Setup & Installation
Open PowerShell in the project directory:

```powershell
cd "C:\Users\IMRD\.gemini\antigravity\scratch\student_management_system"
pip install -r requirements.txt
```

### 2. Seed Database & Accounts
Populate the database with MCA courses, sample students, and login accounts:
```powershell
python seed_data.py
```

### 3. Run the Application
Start the Flask development server:
```powershell
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```
*(You will be directed to `/login` to sign in as Admin or Student)*

### 4. Running the Automated Tests
```powershell
python test_app.py
```
=======
# Student-Management-System

