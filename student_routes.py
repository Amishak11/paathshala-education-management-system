from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from extensions import db
from datetime import datetime
from sqlalchemy import func

from models import (
    Student,
    StudentLogin,
   
    Notes,
    ExamResult,
    Announcement,

    Marks,
    Attendance,
    Subject,
    TimetableSlot
)

import re

def normalize_class(v: str) -> str:
    if not v:
        return ""
    v = str(v).strip().lower()
    m = re.search(r"\d+", v)
    return m.group(0) if m else v

student_bp = Blueprint("student_bp", __name__, url_prefix="/student")


# =========================
# Helpers
# =========================
def clean_text(x):
    if not x:
        return ""
    return " ".join(str(x).strip().split())


def norm_class(x: str) -> str:
    """Normalize class name for consistent matching"""
    return clean_text(x).lower()


def time_key(ts: str) -> int:
    """Sort time like 09:00-10:00 correctly"""
    try:
        start = ts.split("-")[0].strip()
        h, m = start.split(":")
        return int(h) * 60 + int(m)
    except:
        return 10**9


# =====================================================
# ✅ STUDENT DASHBOARD (NOW WITH TIMETABLE)
# =====================================================
@student_bp.route("/dashboard", methods=["GET"])
def student_dashboard():
    student_email = session.get("student_email")
    if not student_email:
        return redirect("/login/student")

    student = Student.query.filter_by(email=student_email).first()
    if not student:
        return redirect("/login/student")

    student_class_raw = student.student_class or ""
    student_class_norm = norm_class(student_class_raw)

    # ✅ Notes list for dashboard page (latest 5)
    class_notes = Notes.query.filter(
        func.lower(func.trim(Notes.class_name)) == student_class_norm
    ).order_by(Notes.id.desc()).limit(5).all()

   
    # ✅ Timetable for dashboard (same as timetable page)
    slots = TimetableSlot.query.filter(
        func.lower(func.trim(TimetableSlot.class_name)) == student_class_norm
    ).all()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days_in_db = sorted(
        {s.day for s in slots if s.day},
        key=lambda d: day_order.index(d) if d in day_order else 99
    )

    time_slots = sorted({s.time_slot for s in slots if s.time_slot}, key=time_key)

    timetable = {}
    for s in slots:
        timetable[(s.day, s.time_slot)] = {
            "subject": s.subject or "",
            "faculty": s.faculty_name or ""
        }

    return render_template(
        "student/dashboard.html",
        student=student,
        student_class=student_class_raw,   # show original in UI
        class_notes=class_notes,
       

        # ✅ timetable data for dashboard section
        slots=slots,
        days=days_in_db,
        time_slots=time_slots,
        timetable=timetable
    )


# =====================================================
# ✅ STUDENT TIMETABLE PAGE
# =====================================================
@student_bp.route("/timetable", methods=["GET"])
def student_timetable():
    student_email = session.get("student_email")
    if not student_email:
        return redirect("/login/student")

    student = Student.query.filter_by(email=student_email).first()
    if not student:
        return redirect("/login/student")

    student_class_raw = student.student_class or ""
    student_class_norm = norm_class(student_class_raw)

    slots = TimetableSlot.query.filter(
        func.lower(func.trim(TimetableSlot.class_name)) == student_class_norm
    ).all()

    return render_template(
        "student/view_timetable.html",
        student=student,
        student_class=student_class_raw,
        slots=slots
    )


# =====================================================
# ✅ STUDENT DASHBOARD DATA API (FOR CHART + CALENDAR)
# =====================================================
@student_bp.route("/dashboard/data", methods=["GET"])
def student_dashboard_data():
    student_email = session.get("student_email")
    if not student_email:
        return jsonify({"error": "not_logged_in"}), 401

    student = Student.query.filter_by(email=student_email).first()
    if not student:
        return jsonify({"error": "student_not_found"}), 404

    student_class_raw = student.student_class or ""
    student_class_norm = norm_class(student_class_raw)
    student_phone = student.phone

    # ---------------- Attendance ----------------
    total_lectures = (
        db.session.query(Attendance.date, Attendance.subject, Attendance.lecture_no)
        .filter(
            Attendance.person_type == "student",
            func.lower(func.trim(Attendance.class_name)) == student_class_norm
        )
        .distinct()
        .count()
    )

    present_lectures = Attendance.query.filter_by(
        person_type="student",
        phone=student_phone,
        class_name=student_class_raw,
        status="Present"
    ).count()

    attendance_percent = round((present_lectures / total_lectures) * 100) if total_lectures > 0 else 0

    # ---------------- Announcements ----------------
    announcement_count = Announcement.query.count()

    # ---------------- Notes count (class-wise) ----------------
    student_key = normalize_class(student.student_class)

    all_notes = Notes.query.order_by(Notes.id.desc()).all()


    class_notes = [n for n in all_notes if normalize_class(n.class_name) == student_key]

    notes_count = len(class_notes)


    notes_by_subject = {}
    for n in class_notes:
        sub = (getattr(n, "subject", None) or "General")
        notes_by_subject[sub] = notes_by_subject.get(sub, 0) + 1

    # ✅ JS in your dashboard expects an OBJECT/MAP, not list
    rows = (
        db.session.query(Notes.subject, func.count(Notes.id))
        .filter(func.lower(func.trim(Notes.class_name)) == student_class_norm)
        .group_by(Notes.subject)
        .all()
    )

    notes_by_subject = {}
    for sub, cnt in rows:
        notes_by_subject[sub or "General"] = cnt

    # ---------------- Calendar events ----------------
    calendar_events = []
    announcements = Announcement.query.all()
    for a in announcements:
        if getattr(a, "event_date", None):
            calendar_events.append({
                "title": a.title,
                "date": a.event_date.strftime("%Y-%m-%d"),
                "details": a.description or "",
                "type": a.type or "notice"
            })

    # ---------------- Marks ----------------
    marks_rows = Marks.query.filter_by(student_id=student.id).all()
    marks_data = []
    for m in marks_rows:
        marks_data.append({
            "test_name": getattr(m, "test_name", "") or "Test",
            "marks": getattr(m, "marks", 0) or 0,
            "subject": getattr(m, "subject", None),
            "total": getattr(m, "total_marks", None),
            "date": getattr(m, "test_date", None).strftime("%Y-%m-%d") if getattr(m, "test_date", None) else None
        })

    return jsonify({
        "attendance_percent": attendance_percent,
        "present_lectures": present_lectures,
        "total_lectures": total_lectures,

        "announcement_count": announcement_count,

        "notes_count": notes_count,
        "notes_by_subject": notes_by_subject,

        "marks_data": marks_data,
        "calendar_events": calendar_events
    })




# =====================================================
# ✅ STUDENT PROFILE
# =====================================================
@student_bp.route("/profile")
def student_profile():
    if "student_email" not in session:
        return redirect("/login/student")

    student = Student.query.filter_by(email=session["student_email"]).first()
    return render_template("student/student_profile.html", student=student)


# =====================================================
# ✅ STUDENT RESULTS (USING STUDENT NAME + CLASS)
# =====================================================
@student_bp.route("/results")
def student_results():
    student_email = session.get("student_email")
    student_name = session.get("student_name")

    if not student_email or not student_name:
        return redirect("/login/student")

    student = Student.query.filter_by(email=student_email).first()
    if not student:
        return redirect("/login/student")

    results = (ExamResult.query
               .filter_by(student_name=student_name, class_name=student.student_class)
               .order_by(
                   (ExamResult.exam_date.is_(None)).asc(),  # ✅ MySQL alternative to NULLS LAST
                   ExamResult.exam_date.desc(),
                   ExamResult.id.desc()
               )
               .all())

    # Group by date
    results_by_date = {}
    for r in results:
        date_key = r.exam_date.strftime("%Y-%m-%d") if r.exam_date else "No Date"
        results_by_date.setdefault(date_key, []).append(r)

    # Average marks (ignore absent=-1)
    valid_scores = [r.obtained_marks for r in results if r.obtained_marks is not None and r.obtained_marks >= 0]
    avg_marks = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0

    # Pass/Fail (ignore absent; fail if any subject < 35)
    status = "PASS"
    for r in results:
        if r.obtained_marks is not None and r.obtained_marks >= 0 and r.obtained_marks < 35:
            status = "FAIL"
            break

    return render_template(
        "student/student_results.html",
        student=student,
        results=results,
        results_by_date=results_by_date,
        avg_marks=avg_marks,
        status=status
    )

# =====================================================
# ✅ STUDENT LOGIN
# =====================================================
@student_bp.route("/login", methods=["POST"])
def student_login():
    email = request.form["email"].lower()
    password = request.form["password"]

    login = StudentLogin.query.filter_by(email=email, password=password).first()
    if not login:
        return "Invalid credentials"

    student = Student.query.filter_by(email=email).first()
    if not student:
        return "Student record not found"

    session["student_email"] = student.email
    session["student_name"] = student.name
    session["student_phone"] = student.phone

    # ✅ optional but useful if you still need it anywhere
    session["student_id"] = student.id

    return redirect(url_for("student_bp.student_dashboard"))


# =====================================================
# ✅ ADMIN → ADD STUDENT VIEW
# =====================================================
@student_bp.route("/add", methods=["GET"])
def add_student_view():
    return render_template("admin/add_student.html")


# =====================================================
# ✅ ADMIN → ADD STUDENT API
# =====================================================
@student_bp.route("/add", methods=["POST"])
def add_student_api():
    data = request.json
    email = data["email"].lower()

    if StudentLogin.query.filter_by(email=email).first():
        return jsonify({"message": "Student already exists"}), 400

    dob_value = None
    if data.get("dob"):
        dob_value = datetime.strptime(data["dob"], "%Y-%m-%d").date()

    student = Student(
        name=data["name"],
        student_class=data["student_class"],
        academic_year=data.get("academic_year", "2025-26"),
        school=data["school"],
        email=email,
        phone=data["phone"],
        subjects=",".join(data["subjects"]),
        address=data.get("address"),
        dob=dob_value
    )

    db.session.add(student)
    login = StudentLogin(email=email, password=data["password"])
    db.session.add(login)

    db.session.commit()
    return jsonify({"message": "Student added successfully"})


# =====================================================
# ✅ ADMIN → VIEW STUDENTS
# =====================================================
@student_bp.route("/view")
def view_students():
    return render_template("admin/view_students.html")


# =====================================================
# ✅ ADMIN → GET STUDENTS API
# =====================================================
@student_bp.route("/all", methods=["GET"])
def get_students():
    students = Student.query.all()
    return jsonify([
        {
            "id": s.id,
            "name": s.name,
            "class": s.student_class,
            "school": s.school,
            "email": s.email,
            "phone": s.phone,
            "subjects": s.subjects.split(",") if s.subjects else []
        }
        for s in students
    ])


# =====================================================
# ✅ ADMIN → UPDATE STUDENT
# =====================================================
@student_bp.route("/update/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.json
    student = Student.query.get(id)

    if not student:
        return jsonify({"message": "Student not found"}), 404

    student.name = data.get("name")
    student.student_class = data.get("student_class")
    student.school = data.get("school")
    student.email = data.get("email").lower()
    student.phone = data.get("phone")

    if data.get("subjects"):
        student.subjects = ",".join(data["subjects"])

    if data.get("password"):
        login = StudentLogin.query.filter_by(email=student.email).first()
        if login:
            login.password = data["password"]

    db.session.commit()
    return jsonify({"message": "Student updated successfully"})


# =====================================================
# ✅ ADMIN → DELETE STUDENT
# =====================================================
@student_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_student(id):
    student = Student.query.get(id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    login = StudentLogin.query.filter_by(email=student.email).first()
    if login:
        db.session.delete(login)

    db.session.delete(student)
    db.session.commit()

    return jsonify({"message": "Student deleted successfully"})


# =====================================================
# ✅ ADMIN → EDIT STUDENT PAGE
# =====================================================
@student_bp.route("/edit/<int:id>")
def edit_student_page(id):
    student = Student.query.get(id)
    return render_template("admin/edit_student.html", student=student)