from flask import Blueprint, request, jsonify, render_template # <-- ADDED render_template
from extensions import db


subject_bp = Blueprint("subject_bp", __name__)

# ----------------------------------------------------------------------
# 1. Admin View: Add Subject Page (NEW FUNCTION)
# Accessible via: /subject/add (using GET method from the Admin dashboard link)
# ----------------------------------------------------------------------
@subject_bp.route("/add", methods=["GET"])
def add_subject_view():
    from models import Subject
    # Renders the HTML file located at: frontend/admin/add_subject.html
    return render_template('admin/add_subject.html')


# ----------------------------------------------------------------------
# 2. Add Subject (API endpoint)
# NOTE: Renamed the function to avoid conflict with the GET view above.
# This endpoint handles the actual form submission (POST method).
# ----------------------------------------------------------------------
@subject_bp.route("/add", methods=["POST"])
def add_subject_api():
    from models import Subject # <-- Renamed to 'add_subject_api'
    data = request.json
    subject = Subject(name=data["name"])
    db.session.add(subject)
    db.session.commit()
    return jsonify({"message": "Subject added successfully"}), 201


# ----------------------------------------------------------------------
# 3. Get All Subjects (API endpoint)
# ----------------------------------------------------------------------
@subject_bp.route("/all", methods=["GET"])
def all_subjects():
    from models import Subject
    subjects = Subject.query.all()
    result = [{"id": s.id, "name": s.name} for s in subjects]
    return jsonify(result)