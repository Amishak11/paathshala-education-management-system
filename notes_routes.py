import os
import re
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template, send_from_directory, session, redirect, abort
from extensions import db
from models import Notes, Student

# ✅ One blueprint only
notes_bp = Blueprint("notes_bp", __name__, url_prefix="/notes")

# ✅ Upload base folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BASE = os.path.normpath(os.path.join(BASE_DIR, "../uploads/notes"))

ALLOWED_EXT = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}
os.makedirs(UPLOAD_BASE, exist_ok=True)


def normalize_class(v: str) -> str:
    """
    Converts '7th', '7', 'Class 7' -> '7'
    """
    if not v:
        return ""
    v = str(v).strip().lower()
    m = re.search(r"\d+", v)
    return m.group(0) if m else v


# ==========================
# ✅ ADMIN: Upload page
# ==========================
@notes_bp.route("/upload", methods=["GET"])
def upload_notes_view():
    return render_template("admin/upload_notes.html")


# ==========================
# ✅ ADMIN: Upload API
# ==========================
@notes_bp.route("/upload", methods=["POST"])
def upload_notes_api():
    title = request.form.get("title")
    class_name = request.form.get("class_name")
    file = request.files.get("file")

    if not title or not class_name or not file:
        return jsonify({"message": "Missing data"}), 400
    
    subject = request.form.get("subject")

    if not subject:
        return jsonify({"message": "Missing subject"}), 400


    if "." not in file.filename:
        return jsonify({"message": "Invalid file name"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({"message": "Invalid file type"}), 400

    filename = secure_filename(file.filename)

    # ✅ IMPORTANT: keep same structure everywhere
    safe_class = secure_filename(str(class_name))
    class_folder = os.path.join(UPLOAD_BASE, f"class_{safe_class}")
    os.makedirs(class_folder, exist_ok=True)

    file.save(os.path.join(class_folder, filename))

    note = Notes(
    title=title,
    class_name=str(class_name),
    subject=subject,   # ✅ ADD THIS
    filename=filename,
    filetype=ext
)


    db.session.add(note)
    db.session.commit()

    return jsonify({"message": "Notes uploaded successfully ✅"})




# ==========================
# ✅ ADMIN: View page
# ==========================
@notes_bp.route("/view", methods=["GET"])
def admin_view_notes():
    return render_template("admin/view_notes.html")


# ==========================
# ✅ ADMIN: Get all notes JSON
# ==========================
@notes_bp.route("/all", methods=["GET"])
def get_notes():
    notes = Notes.query.order_by(Notes.id.desc()).all()
    output = {}

    for n in notes:
        key = str(n.class_name)
        output.setdefault(key, []).append({
            "id": n.id,
            "title": n.title,
            "filename": n.filename,
            "filetype": n.filetype
        })

    return jsonify(output)


# ==========================
# ✅ Common: Serve file (ONE route only)
# ==========================
@notes_bp.route("/file/<class_name>/<filename>")
def serve_notes_file(class_name, filename):
    class_name = secure_filename(str(class_name))
    filename = secure_filename(filename)

    folder = os.path.join(UPLOAD_BASE, f"class_{class_name}")
    file_path = os.path.join(folder, filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(folder, filename)


# ==========================
# ✅ ADMIN: Delete note
# ==========================
@notes_bp.route("/delete/<int:id>", methods=["POST"])
def delete_note(id):
    note = Notes.query.get_or_404(id)

    safe_class = secure_filename(str(note.class_name))
    file_path = os.path.join(UPLOAD_BASE, f"class_{safe_class}", note.filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(note)
    db.session.commit()

    return jsonify({"message": "Note deleted ✅"})


# ==========================
# ✅ ADMIN: Edit note title
# ==========================
@notes_bp.route("/edit/<int:id>", methods=["POST"])
def edit_note(id):
    data = request.get_json()
    note = Notes.query.get_or_404(id)

    note.title = data.get("title", note.title)
    db.session.commit()

    return jsonify({"message": "Note updated ✅"})


# ==========================
# ✅ STUDENT: View ONLY class notes
# ==========================
@notes_bp.route("/student/view", methods=["GET"])
def student_view_notes():
    student_email = session.get("student_email")
    if not student_email:
        return redirect("/login/student")

    student = Student.query.filter_by(email=student_email).first()
    if not student:
        return redirect("/login/student")

    student_key = normalize_class(student.student_class)

    all_notes = Notes.query.order_by(Notes.id.desc()).all()
    notes = [n for n in all_notes if normalize_class(n.class_name) == student_key]

    return render_template("student/view_notes.html", student=student, notes=notes)


# ==========================
# ✅ ADMIN: View notes by class (Folder click)
# URL: /notes/class/<class_name>
# ==========================
@notes_bp.route("/class/<class_name>")
def notes_by_class(class_name):
    class_name = str(class_name)

    notes = Notes.query.filter_by(class_name=class_name).order_by(Notes.id.desc()).all()

    return render_template(
        "admin/class_notes.html",
        class_name=class_name,
        notes=notes
    )
