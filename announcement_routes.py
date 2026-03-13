from flask import Blueprint, request, jsonify, render_template, redirect,session
from extensions import db
from datetime import datetime
from models import Announcement

announcement_bp = Blueprint("announcement_bp", __name__, url_prefix="/announcement")


# ============================
# ADMIN PAGE → ADD ANNOUNCEMENT
# ============================
@announcement_bp.route("/add", methods=["GET", "POST"])
def add_announcement():

    from models import Announcement

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        event_date = request.form["event_date"]
        type = request.form["type"]

        new_announcement = Announcement(
            title=title,
            description=description,
            event_date=datetime.strptime(event_date, "%Y-%m-%d").date(),
            type=type
        )

        db.session.add(new_announcement)
        db.session.commit()

        return redirect("/announcement/view")

    return render_template("admin/add_announcement.html")


# ============================
# ADMIN PAGE → VIEW ANNOUNCEMENTS
# ============================
@announcement_bp.route("/view")
def view_announcements():
    from models import Announcement

    announcements = Announcement.query.order_by(
        Announcement.event_date.desc()
    ).all()

    return render_template(
        "admin/view_announcements.html",
        announcements=announcements
    )


# ============================
# API → GET ALL ANNOUNCEMENTS
# For Student + Faculty Dashboards
# ============================
@announcement_bp.route("/all")
def get_all_announcements():
    from models import Announcement

    announcements = Announcement.query.order_by(
        Announcement.event_date.desc()
    ).all()

    return jsonify([
        {
            "title": a.title,
            "description": a.description,
            "event_date": a.event_date.strftime("%Y-%m-%d"),
            "type": a.type
        }
        for a in announcements
    ])


# ============================
# DELETE ANNOUNCEMENT (ADMIN)
# ============================
@announcement_bp.route("/delete/<int:id>")
def delete_announcement(id):
    from models import Announcement

    ann = Announcement.query.get_or_404(id)

    db.session.delete(ann)
    db.session.commit()

    return redirect("/announcement/view")


# =====================================================
# ✅ STUDENT PAGE → VIEW ANNOUNCEMENTS (READ ONLY)
# =====================================================
@announcement_bp.route("/student")
def student_announcements():
    student_email = session.get("student_email")
    if not student_email:
        return redirect("/login/student")

    announcements = Announcement.query.order_by(
        Announcement.event_date.desc()
    ).all()

    return render_template(
        "student/announcements.html",
        announcements=announcements
    )