from flask import Blueprint, render_template, session, redirect, jsonify, request
from datetime import date, datetime, timedelta
from sqlalchemy import func
from extensions import db

from models import (
    Announcement,
    Notes,
    FacultyLectureLog,
    FacultyLeave,
    FacultyLogin,
    Faculty,
    TimetableSlot,
    Student,
    StudentAttendance
)

faculty_bp = Blueprint("faculty_bp", __name__, url_prefix="/faculty")


# -----------------------
# Helpers
# -----------------------
def norm_name(x: str) -> str:
    """trim + collapse spaces + lowercase"""
    if not x:
        return ""
    return " ".join(str(x).strip().split()).lower()


def time_key(ts: str) -> int:
    """
    Sort time slots by start time.
    Example: '09:00-10:00' -> 540
    """
    try:
        start = ts.split("-")[0].strip()
        h, m = start.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 10**9


def status_to_ui(s: str) -> str:
    """DB status ('P'/'A') -> UI status ('Present'/'Absent')"""
    return "Present" if s == "P" else "Absent"


def ui_to_status(s: str) -> str:
    """UI status ('Present'/'Absent') -> DB status ('P'/'A')"""
    return "P" if str(s).lower() == "present" else "A"


# -----------------------
# Login redirect
# -----------------------
@faculty_bp.route("/login", methods=["GET"])
def faculty_login_redirect():
    return redirect("/login/faculty")


# -----------------------
# ✅ FACULTY DASHBOARD
# -----------------------
@faculty_bp.route("/dashboard")
def faculty_dashboard():
    faculty_name = session.get("faculty_name")
    faculty_phone = session.get("faculty_phone")

    if not faculty_name:
        return redirect("/login/faculty")

    today_day = date.today().strftime("%A")
    faculty_key = norm_name(faculty_name)

    today_slots = TimetableSlot.query.filter(
        func.lower(func.trim(TimetableSlot.faculty_name)) == faculty_key,
        TimetableSlot.day == today_day
    ).all()

    notes_count = Notes.query.count()

    announcements = Announcement.query.order_by(
        Announcement.event_date.desc()
    ).all()

    leave = None
    if faculty_phone:
        leave = FacultyLeave.query.filter_by(
            faculty_phone=faculty_phone,
            month=date.today().strftime("%B")
        ).first()

    lectures = []
    if faculty_phone:
        lectures = FacultyLectureLog.query.filter_by(
            faculty_phone=faculty_phone
        ).order_by(FacultyLectureLog.date.desc()).all()

    return render_template(
        "faculty/dashboard.html",
        name=faculty_name,
        notes_count=notes_count,
        announcements=announcements,
        leave=leave,
        lectures=lectures,
        today_slots=today_slots,
        date=date
    )


@faculty_bp.route("/attendance")
def faculty_attendance():
    faculty_phone = session.get("faculty_phone")
    if not faculty_phone:
        return redirect("/login/faculty")

    records = FacultyLectureLog.query.filter_by(
        faculty_phone=faculty_phone
    ).order_by(FacultyLectureLog.date.desc()).all()

    return render_template("faculty/attendance.html", records=records)


@faculty_bp.route("/notes")
def faculty_notes():
    if not session.get("faculty_name"):
        return redirect("/login/faculty")

    notes = Notes.query.all()
    return render_template("faculty/notes.html", notes=notes)


# -----------------------
# ✅ ADMIN: Add/View/Edit Faculty (keep as-is)
# -----------------------
@faculty_bp.route("/add", methods=["GET"])
def add_faculty_view():
    return render_template("admin/add_faculty.html")


@faculty_bp.route("/add", methods=["POST"])
def add_faculty_api():
    data = request.json
    email = data["email"].lower()

    if Faculty.query.filter_by(email=email).first():
        return jsonify({"message": "Faculty already exists"}), 400

    faculty = Faculty(
        name=data["name"],
        subject=data["subject"],
        email=email,
        phone=data["phone"],
        experience=data["experience"],
        qualification=data["qualification"]
    )
    db.session.add(faculty)

    login = FacultyLogin(
        email=email,
        password=data.get("password", "faculty123")
    )
    db.session.add(login)

    db.session.commit()
    return jsonify({"message": "Faculty added successfully"})


@faculty_bp.route("/view")
def view_faculty():
    return render_template("admin/view_faculty.html")


@faculty_bp.route("/all", methods=["GET"])
def get_faculty():
    faculty = Faculty.query.all()
    return jsonify([
        {
            "id": f.id,
            "name": f.name,
            "subject": f.subject,
            "email": f.email,
            "phone": f.phone,
            "experience": f.experience,
            "qualification": f.qualification
        }
        for f in faculty
    ])


@faculty_bp.route("/update/<int:id>", methods=["PUT"])
def update_faculty(id):
    data = request.json

    faculty = Faculty.query.get(id)
    if not faculty:
        return jsonify({"message": "Faculty not found"}), 404

    faculty.name = data.get("name")
    faculty.subject = data.get("subject")
    faculty.email = data.get("email").lower()
    faculty.phone = data.get("phone")
    faculty.experience = data.get("experience")
    faculty.qualification = data.get("qualification")

    if data.get("password"):
        login = FacultyLogin.query.filter_by(email=faculty.email).first()
        if login:
            login.password = data["password"]

    db.session.commit()
    return jsonify({"message": "Faculty updated successfully"})


@faculty_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_faculty(id):
    faculty = Faculty.query.get(id)
    if not faculty:
        return jsonify({"message": "Faculty not found"}), 404

    login = FacultyLogin.query.filter_by(email=faculty.email).first()
    if login:
        db.session.delete(login)

    db.session.delete(faculty)
    db.session.commit()
    return jsonify({"message": "Faculty deleted successfully"})


@faculty_bp.route("/edit/<int:id>")
def edit_faculty_page(id):
    faculty = Faculty.query.get(id)
    return render_template("admin/edit_faculty.html", faculty=faculty)


# -----------------------
# ✅ FACULTY TIMETABLE  (UPDATED: adds lecture_no + att_date)
# -----------------------
@faculty_bp.route("/timetable")
def faculty_timetable_view():
    faculty_name = session.get("faculty_name")
    if not faculty_name:
        return redirect("/login/faculty")

    faculty_key = norm_name(faculty_name)

    slots = TimetableSlot.query.filter(
        func.lower(func.trim(TimetableSlot.faculty_name)) == faculty_key
    ).all()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days = sorted(
        {s.day for s in slots if s.day},
        key=lambda d: day_order.index(d) if d in day_order else 99
    )

    time_slots = sorted({s.time_slot for s in slots if s.time_slot}, key=time_key)

    # ✅ this week's Monday
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    day_to_date = {day_order[i]: (week_start + timedelta(days=i)) for i in range(len(day_order))}

    # ✅ lecture numbers per day
    lecture_no_map = {}
    for d in days:
        day_ts = sorted({s.time_slot for s in slots if s.day == d and s.time_slot}, key=time_key)
        for idx, ts in enumerate(day_ts, start=1):
            lecture_no_map[(d, ts)] = idx

    timetable = {}
    for s in slots:
        timetable[(s.day, s.time_slot)] = {
            "class_name": s.class_name,
            "subject": s.subject or "",
            "lecture_no": lecture_no_map.get((s.day, s.time_slot), 1),
            "att_date": day_to_date.get(s.day)  # ✅ correct date for that weekday in this week
        }

    return render_template(
        "faculty/timetable.html",
        faculty_name=faculty_name,
        days=days,
        time_slots=time_slots,
        timetable=timetable,
        date=date
    )


# -----------------------
# ✅ TAKE ATTENDANCE PAGE (UPDATED: uses att_date from timetable)
# -----------------------
@faculty_bp.route("/attendance/take")
def take_attendance_page():
    faculty_name = session.get("faculty_name")
    if not faculty_name:
        return redirect("/login/faculty")

    class_name = request.args.get("class_name")
    day = request.args.get("day")
    time_slot = request.args.get("time_slot")
    subject = request.args.get("subject")
    lecture_no = request.args.get("lecture_no")
    att_date_str = request.args.get("att_date")  # ✅ from timetable link

    if not (class_name and day and time_slot and subject and att_date_str):
        return "Missing lecture details", 400

    try:
        att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()
    except Exception:
        return "Invalid att_date", 400

    students = Student.query.filter_by(student_class=class_name).all()

    existing = StudentAttendance.query.filter_by(
        class_name=class_name,
        day=day,
        time_slot=time_slot,
        subject=subject,
        faculty_name=faculty_name,
        att_date=att_date
    ).all()

    # map by phone (your template uses s.phone)
    id_to_student = {s.id: s for s in students}
    existing_map = {}
    for e in existing:
        st = id_to_student.get(e.student_id)
        if st:
            existing_map[st.phone] = status_to_ui(e.status)

    return render_template(
        "faculty/take_attendance.html",
        class_name=class_name,
        day=day,
        time_slot=time_slot,
        subject=subject,
        lecture_no=lecture_no,
        att_date=att_date_str,   
        students=students,
        existing_map=existing_map,
        date=date
    )


# -----------------------
# ✅ SAVE ATTENDANCE (FORM SUBMIT VERSION)  (UPDATED: uses att_date)
# -----------------------
@faculty_bp.route("/attendance/save", methods=["POST"])
def save_attendance():
    faculty_name = session.get("faculty_name")
    if not faculty_name:
        return redirect("/login/faculty")

    class_name = request.form.get("class_name")
    day = request.form.get("day")
    time_slot = request.form.get("time_slot")
    subject = request.form.get("subject")
    att_date_str = request.form.get("att_date")  

    if not (class_name and day and time_slot and subject and att_date_str):
        return "Missing lecture details", 400

    try:
        att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()
    except Exception:
        return "Invalid att_date", 400

    present_ids = set(int(x) for x in request.form.getlist("present_ids"))
    students = Student.query.filter_by(student_class=class_name).all()

    for st in students:
        status = "P" if st.id in present_ids else "A"

        rec = StudentAttendance.query.filter_by(
            class_name=class_name,
            day=day,
            time_slot=time_slot,
            subject=subject,
            faculty_name=faculty_name,
            student_id=st.id,
            att_date=att_date
        ).first()

        if rec:
            rec.status = status
        else:
            db.session.add(StudentAttendance(
                class_name=class_name,
                day=day,
                time_slot=time_slot,
                subject=subject,
                faculty_name=faculty_name,
                student_id=st.id,
                status=status,
                att_date=att_date
            ))

    db.session.commit()
    return redirect("/faculty/attendance/history")


# -----------------------
# ✅ SAVE ATTENDANCE (JSON/FETCH VERSION) (Already supports date) - KEEP
# -----------------------
@faculty_bp.route("/attendance/mark", methods=["POST"])
def save_attendance_json():
    faculty_name = session.get("faculty_name")
    if not faculty_name:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json() or {}
    date_str = data.get("date")  # "YYYY-MM-DD"
    class_name = data.get("class_name")
    subject = data.get("subject")
    day = data.get("day")
    time_slot = data.get("time_slot")
    records = data.get("records", [])

    if not (date_str and class_name and subject and records and day and time_slot):
        return jsonify({"message": "Missing fields (date/class/subject/day/time_slot/records)"}), 400

    try:
        att_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"message": "Invalid date format"}), 400

    students = Student.query.filter_by(student_class=class_name).all()
    phone_to_id = {s.phone: s.id for s in students}

    for r in records:
        phone = r.get("phone")
        status_ui_val = r.get("status", "Absent")
        student_id = phone_to_id.get(phone)
        if not student_id:
            continue

        status_db = ui_to_status(status_ui_val)

        rec = StudentAttendance.query.filter_by(
            class_name=class_name,
            day=day,
            time_slot=time_slot,
            subject=subject,
            faculty_name=faculty_name,
            student_id=student_id,
            att_date=att_date
        ).first()

        if rec:
            rec.status = status_db
        else:
            db.session.add(StudentAttendance(
                class_name=class_name,
                day=day,
                time_slot=time_slot,
                subject=subject,
                faculty_name=faculty_name,
                student_id=student_id,
                status=status_db,
                att_date=att_date
            ))

    db.session.commit()
    return jsonify({"message": "Attendance saved successfully ✅"})


# -----------------------
# ✅ ATTENDANCE HISTORY PAGE (SUMMARY)
# -----------------------
@faculty_bp.route("/attendance/history")
def faculty_attendance_history():
    faculty_name = session.get("faculty_name")
    if not faculty_name:
        return redirect("/login/faculty")

    records = StudentAttendance.query.filter_by(
        faculty_name=faculty_name
    ).order_by(StudentAttendance.att_date.desc()).all()

    grouped = {}
    for r in records:
        key = (r.att_date, r.class_name, r.day, r.time_slot, r.subject)
        grouped.setdefault(key, {"total": 0, "present": 0})
        grouped[key]["total"] += 1
        if r.status == "P":
            grouped[key]["present"] += 1

    sessions_list = []
    for k, v in grouped.items():
        att_date, class_name, day, time_slot, subject = k
        sessions_list.append({
            "att_date": att_date,
            "class_name": class_name,
            "day": day,
            "time_slot": time_slot,
            "subject": subject,
            "total": v["total"],
            "present": v["present"],
            "absent": v["total"] - v["present"]
        })

    sessions_list.sort(key=lambda x: x["att_date"], reverse=True)

    return render_template(
        "faculty/attendance_history.html",
        sessions=sessions_list,
        date=date
    )


# -----------------------
# ✅ API for detailed history (modal)
# URL: /faculty/attendance/api/details?date=YYYY-MM-DD
# -----------------------
@faculty_bp.route("/attendance/api/details")
def faculty_attendance_api_details():
    faculty_name = session.get("faculty_name")
    if not faculty_name:
        return jsonify([]), 401

    selected_date_str = request.args.get("date")
    if not selected_date_str:
        return jsonify([])

    try:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"error": "Invalid date format"}), 400

    rows = StudentAttendance.query.filter_by(
        faculty_name=faculty_name,
        att_date=selected_date
    ).all()

    if not rows:
        return jsonify([])

    student_ids = list({r.student_id for r in rows})
    students = Student.query.filter(Student.id.in_(student_ids)).all()
    id_to_student = {s.id: s for s in students}

    sessions = {}
    for r in rows:
        key = f"{r.class_name}__{r.subject}__{r.day}__{r.time_slot}"
        if key not in sessions:
            sessions[key] = {
                "class_name": r.class_name,
                "subject": r.subject,
                "day": r.day,
                "time_slot": r.time_slot,
                "lecture": r.time_slot,
                "students": []
            }

        st = id_to_student.get(r.student_id)
        sessions[key]["students"].append({
            "name": st.name if st else "Unknown",
            "phone": st.phone if st else "",
            "status": status_to_ui(r.status)
        })

    out = list(sessions.values())
    for s in out:
        s["students"].sort(key=lambda x: (x["name"] or "").lower())

    return jsonify(out)