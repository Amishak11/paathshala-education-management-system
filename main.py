from flask import Flask, render_template, request, redirect, session
from flask_cors import CORS
from extensions import db


def create_app():
    app = Flask(
        __name__,
        template_folder="frontend",
        static_folder="frontend/assets"
    )

    app.secret_key = "paathshala_secret_key"
    CORS(app)

    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Amisha2005@localhost/paathshala_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # BLUEPRINTS
    from routes.admin_routes import admin_bp
    from routes.result_routes import result_bp
    from routes.student_routes import student_bp
    from routes.faculty_routes import faculty_bp
    from routes.subject_routes import subject_bp
    from routes.notes_routes import notes_bp
    from routes.attendance_routes import attendance_bp
   
    
   
    from routes.ai_routes import ai_bp
   
    from routes.announcement_routes import announcement_bp
    from routes.timetable_routes import timetable_bp

    app.register_blueprint(ai_bp)
    app.register_blueprint(result_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp)   # already /faculty in blueprint
    app.register_blueprint(subject_bp, url_prefix="/subject")
    app.register_blueprint(notes_bp)
    app.register_blueprint(attendance_bp)
  
   
    
 
    app.register_blueprint(announcement_bp)
    app.register_blueprint(timetable_bp)


    from flask import render_template

    @app.route("/gallery/<event>")
    def gallery(event):
        galleries = {
             "science-exhibition": {
             "title": "Science Exhibition",
             "subtitle": "All moments from our Science Exhibition event.",
             "images": [
                "images/p1.jpeg",
                "images/p3.jpeg",
                "images/p4.jpeg",
                "images/p5.jpeg",
                 "images/p6.jpeg",
                  "images/p7.jpeg",
                   "images/p8.jpeg"
            ]
        },
        "new-year": {
            "title": "New Year Celebration",
            "subtitle": "Celebrations and memories from New Year event.",
            "images": [
                "images/n1.jpeg",
                "images/n2.jpeg",
                "images/n5.jpeg",
                "images/n6.jpeg",
              
            ]
        },

         # ===== ACHIEVEMENTS =====
        "results": {
            "title": "95% Board Results",
            "subtitle": "Our top-performing students and achievements.",
            "images": [
                "images/top1.jpeg",
                "images/top2.jpeg"
                
            ]
        },

        "students": {
            "title": "Our Students",
            "subtitle": "Moments from our student community.",
            "images": [
                "images/s1.jpeg",
                "images/s2.jpeg",
                "images/s3.jpeg",
                 "images/s4.jpeg",
                  "images/s8.jpeg",
                   "images/n4.jpeg",
            ]
        },

        "faculty": {
            "title": "Expert Faculty",
            "subtitle": "Our experienced and dedicated teachers.",
            "images": [
                "images/fac1.jpg",
                "images/fac2.jpg"
            ]

        },
        "our picnic": {
            "title": "Our Picnic",
            "subtitle": "Enjoyment and best moments.",
            "images": [
                "images/x1.jpeg"
            ]
        }
    }

        data = galleries.get(event)
        if not data:
            return "Gallery not found", 404
        return render_template(
                "gallery.html",
                 title=data["title"],
                 subtitle=data["subtitle"],
                 images=data["images"]
                 ) 
    

    
        
      

    # ---------------- LOGOUT ----------------
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/")

    # ---------------- HOME ----------------
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    # ==========================================================
    # ✅ COMMON LOGIN PAGE (ONE LOGIN FOR ALL ROLES)
    # ==========================================================
    @app.route("/login", methods=["GET", "POST"])
    def common_login():
        if request.method == "GET":
            # role=None means user will select role in dropdown
            return render_template("login.html", role=None)

        role = request.form.get("role", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not role or not email or not password:
            return render_template("login.html", role=role, error="Please fill all fields.")

        # ---------------- ADMIN ----------------
        if role == "admin":
            if email == "admin@paathshala.com" and password == "admin123":
                session.clear()
                session["role"] = "admin"
                session["admin_email"] = email
                return redirect("/admin/dashboard")
            return render_template("login.html", role="admin", error="Invalid admin credentials.")

        # ---------------- STUDENT ----------------
        if role == "student":
            from models import Student, StudentLogin

            student = Student.query.filter_by(email=email).first()
            login_row = StudentLogin.query.filter_by(email=email, password=password).first()

            if student and login_row:
                session.clear()
                session["role"] = "student"
                session["student_id"] = student.id
                session["student_name"] = student.name
                session["student_email"] = student.email
                return redirect("/student/dashboard")

            return render_template("login.html", role="student", error="Invalid student login.")

        # ---------------- FACULTY ----------------
        if role == "faculty":
            from models import FacultyLogin, Faculty

            login_row = FacultyLogin.query.filter_by(email=email).first()
            if not login_row:
                return render_template("login.html", role="faculty", error="Faculty email not found.")

            if login_row.password != password:
                return render_template("login.html", role="faculty", error="Wrong password.")

            faculty = Faculty.query.filter_by(email=email).first()
            if not faculty:
                return render_template("login.html", role="faculty", error="Faculty profile not found.")

            session.clear()
            session["role"] = "faculty"
            session["faculty_name"] = faculty.name
            session["faculty_email"] = faculty.email
            session["faculty_phone"] = faculty.phone
            return redirect("/faculty/dashboard")

        return render_template("login.html", role=None, error="Invalid role selected.")

   
    @app.route("/login/<role>", methods=["GET"])
    def login_role(role):
        role = (role or "").strip().lower()
        if role not in ["student", "faculty", "admin"]:
            return redirect("/login")
        return render_template("login.html", role=role)

    return app

    


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)