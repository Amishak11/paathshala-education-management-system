from flask import Blueprint, render_template, request, jsonify, session, redirect
from extensions import db
from models import TimetableSlot, Student

timetable_bp = Blueprint("timetable_bp", __name__, url_prefix="/timetable")


def clean_text(x):
    if not x:
        return ""
    return " ".join(str(x).strip().split())


def time_key(ts: str) -> int:
    """
    Sort time like: 09:00-10:00 < 10:00-11:00
    """
    try:
        start = ts.split("-")[0].strip()
        h, m = start.split(":")
        return int(h) * 60 + int(m)
    except:
        return 10**9


@timetable_bp.route("/admin", methods=["GET"])
def admin_timetable():
    return render_template("admin/timetable.html")


@timetable_bp.route("/save", methods=["POST"])
def save_timetable():
    data = request.json or {}
    class_name = clean_text(data.get("class_name"))
    slots = data.get("slots", [])

    if not class_name:
        return jsonify({"message": "❌ class_name is required"}), 400

    # ✅ Delete old timetable of this class first (then insert new)
    TimetableSlot.query.filter_by(class_name=class_name).delete(synchronize_session=False)

    for s in slots:
        day = clean_text(s.get("day"))
        time_slot = clean_text(s.get("time_slot"))
        subject = clean_text(s.get("subject"))
        faculty_name = clean_text(s.get("faculty_name"))

        # must have day + time + subject
        if not (day and time_slot and subject):
            continue

        db.session.add(
            TimetableSlot(
                class_name=class_name,
                day=day,
                time_slot=time_slot,
                subject=subject,
                faculty_name=faculty_name
            )
        )

    db.session.commit()
    return jsonify({"message": "✅ Timetable Saved Successfully!"})


@timetable_bp.route("/get/<class_name>", methods=["GET"])
def get_class_timetable(class_name):
    class_name = clean_text(class_name)
    slots = TimetableSlot.query.filter_by(class_name=class_name).all()

    return jsonify({
        "class_name": class_name,
        "slots": [
            {
                "day": s.day,
                "time_slot": s.time_slot,
                "subject": s.subject,
                "faculty_name": s.faculty_name
            }
            for s in slots
        ]
    })


# ✅ NEW: student timetable JSON API (optional, but very useful for dashboard)
@timetable_bp.route("/student/data", methods=["GET"])
def student_timetable_data():
    student_email = session.get("student_email")
    if not student_email:
        return jsonify({"error": "login required"}), 401

    student = Student.query.filter_by(email=student_email).first()
    if not student:
        return jsonify({"error": "student not found"}), 404

    slots = TimetableSlot.query.filter_by(class_name=student.student_class).all()

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

    return jsonify({
        "student_class": student.student_class,
        "days": days_in_db,
        "time_slots": time_slots,
        "slots": [
            {
                "day": s.day,
                "time_slot": s.time_slot,
                "subject": s.subject,
                "faculty_name": s.faculty_name
            }
            for s in slots
        ]
    })


@timetable_bp.route("/student", methods=["GET"])
def student_timetable():
    student_email = session.get("student_email")
    if not student_email:
        return redirect("/login/student")

    student = Student.query.filter_by(email=student_email).first()
    if not student:
        return redirect("/login/student")

    slots = TimetableSlot.query.filter_by(class_name=student.student_class).all()

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

    # ✅ IMPORTANT:
    # send both "slots" + "timetable/days/time_slots"
    # so ANY timetable.html style will work
    return render_template(
        "student/timetable.html",
        student=student,
        student_class=student.student_class,
        slots=slots,              
        days=days_in_db,
        time_slots=time_slots,
        timetable=timetable
    )