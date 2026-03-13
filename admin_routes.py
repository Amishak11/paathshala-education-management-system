from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from extensions import db
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from datetime import datetime

from models import (
    Student, Faculty, Attendance, Announcement,
    ExamResult, Notes, TimetableSlot, Admin
)

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/login", methods=["GET"])
def admin_login_page():
    return render_template("login.html")


@admin_bp.route("/dashboard")
def admin_dashboard():
   
    student_count = Student.query.count()
    faculty_count = Faculty.query.count()
    announcement_count = Announcement.query.count()
    exam_count = ExamResult.query.count()

   
    top_students = []
    classes = ["7th", "8th", "9th", "10th"]

    for cls in classes:
        topper = (
            db.session.query(
                Student.name.label("name"),                 
                Student.student_class.label("student_class"),
                ExamResult.subject.label("subject"),
                ExamResult.obtained_marks.label("marks")          
            )
            .join(ExamResult, Student.id == ExamResult.student_id)
            .filter(Student.student_class == cls)
            .order_by(ExamResult.obtained_marks.desc())           
            .first()
        )

        if topper:
            top_students.append(topper)

    
    class_folders = []
    for cls in classes:
        cnt = Notes.query.filter_by(class_name=cls).count()
        class_folders.append({"class_name": cls, "count": cnt})

    
    subject_counts = (
        db.session.query(
            TimetableSlot.subject,
            func.count(TimetableSlot.id)
        )
        .filter(TimetableSlot.subject != "")
        .group_by(TimetableSlot.subject)
        .all()
    )

    lecture_labels = [x[0] for x in subject_counts]
    lecture_values = [x[1] for x in subject_counts]

    faculty_rows = (
        db.session.query(
            TimetableSlot.subject,
            TimetableSlot.faculty_name,
            func.count(TimetableSlot.id)
        )
        .filter(TimetableSlot.subject != "")
        .group_by(TimetableSlot.subject, TimetableSlot.faculty_name)
        .all()
    )

    lecture_faculty_map = {}
    for sub, fac, cnt in faculty_rows:
        lecture_faculty_map.setdefault(sub, []).append({"faculty": fac, "count": cnt})

    
    subject_health_query = (
        db.session.query(
            ExamResult.subject,
            func.avg(ExamResult.obtained_marks).label("avg_marks") 
        )
        .group_by(ExamResult.subject)
        .all()
    )

    subject_health_labels = [row[0] for row in subject_health_query]
    subject_health_values = [round(row[1], 1) for row in subject_health_query]

    
    return render_template(
        "admin/dashboard.html",
        student_count=student_count,
        faculty_count=faculty_count,
        announcement_count=announcement_count,
        exam_count=exam_count,
        top_students=top_students,
        class_folders=class_folders,
        lecture_labels=lecture_labels,
        lecture_values=lecture_values,
        lecture_faculty_map=lecture_faculty_map,
        subject_health_labels=subject_health_labels,
        subject_health_values=subject_health_values,
       
    )


@admin_bp.route("/add-result", methods=["GET", "POST"])
def add_result():
    if request.method == "POST":
        student_name = request.form.get("student_name") 
        class_name = request.form.get("class_name")
        subject = request.form.get("subject")

        obtained_marks = int(request.form.get("obtained_marks") or 0)
        exam_date = request.form.get("exam_date")
        total_marks = int(request.form.get("total_marks") or 0)

        # Optional safety check
        if total_marks > 0 and obtained_marks > total_marks:
            obtained_marks = total_marks

        new_result = ExamResult(
             student_name=student_name,
            class_name=class_name,
            subject=subject,
            obtained_marks=obtained_marks,
            exam_date=datetime.strptime(exam_date, "%Y-%m-%d") if exam_date else None,
            total_marks=total_marks
        )

        db.session.add(new_result)
        db.session.commit()
        return redirect("/admin/dashboard")

    students = Student.query.all()
    return render_template("admin/admin_add_result.html", students=students)


@admin_bp.route("/students-by-class")
def students_by_class():
    cls = request.args.get("class_name")

    students = Student.query.filter_by(student_class=cls).all()

    return jsonify({
        "students": [
            {"name": s.full_name if hasattr(s, "full_name") else s.name}
            for s in students
        ]
    })

@admin_bp.route("/results/view")
@admin_bp.route("/results/view/<class_name>")
def view_results(class_name=None):
    q = ExamResult.query

    if class_name:
        q = q.filter_by(class_name=class_name)

    results = q.order_by(ExamResult.id.desc()).all()

    return render_template(
        "admin/view_results.html",
        results=results,
        selected_class=class_name
    )
  