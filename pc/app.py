from flask import Flask, render_template, request, redirect, session
import hashlib
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey"

def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Create admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    # Create courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create semesters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semesters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create divisions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS divisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            division_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            register_no TEXT NOT NULL UNIQUE,
            course_id INTEGER NOT NULL,
            semester_id INTEGER NOT NULL,
            division_id INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (semester_id) REFERENCES semesters (id),
            FOREIGN KEY (division_id) REFERENCES divisions (id)
        )
    ''')
    
    # Create subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            semester_id INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (semester_id) REFERENCES semesters (id)
        )
    ''')
    
    # Create exams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            present INTEGER DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            UNIQUE(student_id, subject_id)
        )
    ''')
    
    # Create marks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            mark INTEGER DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (exam_id) REFERENCES exams (id),
            UNIQUE(student_id, subject_id, exam_id)
        )
    ''')
    
    # Insert default admin if not exists
    cursor.execute('SELECT COUNT(*) FROM admin')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO admin (username, password) VALUES (?, ?)', 
                      ('admin', hashlib.md5('admin'.encode()).hexdigest()))
    
    # Insert sample data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM courses')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO courses (course_name) VALUES (?)', [
            ('Computer Science',),
            ('Information Technology',),
            ('Electronics',)
        ])
    
    cursor.execute('SELECT COUNT(*) FROM semesters')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO semesters (semester_name) VALUES (?)', [
            ('1st Semester',),
            ('2nd Semester',),
            ('3rd Semester',),
            ('4th Semester',)
        ])
    
    cursor.execute('SELECT COUNT(*) FROM divisions')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO divisions (division_name) VALUES (?)', [
            ('A',),
            ('B',),
            ('C',)
        ])
    
    cursor.execute('SELECT COUNT(*) FROM exams')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO exams (exam_name) VALUES (?)', [
            ('Mid Term',),
            ('Final Exam',),
            ('Internal Assessment',)
        ])
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database on startup
init_db()

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cursor = db.cursor()

        username = request.form["username"]
        password = hashlib.md5(
            request.form["password"].encode()
        ).hexdigest()

        cursor.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password)
        )

        admin = cursor.fetchone()

        cursor.close()
        db.close()

        if admin:
            session["admin"] = username
            return redirect("/page1")
        else:
            return "<script>alert('Invalid Login');window.location='/'</script>"

    return render_template("login.html")

# ================= PAGE 1 =================
@app.route("/page1", methods=["GET", "POST"])
def page1():
    if "admin" not in session:
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    selected_course = None
    selected_sem = None
    selected_div = None
    selected_sub_course = None
    selected_sub_sem = None

    students = []
    subjects = []

    # ================= POST ACTIONS =================
    if request.method == "POST":

        # -------- PRESERVE FILTER STATE --------
        # Always capture filter values if they exist in the form
        if "course" in request.form and request.form["course"]:
            selected_course = request.form["course"]
        elif "preserve_course" in request.form:
            selected_course = request.form["preserve_course"]
            
        if "sem" in request.form and request.form["sem"]:
            selected_sem = request.form["sem"]
        elif "preserve_sem" in request.form:
            selected_sem = request.form["preserve_sem"]
            
        if "div" in request.form and request.form["div"]:
            selected_div = request.form["div"]
        elif "preserve_div" in request.form:
            selected_div = request.form["preserve_div"]
            
        if "sub_course" in request.form and request.form["sub_course"]:
            selected_sub_course = request.form["sub_course"]
        elif "preserve_sub_course" in request.form:
            selected_sub_course = request.form["preserve_sub_course"]
            
        if "sub_sem" in request.form and request.form["sub_sem"]:
            selected_sub_sem = request.form["sub_sem"]
        elif "preserve_sub_sem" in request.form:
            selected_sub_sem = request.form["preserve_sub_sem"]

        # -------- ADD STUDENT --------
        if "save_student" in request.form:
            cursor.execute("""
                INSERT INTO students
                (name, register_no, course_id, semester_id, division_id)
                VALUES (?,?,?,?,?)
            """, (
                request.form["name"],
                request.form["reg"],
                request.form["course"],
                request.form["sem"],
                request.form["div"],
            ))
            db.commit()

        # -------- ADD SUBJECT --------
        elif "add_subject" in request.form:
            cursor.execute("""
                INSERT INTO subjects
                (subject_name, course_id, semester_id)
                VALUES (?,?,?)
            """, (
                request.form["subject_name"],
                request.form["sub_course"],
                request.form["sub_sem"]
            ))
            db.commit()

        # -------- ADD EXAM --------
        elif "add_exam" in request.form:
            cursor.execute(
                "INSERT INTO exams (exam_name) VALUES (?)",
                (request.form["exam_name"],)
            )
            db.commit()

        # -------- CLASS MANAGEMENT (FILTER + DELETE STUDENT) --------
        elif "manage_class" in request.form:

            # Delete single student
            if request.form.get("student_id"):
                cursor.execute(
                    "DELETE FROM students WHERE id=?",
                    (request.form["student_id"],)
                )
                db.commit()

            # Fetch filtered students only if we have all filter values
            if selected_course and selected_sem and selected_div:
                cursor.execute("""
                    SELECT * FROM students
                    WHERE course_id=? AND semester_id=? AND division_id=?
                """, (selected_course, selected_sem, selected_div))

                students = cursor.fetchall()

        # -------- DELETE ENTIRE CLASS --------
        elif "delete_class_btn" in request.form:

            # Delete students only if we have all filter values
            if selected_course and selected_sem and selected_div:
                cursor.execute("""
                    DELETE FROM students
                    WHERE course_id=? AND semester_id=? AND division_id=?
                """, (selected_course, selected_sem, selected_div))

                db.commit()

            students = []

        # -------- VIEW CLASS --------
        elif "view_class" in request.form:

            course = request.form["course"]
            sem = request.form["sem"]
            div = request.form["div"]

            cursor.execute("""
                SELECT id FROM students
                WHERE course_id=? AND semester_id=? AND division_id=?
                LIMIT 1
            """, (course, sem, div))

            first_student = cursor.fetchone()

            if first_student:
                cursor.close()
                db.close()
                return redirect(f"/page2/{first_student['id']}")
            else:
                cursor.close()
                db.close()
                return """
                <h3 style='text-align:center;margin-top:50px'>
                No Students Found In Selected Class
                <br><br>
                <a href='/page1'>Go Back</a>
                </h3>
                """

        # -------- FILTER SUBJECTS --------
        elif "filter_subject" in request.form:

            # Fetch filtered subjects only if we have both filter values
            if selected_sub_course and selected_sub_sem:
                cursor.execute("""
                    SELECT * FROM subjects
                    WHERE course_id=? AND semester_id=?
                """, (selected_sub_course, selected_sub_sem))

                subjects = cursor.fetchall()

    # ================= DELETE LINKS (GET) =================
    if request.args.get("delete_subject"):
        cursor.execute(
            "DELETE FROM subjects WHERE id=?",
            (request.args.get("delete_subject"),)
        )
        db.commit()
        return redirect("/page1")

    if request.args.get("delete_exam"):
        cursor.execute(
            "DELETE FROM exams WHERE id=?",
            (request.args.get("delete_exam"),)
        )
        db.commit()
        return redirect("/page1")

    # ================= FETCH MASTER DATA =================
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    cursor.execute("SELECT * FROM semesters")
    semesters = cursor.fetchall()

    cursor.execute("SELECT * FROM divisions")
    divisions = cursor.fetchall()

    cursor.execute("SELECT * FROM exams")
    exams = cursor.fetchall()

    # If no class filter used → show all students
    if selected_course is None:
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()

    # If no subject filter used → show all subjects
    if selected_sub_course is None:
        cursor.execute("SELECT * FROM subjects")
        subjects = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "page1.html",
        courses=courses,
        semesters=semesters,
        divisions=divisions,
        students=students,
        subjects=subjects,
        exams=exams,
        selected_course=selected_course,
        selected_sem=selected_sem,
        selected_div=selected_div,
        selected_sub_course=selected_sub_course,
        selected_sub_sem=selected_sub_sem
    )

# ================= PAGE 2 =================
@app.route("/page2/<int:student_id>")
def page2(student_id):
    if "admin" not in session:
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM students")
    total_students = cursor.fetchone()

    if total_students["total"] == 0:
        cursor.close()
        db.close()
        return """
        <h2 style='text-align:center;margin-top:50px'>
        No Students Added Yet
        <br><br>
        <a href='/page1'>⬅ Go Back</a>
        </h2>
        """

    cursor.execute("""
        SELECT s.*, c.course_name, sem.semester_name, d.division_name
        FROM students s
        LEFT JOIN courses c ON s.course_id = c.id
        LEFT JOIN semesters sem ON s.semester_id = sem.id
        LEFT JOIN divisions d ON s.division_id = d.id
        WHERE s.id = ?
    """, (student_id,))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        db.close()
        return """
        <h2 style='text-align:center;margin-top:50px'>
        Student Not Found
        <br><br>
        <a href='/page1'>⬅ Go Back</a>
        </h2>
        """

    cursor.execute("""
        SELECT * FROM students
        WHERE course_id=? AND semester_id=? AND division_id=?
    """, (student["course_id"], student["semester_id"], student["division_id"]))

    class_students = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM subjects
        WHERE course_id=? AND semester_id=?
    """, (student["course_id"], student["semester_id"]))

    subjects = cursor.fetchall()

    cursor.execute("SELECT * FROM exams")
    exams = cursor.fetchall()

    data = []

    for sub in subjects:
        # Attendance
        cursor.execute("""
            SELECT present
            FROM attendance
            WHERE student_id=? AND subject_id=?
        """, (student_id, sub["id"]))

        att = cursor.fetchone()
        total_att = att["present"] if att else 0

        # Marks
        marks = []
        for exam in exams:
            cursor.execute("""
                SELECT mark FROM marks
                WHERE student_id=? AND subject_id=? AND exam_id=?
            """, (student_id, sub["id"], exam["id"]))

            markData = cursor.fetchone()
            mark = markData["mark"] if markData else 0
            marks.append(mark)

        # Append data
        data.append({
            "subject": sub["subject_name"],
            "subject_id": sub["id"],
            "attendance": total_att,
            "marks": marks
        })

    cursor.close()
    db.close()

    return render_template(
        "page2.html",
        student=student,
        class_students=class_students,
        data=data,
        exams=exams
    )

@app.route("/save_progress", methods=["POST"])
def save_progress():
    if "admin" not in session:
        return redirect("/")

    student_id = request.form["student_id"]

    db = get_db()
    cursor = db.cursor()

    # ---------- SAVE ATTENDANCE ----------
    for key in request.form:
        if key.startswith("att_"):
            subject_id = key.split("_")[1]
            attendance_value = request.form[key]

            # Check if record exists
            cursor.execute("""
                SELECT id FROM attendance
                WHERE student_id=? AND subject_id=?
            """, (student_id, subject_id))

            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE attendance
                    SET present=?
                    WHERE student_id=? AND subject_id=?
                """, (attendance_value, student_id, subject_id))
            else:
                cursor.execute("""
                    INSERT INTO attendance
                    (student_id, subject_id, present)
                    VALUES (?,?,?)
                """, (student_id, subject_id, attendance_value))

        # ---------- SAVE MARKS ----------
        if key.startswith("mark_"):
            parts = key.split("_")
            subject_id = parts[1]
            exam_id = parts[2]
            mark_value = request.form[key]

            cursor.execute("""
                SELECT id FROM marks
                WHERE student_id=? AND subject_id=? AND exam_id=?
            """, (student_id, subject_id, exam_id))

            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE marks
                    SET mark=?
                    WHERE student_id=? AND subject_id=? AND exam_id=?
                """, (mark_value, student_id, subject_id, exam_id))
            else:
                cursor.execute("""
                    INSERT INTO marks
                    (student_id, subject_id, exam_id, mark)
                    VALUES (?,?,?,?)
                """, (student_id, subject_id, exam_id, mark_value))

    db.commit()
    cursor.close()
    db.close()

    return redirect(f"/page2/{student_id}")

@app.route("/bulk_print/<int:course>/<int:sem>/<int:div>")
def bulk_print(course, sem, div):
    db = get_db()
    cursor = db.cursor()

    # Students in class
    cursor.execute("""
        SELECT s.*, c.course_name, sem.semester_name, d.division_name
        FROM students s
        LEFT JOIN courses c ON s.course_id = c.id
        LEFT JOIN semesters sem ON s.semester_id = sem.id
        LEFT JOIN divisions d ON s.division_id = d.id
        WHERE s.course_id=? AND s.semester_id=? AND s.division_id=?
    """, (course, sem, div))

    students = cursor.fetchall()

    # Subjects
    cursor.execute("""
        SELECT * FROM subjects
        WHERE course_id=? AND semester_id=?
    """, (course, sem))
    subjects = cursor.fetchall()

    # Exams
    cursor.execute("SELECT * FROM exams")
    exams = cursor.fetchall()

    final_data = []

    for student in students:
        subject_data = []

        for sub in subjects:
            # Attendance
            cursor.execute("""
                SELECT SUM(present) as total
                FROM attendance
                WHERE student_id=? AND subject_id=?
            """, (student["id"], sub["id"]))

            att = cursor.fetchone()
            total_att = att["total"] if att["total"] else 0

            # Marks
            marks = []
            for exam in exams:
                cursor.execute("""
                    SELECT mark FROM marks
                    WHERE student_id=? AND subject_id=? AND exam_id=?
                """, (student["id"], sub["id"], exam["id"]))

                m = cursor.fetchone()
                mark = m["mark"] if m else 0
                marks.append(mark)

            subject_data.append({
                "subject": sub["subject_name"],
                "attendance": total_att,
                "marks": marks
            })

        final_data.append({
            "student": student,
            "subjects": subject_data
        })

    cursor.close()
    db.close()

    return render_template(
        "bulk_print.html",
        data=final_data,
        exams=exams
    )

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)


