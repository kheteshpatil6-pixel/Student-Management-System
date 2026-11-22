import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from database import get_db_connection, init_db, score_to_grade

# Student list (Focus on MCA batches and campus programs)
SAMPLE_STUDENTS = [
    # MCA 1 (Div A, B, C)
    ("MCA-2026-001", "Rohit", "Patil", "rohit.patil@rcpimrd.ac.in", "+91-98230-11001", "Male", "2003-03-12", "MCA", 1, "R. C. Patel Campus, Shirpur"),
    ("MCA-2026-002", "Pooja", "Chaudhari", "pooja.c@rcpimrd.ac.in", "+91-98230-11002", "Female", "2003-07-25", "MCA", 1, "Nimzari Naka, Shirpur"),
    ("MCA-2026-003", "Harshal", "Shinde", "harshal.s@rcpimrd.ac.in", "+91-98230-11003", "Male", "2002-11-14", "MCA", 1, "Karvand Naka, Shirpur"),
    ("MCA-2026-004", "Neha", "Bhamare", "neha.b@rcpimrd.ac.in", "+91-98230-11004", "Female", "2003-05-18", "MCA", 1, "Subhash Nagar, Shirpur"),
    ("MCA-2026-005", "Vikas", "Sonar", "vikas.s@rcpimrd.ac.in", "+91-98230-11005", "Male", "2003-01-20", "MCA", 1, "Main Road, Shirpur"),
    ("MCA-2026-006", "Anjali", "Desale", "anjali.d@rcpimrd.ac.in", "+91-98230-11006", "Female", "2003-09-08", "MCA", 1, "Vikram Nagar, Shirpur"),
    
    # MCA 2 (Sem 3)
    ("MCA-2025-010", "Chetan", "Sonawane", "chetan.s@rcpimrd.ac.in", "+91-98230-11010", "Male", "2001-08-09", "MCA", 2, "Near Bus Stand, Dhule"),
    ("MCA-2025-011", "Snehal", "Mahajan", "snehal.m@rcpimrd.ac.in", "+91-98230-11011", "Female", "2002-02-22", "MCA", 2, "Adarsh Nagar, Shirpur"),
    ("MCA-2025-012", "Pratik", "Badgujar", "pratik.b@rcpimrd.ac.in", "+91-98230-11012", "Male", "2001-12-03", "MCA", 2, "Shahada Road, Shirpur"),

    # Other Campus Students
    ("CS-2023-001", "Alex", "Rivers", "alex.rivers@campus.edu", "+1-555-0101", "Male", "2002-04-12", "Computer Science", 3, "42 Willow Creek Rd"),
    ("CS-2023-002", "Maya", "Patel", "maya.patel@campus.edu", "+1-555-0102", "Female", "2003-08-19", "Computer Science", 2, "108 Maple Avenue"),
    ("DS-2023-010", "Liam", "Johnson", "liam.j@campus.edu", "+1-555-0105", "Male", "2002-09-23", "Data Science", 3, "230 Cedar Lane"),
    ("DS-2023-011", "Zara", "Khan", "zara.khan@campus.edu", "+1-555-0106", "Female", "2003-01-30", "Data Science", 2, "88 Sunset Park"),
    ("BA-2023-040", "James", "Wilson", "james.w@campus.edu", "+1-555-0111", "Male", "2002-03-15", "Business Admin", 3, "112 Grand Concourse")
]

# Pure MCA Courses according to R. C. Patel IMRD Timetable
ALL_COURSES = [
    # --- MCA Semester 1 (Theory & Practical) ---
    (
        "MCA-411",
        "Java Programming (Theory)",
        "MCA",
        4,
        "MCA Sem 1",
        "Prof. M. S. Sonawane (MSS) / Prof. V. A. Patil (VAP)",
        "Core Object-Oriented Programming using Java, exception handling, multithreading, collections framework, and event handling."
    ),
    (
        "MCA-412",
        "Java Programming Lab (Practical)",
        "MCA",
        2,
        "MCA Sem 1",
        "Prof. M. S. Sonawane (MSS) / Prof. V. A. Patil (VAP)",
        "Laboratory experiments on Java OOP principles, file handling, GUI application development, and JDBC database access."
    ),
    (
        "MCA-413",
        "Data Structures & Algorithms (Theory)",
        "MCA",
        4,
        "MCA Sem 1",
        "Prof. M. N. Bhalekar (MNB)",
        "Linear and non-linear data structures, algorithm complexity analysis, binary search trees, graph theory, sorting and searching."
    ),
    (
        "MCA-414",
        "Data Structures Lab (Practical)",
        "MCA",
        2,
        "MCA Sem 1",
        "Prof. V. M. Patil (VMP) / Prof. R. R. Patil (RRP)",
        "Practical implementation of stacks, queues, linked lists, binary trees, hashing, and shortest path algorithms."
    ),
    (
        "MCA-415",
        "Operating Systems (Theory)",
        "MCA",
        4,
        "MCA Sem 1",
        "Prof. R. R. Patil (RRP) / Prof. D. R. Nemade (DRN)",
        "Operating system concepts: process scheduling, threads, mutual exclusion, deadlock avoidance, virtual memory, and file systems."
    ),
    (
        "MCA-416",
        "Python Programming Lab (Practical)",
        "MCA",
        2,
        "MCA Sem 1",
        "MCA Department Lab Faculty",
        "Hands-on Python scripting: core syntax, data structures, functional programming, OOP, NumPy, and Pandas library fundamentals."
    ),
    (
        "MCA-417",
        "Web Technologies (Theory)",
        "MCA",
        4,
        "MCA Sem 1",
        "Prof. A. P. Patil (APP) / Prof. M. N. Bhalekar (MNB)",
        "Modern web development: HTML5, CSS3, JavaScript ES6+, DOM manipulation, responsive UI frameworks, and RESTful web services."
    ),
    (
        "MCA-418(A)",
        "Cloud Computing (Theory)",
        "MCA",
        3,
        "MCA Sem 1",
        "Prof. A. R. Patil (ARP)",
        "Cloud architectural models, virtualization, Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and cloud security."
    ),
    (
        "MCA-418(B)",
        "Cloud Computing Lab (Practical)",
        "MCA",
        2,
        "MCA Sem 1",
        "Prof. A. R. Patil (ARP)",
        "Hands-on cloud experiments: virtual machine configuration, cloud storage bucket management, containerization with Docker."
    ),
    (
        "MCA-419(A)",
        "Data Science (Theory)",
        "MCA",
        3,
        "MCA Sem 1",
        "Prof. D. G. Patil (DGP)",
        "Foundations of data science, statistical inference, exploratory data analysis, data wrangling, and predictive modeling."
    ),
    (
        "MCA-419(B)",
        "Data Science Lab (Practical)",
        "MCA",
        2,
        "MCA Sem 1",
        "Prof. D. G. Patil (DGP) / Prof. H. L. Chaudhari (HLC)",
        "Practical data analytics workflows using Python, Pandas, Matplotlib, Seaborn, and Scikit-Learn machine learning pipelines."
    ),
    (
        "MCA-421(A)",
        "Web Development Elective (Theory)",
        "MCA",
        3,
        "MCA Sem 1",
        "Prof. V. N. Chaudhari (VNC)",
        "Advanced full-stack web architectures, server-side rendering, asynchronous request handling, and web application security."
    ),
    (
        "MCA-421(B)",
        "Web Development Lab (Practical)",
        "MCA",
        2,
        "MCA Sem 1",
        "Prof. V. N. Chaudhari (VNC)",
        "Laboratory projects building end-to-end web applications with backend APIs, database integration, and reactive frontends."
    ),
    (
        "MCA-457(B)",
        "DevOps Lab (Practical)",
        "MCA",
        2,
        "MCA Sem 1",
        "MCA DevOps Faculty Team",
        "Practical continuous integration and deployment (CI/CD), Git version control workflows, container orchestration, and automated testing."
    ),

    # --- MCA Semester 3 (MCA 2) ---
    (
        "MCA-512",
        "Advanced Software Engineering & Big Data",
        "MCA",
        4,
        "MCA Sem 3",
        "Prof. R. B. Bagul (RBB) / Prof. H. L. Chaudhari (HLC)",
        "Agile software processes, architectural patterns, big data fundamentals, Hadoop ecosystem, and distributed processing."
    ),
    (
        "MCA-517(A)",
        "Machine Learning & Cloud Infrastructure",
        "MCA",
        4,
        "MCA Sem 3",
        "Prof. V. S. Tamboli (VST) / Prof. A. R. Patil (ARP)",
        "Supervised and unsupervised learning algorithms, artificial neural networks, model deployment on cloud platforms."
    )
]

def seed():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM attendance")
    cursor.execute("DELETE FROM enrollments")
    cursor.execute("DELETE FROM courses")
    cursor.execute("DELETE FROM students")

    # Insert Students
    for s in SAMPLE_STUDENTS:
        cursor.execute('''
            INSERT INTO students (roll_no, first_name, last_name, email, phone, gender, dob, department, year, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', s)

    # Insert Courses
    for c in ALL_COURSES:
        cursor.execute('''
            INSERT INTO courses (code, name, department, credits, semester, instructor, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', c)

    conn.commit()

    # Fetch created IDs
    students = cursor.execute("SELECT id, roll_no, email, department FROM students").fetchall()
    courses = cursor.execute("SELECT id, code, department, semester FROM courses").fetchall()

    # Create enrollments
    random.seed(42)
    for s in students:
        s_id = s['id']
        s_dept = s['department']

        # Match relevant department courses
        dept_courses = [c['id'] for c in courses if c['department'] == s_dept]
        if not dept_courses:
            dept_courses = [c['id'] for c in courses]

        # Enroll in 3 to 6 courses
        num_courses = min(len(dept_courses), random.randint(3, 6))
        chosen = random.sample(dept_courses, num_courses)

        for c_id in chosen:
            score = round(random.uniform(62, 96), 1)
            grade, _ = score_to_grade(score)
            status = "Completed" if score >= 50 else "Enrolled"
            cursor.execute('''
                INSERT INTO enrollments (student_id, course_id, semester, score, grade, status)
                VALUES (?, ?, 'Fall 2026', ?, ?, ?)
            ''', (s_id, c_id, score, grade, status))

    conn.commit()

    # Seed Attendance for the past 5 working days
    base_date = datetime.now() - timedelta(days=7)
    attendance_dates = []
    curr = base_date
    while len(attendance_dates) < 5:
        if curr.weekday() < 5:
            attendance_dates.append(curr.strftime('%Y-%m-%d'))
        curr += timedelta(days=1)

    enrollments = cursor.execute("SELECT student_id, course_id FROM enrollments").fetchall()
    statuses = ["Present", "Present", "Present", "Present", "Late", "Absent"]

    for enr in enrollments:
        for dt in attendance_dates:
            status = random.choice(statuses)
            cursor.execute('''
                INSERT OR IGNORE INTO attendance (student_id, course_id, date, status)
                VALUES (?, ?, ?, ?)
            ''', (enr['student_id'], enr['course_id'], dt, status))

    # Seed Users (Admin & Students)
    admin_pw = generate_password_hash("admin123")
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role)
        VALUES ('admin', 'admin@rcpimrd.ac.in', ?, 'admin')
    ''', (admin_pw,))

    # Default demo student
    first_student = students[0] if students else None
    student_pw = generate_password_hash("student123")
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role, student_id)
        VALUES ('student', 'student@rcpimrd.ac.in', ?, 'student', ?)
    ''', (student_pw, first_student['id'] if first_student else None))

    # User account for each student (Username = Roll No, Password = student123)
    for s in students:
        s_pw = generate_password_hash("student123")
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, role, student_id)
            VALUES (?, ?, ?, 'student', ?)
        ''', (s['roll_no'], s['email'], s_pw, s['id']))

    conn.commit()
    conn.close()
    print(f"Successfully seeded database with {len(SAMPLE_STUDENTS)} students, {len(ALL_COURSES)} MCA courses, and user authentication accounts!")

if __name__ == '__main__':
    seed()
