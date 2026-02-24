from flask import Flask, render_template, request, redirect, session
import hashlib
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ================= DATABASE =================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="kmct_db"
    )


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    

    if request.method == "POST":

        db = get_db()
        cursor = db.cursor(dictionary=True)

        username = request.form["username"]
        password = hashlib.md5(
            request.form["password"].encode()
        ).hexdigest()

        cursor.execute(
            "SELECT * FROM admin WHERE username=%s AND password=%s",
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
    cursor = db.cursor(dictionary=True)

    selected_course = None
    selected_sem = None
    selected_div = None
    selected_sub_course = None
    selected_sub_sem = None

    students = []
    subjects = []

    # ================= POST ACTIONS =================
    if request.method == "POST":

        # -------- ADD STUDENT --------
        if "save_student" in request.form:
            cursor.execute("""
                INSERT INTO students
                (name, register_no, course_id, semester_id, division_id)
                VALUES (%s,%s,%s,%s,%s)
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
                VALUES (%s,%s,%s)
            """, (
                request.form["subject_name"],
                request.form["sub_course"],
                request.form["sub_sem"]
            ))
            db.commit()

        # -------- ADD EXAM --------
        elif "add_exam" in request.form:
            cursor.execute(
                "INSERT INTO exams (exam_name) VALUES (%s)",
                (request.form["exam_name"],)
            )
            db.commit()

        # -------- CLASS MANAGEMENT (FILTER + DELETE STUDENT) --------
        elif "manage_class" in request.form:

            selected_course = request.form["course"]
            selected_sem = request.form["sem"]
            selected_div = request.form["div"]

            # Delete single student
            if request.form.get("student_id"):
                cursor.execute(
                    "DELETE FROM students WHERE id=%s",
                    (request.form["student_id"],)
                )
                db.commit()

            # Fetch filtered students
            cursor.execute("""
                SELECT * FROM students
                WHERE course_id=%s AND semester_id=%s AND division_id=%s
            """, (selected_course, selected_sem, selected_div))

            students = cursor.fetchall()

        # -------- DELETE ENTIRE CLASS --------
        elif "delete_class_btn" in request.form:

            selected_course = request.form["course"]
            selected_sem = request.form["sem"]
            selected_div = request.form["div"]

            cursor.execute("""
                DELETE FROM students
                WHERE course_id=%s AND semester_id=%s AND division_id=%s
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
                WHERE course_id=%s AND semester_id=%s AND division_id=%s
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

            selected_sub_course = request.form["sub_course"]
            selected_sub_sem = request.form["sub_sem"]

            cursor.execute("""
                SELECT * FROM subjects
                WHERE course_id=%s AND semester_id=%s
            """, (selected_sub_course, selected_sub_sem))

            subjects = cursor.fetchall()

    # ================= DELETE LINKS (GET) =================
    if request.args.get("delete_subject"):
        cursor.execute(
            "DELETE FROM subjects WHERE id=%s",
            (request.args.get("delete_subject"),)
        )
        db.commit()
        return redirect("/page1")

    if request.args.get("delete_exam"):
        cursor.execute(
            "DELETE FROM exams WHERE id=%s",
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
    cursor = db.cursor(dictionary=True, buffered=True)

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
        WHERE s.id = %s
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
        WHERE course_id=%s AND semester_id=%s AND division_id=%s
    """, (student["course_id"], student["semester_id"], student["division_id"]))

    class_students = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM subjects
        WHERE course_id=%s AND semester_id=%s
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
        WHERE student_id=%s AND subject_id=%s
    """, (student_id, sub["id"]))

    att = cursor.fetchone()
    total_att = att["present"] if att else 0

    # Marks
    marks = []
    for exam in exams:
        cursor.execute("""
            SELECT mark FROM marks
            WHERE student_id=%s AND subject_id=%s AND exam_id=%s
        """, (student_id, sub["id"], exam["id"]))

        markData = cursor.fetchone()
        mark = markData["mark"] if markData else 0
        marks.append(mark)

    # ✅ NOW append (OUTSIDE exam loop)
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
    cursor = db.cursor(dictionary=True, buffered=True)

    # ---------- SAVE ATTENDANCE ----------
    for key in request.form:

        if key.startswith("att_"):

            subject_id = key.split("_")[1]
            attendance_value = request.form[key]

            # Check if record exists
            cursor.execute("""
                SELECT id FROM attendance
                WHERE student_id=%s AND subject_id=%s
            """, (student_id, subject_id))

            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE attendance
                    SET present=%s
                    WHERE student_id=%s AND subject_id=%s
                """, (attendance_value, student_id, subject_id))
            else:
                cursor.execute("""
                    INSERT INTO attendance
                    (student_id, subject_id, present)
                    VALUES (%s,%s,%s)
                """, (student_id, subject_id, attendance_value))


        # ---------- SAVE MARKS ----------
        if key.startswith("mark_"):

            parts = key.split("_")
            subject_id = parts[1]
            exam_id = parts[2]
            mark_value = request.form[key]

            cursor.execute("""
                SELECT id FROM marks
                WHERE student_id=%s AND subject_id=%s AND exam_id=%s
            """, (student_id, subject_id, exam_id))

            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE marks
                    SET mark=%s
                    WHERE student_id=%s AND subject_id=%s AND exam_id=%s
                """, (mark_value, student_id, subject_id, exam_id))
            else:
                cursor.execute("""
                    INSERT INTO marks
                    (student_id, subject_id, exam_id, mark)
                    VALUES (%s,%s,%s,%s)
                """, (student_id, subject_id, exam_id, mark_value))

    db.commit()
    cursor.close()
    db.close()

    return redirect(f"/page2/{student_id}")

    return redirect(f"/page2/{student_id}")
@app.route("/bulk_print/<int:course>/<int:sem>/<int:div>")
def bulk_print(course, sem, div):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Students in class
    cursor.execute("""
        SELECT s.*, c.course_name, sem.semester_name, d.division_name
        FROM students s
        LEFT JOIN courses c ON s.course_id = c.id
        LEFT JOIN semesters sem ON s.semester_id = sem.id
        LEFT JOIN divisions d ON s.division_id = d.id
        WHERE s.course_id=%s AND s.semester_id=%s AND s.division_id=%s
    """, (course, sem, div))

    students = cursor.fetchall()

    # Subjects
    cursor.execute("""
        SELECT * FROM subjects
        WHERE course_id=%s AND semester_id=%s
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
                WHERE student_id=%s AND subject_id=%s
            """, (student["id"], sub["id"]))

            att = cursor.fetchone()
            total_att = att["total"] if att["total"] else 0

            # Marks
            marks = []
            for exam in exams:
                cursor.execute("""
                    SELECT mark FROM marks
                    WHERE student_id=%s AND subject_id=%s AND exam_id=%s
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
