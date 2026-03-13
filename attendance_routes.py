from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from extensions import db
from datetime import datetime
from sqlalchemy import func

attendance_bp = Blueprint("attendance_bp", __name__, url_prefix="/attendance")

FAC_CLASS = "__FACULTY__"
FAC_SUBJECT = "__FACULTY__"
FAC_LECTURE = "0"


# ==========================
# ADMIN: MANAGE PAGE (FACULTY)
# ==========================
@attendance_bp.route("/manage", methods=["GET"])
def manage_attendance():
   
    return render_template("admin/attendance.html")


# ==========================
# ✅ STUDENT: VIEW OWN ATTENDANCE PAGE
# ==========================
@attendance_bp.route("/student", methods=["GET"])
def student_attendance_page():
    from models import Student, Attendance

   
    student_email = session.get("student_email")
    if not student_email:
        return redirect("/login/student")

    student = Student.query.filter_by(email=student_email).first()
    if not student:
        return redirect("/login/student")

  
    student_phone = student.phone
    student_class = student.student_class

    attendance = (Attendance.query
        .filter_by(
            person_type="student",
            phone=student_phone,
            class_name=student_class
        )
        .order_by(Attendance.date.desc(), Attendance.created_at.desc())
        .all()
    )

    # ✅ Put your pasted HTML in: frontend/student/attendance.html
    return render_template(
        "student/attendance.html",
        student=student,
        attendance=attendance
    )


# ==========================
# API: STUDENTS LIST BY CLASS
# ==========================
@attendance_bp.route("/students/class/<class_name>")
def get_students_by_class(class_name):
    from models import Student
    students = Student.query.filter_by(student_class=class_name).all()

    # ✅ return full_name if exists else name
    return jsonify([
        {
            "name": (getattr(s, "full_name", None) or getattr(s, "name", "")),
            "phone": s.phone
        }
        for s in students
    ])


# ==========================
# API: FACULTY LIST
# ==========================
@attendance_bp.route("/faculty/list")
def get_faculty_list():
    from models import Faculty
    faculty = Faculty.query.all()
    return jsonify([{"name": f.name, "phone": f.phone} for f in faculty])


# ==========================
# ✅ SAVE/UPDATE ATTENDANCE (NO DUPLICATES)
# ==========================
@attendance_bp.route("/mark", methods=["POST"])
def mark_attendance():
    from models import Attendance
    data = request.json

    attendance_type = data.get("type", "student")
    date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()

    subject = (data.get("subject") or "").strip()
    lecture_no = (data.get("lecture_no") or "").strip()
    class_name = (data.get("class_name") or "").strip()
    section = (data.get("section") or "").strip()
    records = data.get("records", [])

    if not records:
        return jsonify({"message": "No records received"}), 400

    # ✅ Student validation
    if attendance_type == "student":
        if not subject or not lecture_no or not class_name:
            return jsonify({"message": "Missing student fields (Class/Subject/Lecture)"}), 400

    # ✅ Faculty placeholders so UNIQUE constraint works
    if attendance_type == "faculty":
        class_name = FAC_CLASS
        subject = FAC_SUBJECT
        lecture_no = FAC_LECTURE
        section = ""

    for r in records:
        phone = (r.get("phone") or "").strip()
        name = (r.get("name") or "").strip()
        status = (r.get("status") or "").strip()  # "Present"/"Absent"

        if not phone:
            continue

        existing = Attendance.query.filter_by(
            person_type=attendance_type,
            date=date_obj,
            phone=phone,
            class_name=class_name,
            subject=subject,
            lecture_no=lecture_no
        ).first()

        if existing:
            existing.name = name
            existing.status = status
            existing.section = section
            existing.created_at = datetime.utcnow()
        else:
            new_record = Attendance(
                person_type=attendance_type,
                name=name,
                phone=phone,
                class_name=class_name,
                section=section,
                subject=subject,
                lecture_no=lecture_no,
                date=date_obj,
                status=status
            )
            db.session.add(new_record)

    db.session.commit()
    return jsonify({"message": "Attendance Saved/Updated Successfully ✅"})


# ==========================
# ADMIN: VIEW PAGE
# ==========================
@attendance_bp.route("/view", methods=["GET"])
def view_attendance_page():
    return render_template("admin/view_attendance.html")


# ==========================
# ✅ VIEW RECORDS BY DATE (FACULTY or STUDENT)
# ==========================
@attendance_bp.route("/records", methods=["POST"])
def fetch_attendance_records():
    from models import Attendance
    data = request.json

    person_type = data.get("type")
    date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()

    class_name = (data.get("class_name") or "").strip()
    subject = (data.get("subject") or "").strip()
    lecture_no = (data.get("lecture_no") or "").strip()

    query = Attendance.query.filter_by(person_type=person_type, date=date_obj)

    # Student filtering
    if person_type == "student":
        if class_name:
            query = query.filter_by(class_name=class_name)
        if subject:
            query = query.filter_by(subject=subject)
        if lecture_no:
            query = query.filter_by(lecture_no=lecture_no)

    # Faculty should only show faculty placeholder rows
    if person_type == "faculty":
        query = query.filter_by(class_name=FAC_CLASS, subject=FAC_SUBJECT, lecture_no=FAC_LECTURE)

    records = query.order_by(Attendance.name.asc()).all()

    return jsonify([
        {
            "name": r.name,
            "phone": r.phone,
            "status": r.status,
            "class_name": r.class_name,
            "subject": r.subject,
            "lecture_no": r.lecture_no,
            "created_at": r.created_at.strftime("%d-%m-%Y %I:%M %p") if r.created_at else ""
        }
        for r in records
    ])


# ==========================================
# ✅ API: FETCH CLASS-WISE DETAILS FOR HISTORY MODAL (ADMIN CALENDAR)
# ==========================================
@attendance_bp.route("/api/details")
def get_calendar_attendance_details():
    from models import Attendance
    selected_date_str = request.args.get("date")

    if not selected_date_str:
        return jsonify([])

    try:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"error": "Invalid date format"}), 400

    records = Attendance.query.filter_by(
        person_type="student",
        date=selected_date
    ).all()

    sessions = {}
    for r in records:
        session_key = f"{r.class_name}_{r.subject}_{r.lecture_no}"

        if session_key not in sessions:
            sessions[session_key] = {
                "class_name": r.class_name,
                "subject": r.subject,
                "lecture": r.lecture_no,
                "students": []
            }

        sessions[session_key]["students"].append({
            "name": r.name,
            "status": r.status,
            "phone": r.phone
        })

    return jsonify(list(sessions.values()))