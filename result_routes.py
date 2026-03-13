from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from extensions import db
from models import ExamResult, Student

result_bp = Blueprint("result_bp", __name__, url_prefix="/results")


# ===============================
# ✅ VIEW RESULTS (class wise)
# ===============================
@result_bp.route("/view")
@result_bp.route("/view/<class_name>")
def view_results(class_name=None):
    q = ExamResult.query
    if class_name:
        q = q.filter_by(class_name=class_name)

    results = q.order_by(ExamResult.id.desc()).all()
    return render_template("admin/view_results.html", results=results, selected_class=class_name)


# ===============================
# ✅ EDIT RESULT
# ===============================
@result_bp.route("/edit/<int:result_id>", methods=["GET", "POST"])
def edit_result(result_id):
    r = ExamResult.query.get_or_404(result_id)

    if request.method == "POST":
        r.student_name = (request.form.get("student_name") or "").strip()
        r.class_name = (request.form.get("class_name") or "").strip()
        r.subject = (request.form.get("subject") or "").strip()

        total_marks = int(request.form.get("total_marks") or 0)
        r.total_marks = total_marks

        exam_date = request.form.get("exam_date")
        r.exam_date = datetime.strptime(exam_date, "%Y-%m-%d").date() if exam_date else None

        is_absent = request.form.get("is_absent")
        if is_absent == "1":
            r.obtained_marks = -1
        else:
            r.obtained_marks = int(request.form.get("obtained_marks") or 0)

        # safety
        if r.obtained_marks != -1 and r.total_marks > 0 and r.obtained_marks > r.total_marks:
            r.obtained_marks = r.total_marks

        db.session.commit()
        return redirect(url_for("result_bp.view_results", class_name=r.class_name))

    return render_template("admin/edit_result.html", r=r)


# ===============================
# ✅ DELETE RESULT
# ===============================
@result_bp.route("/delete/<int:result_id>")
def delete_result(result_id):
    r = ExamResult.query.get_or_404(result_id)
    class_name = r.class_name
    db.session.delete(r)
    db.session.commit()
    return redirect(url_for("result_bp.view_results", class_name=class_name))