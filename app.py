import csv
import io
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db_connection, init_db, score_to_grade

app = Flask(__name__)
app.secret_key = 'rcp-imrd-sms-secret-key-2026-super-secure'

# Ensure DB initialized on startup
init_db()

# ----------------- AUTHENTICATION HELPERS & DECORATORS ----------------- #

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in with administrator credentials.', 'warning')
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('student_portal'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    return {
        'current_user': {
            'is_authenticated': 'user_id' in session,
            'id': session.get('user_id'),
            'username': session.get('username', 'Guest'),
            'role': session.get('role', 'guest'),
            'student_id': session.get('student_id')
        }
    }

def calculate_student_gpa(enrollments):
    """Calculates cumulative GPA on a 4.0 scale weighted by course credits."""
    total_credit_points = 0.0
    total_credits = 0
    for e in enrollments:
        if e['score'] is not None and e['credits']:
            _, gpa_val = score_to_grade(e['score'])
            credits = e['credits']
            total_credit_points += (gpa_val * credits)
            total_credits += credits
    return round(total_credit_points / total_credits, 2) if total_credits > 0 else 0.0

def get_departments():
    return [
        "MCA",
        "Computer Science",
        "Data Science",
        "Electrical Eng",
        "Mechanical Eng",
        "Business Admin",
        "Mathematics",
        "Humanities"
    ]

# ----------------- AUTHENTICATION ROUTES ----------------- #

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('dashboard'))
        return redirect(url_for('student_portal'))

    if request.method == 'POST':
        login_id = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role_pref = request.form.get('role', 'admin').strip()
        next_url = request.form.get('next', '')

        if not (login_id and password):
            flash('Please enter your username/ID and password.', 'danger')
            return render_template('login.html', next_url=next_url)

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Allow logging in with username, roll_no, or email
        user = cursor.execute('''
            SELECT * FROM users 
            WHERE (username = ? OR email = ?)
        ''', (login_id, login_id)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['student_id'] = user['student_id']

            flash(f"Welcome back, {user['username']}! Logged in as {user['role'].capitalize()}.", 'success')

            if next_url and next_url.startswith('/'):
                return redirect(next_url)

            if user['role'] == 'admin':
                return redirect(url_for('dashboard'))
            return redirect(url_for('student_portal'))
        else:
            flash('Invalid username/email or password. Please try again.', 'danger')
            return render_template('login.html', next_url=next_url)

    next_url = request.args.get('next', '')
    return render_template('login.html', next_url=next_url)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('login'))

# ----------------- STUDENT SELF-SERVICE PORTAL ----------------- #

@app.route('/student/portal')
@login_required
def  student_portal():
    student_id = session.get('student_id')

    # If an admin accesses this page, show the first available student as a preview
    conn = get_db_connection()
    cursor = conn.cursor()

    if not student_id:
        first_s = cursor.execute("SELECT id FROM students ORDER BY id ASC LIMIT 1").fetchone()
        if first_s:
            student_id = first_s['id']
        else:
            conn.close()
            flash('No student profile is currently linked.', 'warning')
            return redirect(url_for('dashboard'))

    student = cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        conn.close()
        flash('Student record could not be found.', 'warning')
        return redirect(url_for('dashboard'))

    enrollments = cursor.execute('''
        SELECT e.*, c.code, c.name as course_name, c.credits, c.instructor, c.description
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = ?
        ORDER BY e.semester DESC, c.code ASC
    ''', (student_id,)).fetchall()

    attendance_records = cursor.execute('''
        SELECT a.*, c.code as course_code, c.name as course_name
        FROM attendance a
        JOIN courses c ON a.course_id = c.id
        WHERE a.student_id = ?
        ORDER BY a.date DESC
        LIMIT 25
    ''', (student_id,)).fetchall()

    total_att = len(attendance_records)
    present_att = sum(1 for a in attendance_records if a['status'] in ('Present', 'Late'))
    attendance_pct = round((present_att / total_att) * 100, 1) if total_att > 0 else 0.0

    gpa = calculate_student_gpa(enrollments)
    earned_credits = sum(e['credits'] for e in enrollments if e['grade'] not in ('-', 'F'))

    conn.close()

    return render_template(
        'student_portal.html',
        student=student,
        enrollments=enrollments,
        attendance_records=attendance_records,
        attendance_pct=attendance_pct,
        gpa=gpa,
        earned_credits=earned_credits
    )

# ----------------- ADMIN DASHBOARD ----------------- #

@app.route('/')
@login_required
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('student_portal'))

    conn = get_db_connection()
    cursor = conn.cursor()

    total_students = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_courses = cursor.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    total_enrollments = cursor.execute("SELECT COUNT(*) FROM enrollments WHERE status = 'Enrolled'").fetchone()[0]
    
    # Campus Average Score
    avg_score_row = cursor.execute("SELECT AVG(score) FROM enrollments WHERE score IS NOT NULL").fetchone()
    avg_score = round(avg_score_row[0], 1) if avg_score_row and avg_score_row[0] else 0.0
    _, avg_grade = score_to_grade(avg_score)

    # Department distribution
    dept_distribution = cursor.execute('''
        SELECT department, COUNT(*) as count 
        FROM students 
        GROUP BY department 
        ORDER BY count DESC
    ''').fetchall()

    # Recent enrollments
    recent_enrollments = cursor.execute('''
        SELECT e.id, s.first_name, s.last_name, s.roll_no, c.code, c.name as course_name, 
               e.semester, e.score, e.grade, e.status, e.enrolled_at
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        JOIN courses c ON e.course_id = c.id
        ORDER BY e.id DESC
        LIMIT 6
    ''').fetchall()

    # Top performing students
    top_students = cursor.execute('''
        SELECT s.id, s.roll_no, s.first_name, s.last_name, s.department, AVG(e.score) as avg_score, COUNT(e.id) as course_count
        FROM students s
        JOIN enrollments e ON s.id = e.student_id
        WHERE e.score IS NOT NULL
        GROUP BY s.id
        HAVING course_count >= 1
        ORDER BY avg_score DESC
        LIMIT 5
    ''').fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total_students=total_students,
        total_courses=total_courses,
        total_enrollments=total_enrollments,
        avg_score=avg_score,
        avg_grade=avg_grade,
        dept_distribution=dept_distribution,
        recent_enrollments=recent_enrollments,
        top_students=top_students
    )

# ----------------- STUDENTS MANAGEMENT (ADMIN) ----------------- #

@app.route('/students')
@admin_required
def students():
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', '').strip()
    year = request.args.get('year', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT s.*, 
               COUNT(e.id) as total_courses,
               ROUND(AVG(e.score), 1) as avg_score
        FROM students s
        LEFT JOIN enrollments e ON s.id = e.student_id
        WHERE 1=1
    '''
    params = []

    if search:
        query += ''' AND (s.first_name LIKE ? OR s.last_name LIKE ? OR s.roll_no LIKE ? OR s.email LIKE ?) '''
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if dept:
        query += ''' AND s.department = ? '''
        params.append(dept)

    if year:
        query += ''' AND s.year = ? '''
        params.append(int(year))

    query += ''' GROUP BY s.id ORDER BY s.id DESC '''
    students_list = cursor.execute(query, params).fetchall()
    departments = get_departments()
    conn.close()

    return render_template(
        'students.html',
        students=students_list,
        departments=departments,
        selected_dept=dept,
        selected_year=year,
        search_query=search
    )

@app.route('/students/create', methods=['POST'])
@admin_required
def create_student():
    roll_no = request.form.get('roll_no', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    gender = request.form.get('gender', 'Other')
    dob = request.form.get('dob', '')
    department = request.form.get('department', '').strip()
    year = int(request.form.get('year', 1))
    address = request.form.get('address', '').strip()

    if not (roll_no and first_name and last_name and email and department):
        flash('Please fill in all required fields (Roll No, Names, Email, Department).', 'danger')
        return redirect(url_for('students'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO students (roll_no, first_name, last_name, email, phone, gender, dob, department, year, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (roll_no, first_name, last_name, email, phone, gender, dob, department, year, address))
        new_student_id = cursor.lastrowid

        # Also create student login account automatically
        default_pw = generate_password_hash("student123")
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, role, student_id)
            VALUES (?, ?, ?, 'student', ?)
        ''', (roll_no, email, default_pw, new_student_id))

        conn.commit()
        flash(f'Student "{first_name} {last_name}" ({roll_no}) added successfully! Login account created (Password: student123).', 'success')
    except Exception as e:
        flash(f'Error adding student: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('students'))

@app.route('/students/<int:student_id>')
@login_required
def student_detail(student_id):
    # If student is logged in, they can only view their own profile
    if session.get('role') == 'student' and session.get('student_id') != student_id:
        flash('You only have permission to view your own profile.', 'warning')
        return redirect(url_for('student_portal'))

    conn = get_db_connection()
    cursor = conn.cursor()

    student = cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        flash('Student record not found.', 'warning')
        conn.close()
        return redirect(url_for('students'))

    enrollments = cursor.execute('''
        SELECT e.*, c.code, c.name as course_name, c.credits, c.instructor
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = ?
        ORDER BY e.semester DESC, c.code ASC
    ''', (student_id,)).fetchall()

    attendance_records = cursor.execute('''
        SELECT a.*, c.code as course_code, c.name as course_name
        FROM attendance a
        JOIN courses c ON a.course_id = c.id
        WHERE a.student_id = ?
        ORDER BY a.date DESC
        LIMIT 20
    ''', (student_id,)).fetchall()

    total_att = len(attendance_records)
    present_att = sum(1 for a in attendance_records if a['status'] in ('Present', 'Late'))
    attendance_pct = round((present_att / total_att) * 100, 1) if total_att > 0 else 0.0

    gpa = calculate_student_gpa(enrollments)
    earned_credits = sum(e['credits'] for e in enrollments if e['grade'] not in ('-', 'F'))

    enrolled_course_ids = [e['course_id'] for e in enrollments]
    all_courses = cursor.execute("SELECT * FROM courses ORDER BY code ASC").fetchall()
    available_courses = [c for c in all_courses if c['id'] not in enrolled_course_ids]

    conn.close()

    return render_template(
        'student_detail.html',
        student=student,
        enrollments=enrollments,
        attendance_records=attendance_records,
        attendance_pct=attendance_pct,
        gpa=gpa,
        earned_credits=earned_credits,
        available_courses=available_courses
    )

@app.route('/students/<int:student_id>/update', methods=['POST'])
@admin_required
def update_student(student_id):
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    gender = request.form.get('gender', 'Other')
    dob = request.form.get('dob', '')
    department = request.form.get('department', '').strip()
    year = int(request.form.get('year', 1))
    address = request.form.get('address', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE students 
            SET first_name = ?, last_name = ?, email = ?, phone = ?, gender = ?, 
                dob = ?, department = ?, year = ?, address = ?
            WHERE id = ?
        ''', (first_name, last_name, email, phone, gender, dob, department, year, address, student_id))
        conn.commit()
        flash('Student profile updated successfully!', 'success')
    except Exception as e:
        flash(f'Failed to update student: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('student_detail', student_id=student_id))

@app.route('/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    cursor.execute("DELETE FROM users WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()
    flash('Student record deleted successfully.', 'info')
    return redirect(url_for('students'))

# ----------------- COURSES MANAGEMENT ----------------- #

@app.route('/courses')
@login_required
def courses():
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT c.*, COUNT(e.id) as enrolled_count
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        WHERE 1=1
    '''
    params = []

    if search:
        query += ''' AND (c.code LIKE ? OR c.name LIKE ? OR c.instructor LIKE ?) '''
        term = f"%{search}%"
        params.extend([term, term, term])

    if dept:
        query += ''' AND c.department = ? '''
        params.append(dept)

    query += ''' GROUP BY c.id ORDER BY c.code ASC '''
    courses_list = cursor.execute(query, params).fetchall()
    departments = get_departments()
    conn.close()

    return render_template(
        'courses.html',
        courses=courses_list,
        departments=departments,
        selected_dept=dept,
        search_query=search
    )

@app.route('/courses/create', methods=['POST'])
@admin_required
def create_course():
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    credits = int(request.form.get('credits', 3))
    semester = request.form.get('semester', 'MCA Sem 1').strip()
    instructor = request.form.get('instructor', '').strip()
    description = request.form.get('description', '').strip()

    if not (code and name and department):
        flash('Course Code, Name, and Department are required.', 'danger')
        return redirect(url_for('courses'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO courses (code, name, department, credits, semester, instructor, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (code, name, department, credits, semester, instructor, description))
        conn.commit()
        flash(f'Course {code} ({name}) created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating course: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('courses'))

@app.route('/courses/<int:course_id>/update', methods=['POST'])
@admin_required
def update_course(course_id):
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    credits = int(request.form.get('credits', 3))
    semester = request.form.get('semester', 'MCA Sem 1').strip()
    instructor = request.form.get('instructor', '').strip()
    description = request.form.get('description', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE courses
            SET code = ?, name = ?, department = ?, credits = ?, semester = ?, instructor = ?, description = ?
            WHERE id = ?
        ''', (code, name, department, credits, semester, instructor, description, course_id))
        conn.commit()
        flash(f'Course {code} updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating course: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('courses'))

@app.route('/courses/<int:course_id>/delete', methods=['POST'])
@admin_required
def delete_course(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()
    flash('Course and associated enrollment data deleted.', 'info')
    return redirect(url_for('courses'))

# ----------------- ENROLLMENTS & GRADING (ADMIN) ----------------- #

@app.route('/enrollments')
@admin_required
def enrollments():
    course_filter = request.args.get('course_id', '')
    student_filter = request.args.get('student_id', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT e.*, s.roll_no, s.first_name, s.last_name, s.department as student_dept,
               c.code as course_code, c.name as course_name, c.credits
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        JOIN courses c ON e.course_id = c.id
        WHERE 1=1
    '''
    params = []

    if course_filter:
        query += " AND e.course_id = ?"
        params.append(course_filter)

    if student_filter:
        query += " AND e.student_id = ?"
        params.append(student_filter)

    query += " ORDER BY e.id DESC"
    all_enrollments = cursor.execute(query, params).fetchall()

    all_students = cursor.execute("SELECT id, roll_no, first_name, last_name FROM students ORDER BY roll_no ASC").fetchall()
    all_courses = cursor.execute("SELECT id, code, name FROM courses ORDER BY code ASC").fetchall()
    conn.close()

    return render_template(
        'enrollments.html',
        enrollments=all_enrollments,
        students=all_students,
        courses=all_courses,
        selected_course=course_filter,
        selected_student=student_filter
    )

@app.route('/enrollments/create', methods=['POST'])
@admin_required
def create_enrollment():
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    semester = request.form.get('semester', 'Fall 2026')
    redirect_target = request.form.get('redirect_target', 'enrollments')

    if not (student_id and course_id):
        flash('Both Student and Course must be selected.', 'danger')
        return redirect(url_for('enrollments'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO enrollments (student_id, course_id, semester, status)
            VALUES (?, ?, ?, 'Enrolled')
        ''', (student_id, course_id, semester))
        conn.commit()
        flash('Enrollment completed successfully!', 'success')
    except Exception as e:
        flash(f'Enrollment failed (Student may already be enrolled in this semester): {str(e)}', 'danger')
    finally:
        conn.close()

    if redirect_target == 'student_detail':
        return redirect(url_for('student_detail', student_id=student_id))
    return redirect(url_for('enrollments'))

@app.route('/enrollments/<int:enrollment_id>/update_score', methods=['POST'])
@admin_required
def update_score(enrollment_id):
    score_raw = request.form.get('score', '').strip()
    status = request.form.get('status', 'Enrolled')
    redirect_target = request.form.get('redirect_target', 'enrollments')
    student_id = request.form.get('student_id')

    score = None
    grade = '-'
    if score_raw != '':
        try:
            score = float(score_raw)
            if score < 0 or score > 100:
                flash('Score must be between 0 and 100.', 'danger')
                return redirect(url_for('enrollments'))
            grade, _ = score_to_grade(score)
            if score >= 50 and status == 'Enrolled':
                status = 'Completed'
        except ValueError:
            flash('Invalid score value.', 'danger')
            return redirect(url_for('enrollments'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE enrollments
        SET score = ?, grade = ?, status = ?
        WHERE id = ?
    ''', (score, grade, status, enrollment_id))
    conn.commit()
    conn.close()

    flash(f'Score updated to {score} (Grade: {grade}, Status: {status})', 'success')
    if redirect_target == 'student_detail' and student_id:
        return redirect(url_for('student_detail', student_id=student_id))
    return redirect(url_for('enrollments'))

@app.route('/enrollments/<int:enrollment_id>/delete', methods=['POST'])
@admin_required
def delete_enrollment(enrollment_id):
    redirect_target = request.form.get('redirect_target', 'enrollments')
    student_id = request.form.get('student_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
    conn.commit()
    conn.close()
    flash('Enrollment record removed.', 'info')

    if redirect_target == 'student_detail' and student_id:
        return redirect(url_for('student_detail', student_id=student_id))
    return redirect(url_for('enrollments'))

# ----------------- ATTENDANCE (ADMIN) ----------------- #

@app.route('/attendance')
@admin_required
def attendance():
    course_id = request.args.get('course_id', '')
    date_val = request.args.get('date', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    all_courses = cursor.execute("SELECT id, code, name FROM courses ORDER BY code ASC").fetchall()
    
    if not course_id and all_courses:
        course_id = str(all_courses[0]['id'])

    enrolled_students = []
    attendance_map = {}

    if course_id:
        enrolled_students = cursor.execute('''
            SELECT s.id, s.roll_no, s.first_name, s.last_name, s.department
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            WHERE e.course_id = ?
            ORDER BY s.roll_no ASC
        ''', (course_id,)).fetchall()

        if date_val:
            records = cursor.execute('''
                SELECT student_id, status FROM attendance
                WHERE course_id = ? AND date = ?
            ''', (course_id, date_val)).fetchall()
            attendance_map = {r['student_id']: r['status'] for r in records}

    conn.close()

    return render_template(
        'attendance.html',
        courses=all_courses,
        selected_course_id=int(course_id) if course_id else None,
        selected_date=date_val,
        students=enrolled_students,
        attendance_map=attendance_map
    )

@app.route('/attendance/save', methods=['POST'])
@admin_required
def save_attendance():
    course_id = request.form.get('course_id')
    date_val = request.form.get('date')

    if not (course_id and date_val):
        flash('Course and Date are required.', 'danger')
        return redirect(url_for('attendance'))

    conn = get_db_connection()
    cursor = conn.cursor()

    for key, value in request.form.items():
        if key.startswith('att_'):
            student_id = int(key.replace('att_', ''))
            cursor.execute('''
                INSERT INTO attendance (student_id, course_id, date, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(student_id, course_id, date) DO UPDATE SET status = excluded.status
            ''', (student_id, course_id, date_val, value))

    conn.commit()
    conn.close()
    flash(f'Attendance recorded for {date_val} successfully!', 'success')
    return redirect(url_for('attendance', course_id=course_id, date=date_val))

# ----------------- CSV EXPORT (ADMIN) ----------------- #

@app.route('/export/students.csv')
@admin_required
def export_students_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    students_data = cursor.execute('''
        SELECT s.roll_no, s.first_name, s.last_name, s.email, s.phone, s.gender, s.dob, s.department, s.year,
               ROUND(AVG(e.score), 2) as avg_score, COUNT(e.id) as enrolled_courses
        FROM students s
        LEFT JOIN enrollments e ON s.id = e.student_id
        GROUP BY s.id
        ORDER BY s.roll_no ASC
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll No", "First Name", "Last Name", "Email", "Phone", "Gender", "Date of Birth", "Department", "Year", "Avg Score", "Total Courses"])

    for s in students_data:
        writer.writerow([
            s['roll_no'], s['first_name'], s['last_name'], s['email'], s['phone'] or '',
            s['gender'] or '', s['dob'] or '', s['department'], s['year'],
            s['avg_score'] if s['avg_score'] is not None else 'N/A',
            s['enrolled_courses']
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=students_export.csv"}
    )

# ----------------- JSON REST API ----------------- #

@app.route('/api/stats', methods=['GET'])
def api_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    total_s = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_c = cursor.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    total_e = cursor.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]
    avg_s = cursor.execute("SELECT AVG(score) FROM enrollments WHERE score IS NOT NULL").fetchone()[0]
    conn.close()

    return jsonify({
        "total_students": total_s,
        "total_courses": total_c,
        "total_enrollments": total_e,
        "average_score": round(avg_s, 2) if avg_s else 0.0
    })

@app.route('/api/students', methods=['GET'])
def api_get_students():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students ORDER BY roll_no ASC").fetchall()
    conn.close()
    return jsonify([dict(s) for s in students])

@app.route('/api/students/<int:id>', methods=['GET'])
def api_get_student_by_id(id):
    conn = get_db_connection()
    s = conn.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()
    conn.close()
    if not s:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(dict(s))

if __name__ == '__main__':
    print("==================================================")
    print(" 🚀 R. C. Patel IMRD Student Management System")
    print(" 🌐 Local URL: http://127.0.0.1:5000")
    print(" 🔐 Admin Login: username='admin', password='admin123'")
    print(" 👨‍🎓 Student Login: username='MCA-2026-001', password='student123'")
    print("==================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
