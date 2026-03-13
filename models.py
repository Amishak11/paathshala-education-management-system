from datetime import datetime
from extensions import db
 
from sqlalchemy import Column, Integer, String
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    student_class = db.Column(db.String(50), nullable=False)
    academic_year = db.Column(db.String(9), nullable=False)  # 👈 ADD THIS

    school = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)

    subjects = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(300))
    dob = db.Column(db.Date)



class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    phone = db.Column(db.String(15), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    qualification = db.Column(db.String(150), nullable=False)


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)

    person_type = db.Column(db.String(20))  # student / faculty

    name = db.Column(db.String(100))
    phone = db.Column(db.String(15))

    class_name = db.Column(db.String(20), nullable=True)
    section = db.Column(db.String(10), nullable=True)

    subject = db.Column(db.String(50), nullable=True)
    lecture_no = db.Column(db.String(20), nullable=True)

    date = db.Column(db.Date)
    status = db.Column(db.String(10))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class StudentLogin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

from extensions import db



class Marks(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)

    subject = db.Column(db.String(100))              # NEW
    test_name = db.Column(db.String(100))
    marks = db.Column(db.Integer)

    total_marks = db.Column(db.Integer, default=100) # NEW
    test_date = db.Column(db.Date)                   # NEW


class FacultyLogin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

from extensions import db
from datetime import datetime

class Notes(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    filetype = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(50), nullable=True)
    class_name = db.Column(db.String(50), nullable=False)

    

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )




class FacultyLectureSlot(db.Model):
    __tablename__ = "faculty_lecture_slot"

    id = db.Column(db.Integer, primary_key=True)

    schedule_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty_daily_schedule.id"),
        nullable=False
    )

    class_name = db.Column(db.String(10), nullable=False)
    subject = db.Column(db.String(100), nullable=False)

    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)








class AIChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)





class FacultyLectureLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_name = db.Column(db.String(100))   # ✅ ADD THIS
    faculty_phone = db.Column(db.String(15))
    date = db.Column(db.Date)
    subject = db.Column(db.String(100))
    in_time = db.Column(db.Time)
    out_time = db.Column(db.Time)


class FacultyLeave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_name = db.Column(db.String(100))   # ✅ ADD THIS
    faculty_phone = db.Column(db.String(15))
    month = db.Column(db.String(20))   # January
    sick_leave = db.Column(db.Integer, default=0)
    event_leave = db.Column(db.Integer, default=0)




class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    exam_date = db.Column(db.Date)
    description = db.Column(db.String(200))


class ExamResult(db.Model):
    __tablename__ = "exam_result"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id"),
        nullable=False
    )

    student_name = db.Column(db.String(100), nullable=False) 
    class_name = db.Column(db.String(50), nullable=False)

    subject = db.Column(db.String(100), nullable=False)

    exam_date = db.Column(db.Date, nullable=False)

    total_marks = db.Column(db.Integer, nullable=False)

    obtained_marks = db.Column(db.Integer, nullable=False)
class TimetableSlot(db.Model):
    __tablename__ = "timetable_slots"

    id = db.Column(db.Integer, primary_key=True)

    class_name = db.Column(db.String(20), nullable=False)   # 7th, 8th
    day = db.Column(db.String(10), nullable=False)          # Monday
    time_slot = db.Column(db.String(20), nullable=False)    # 09:00-10:00

    subject = db.Column(db.String(100))
    faculty_name = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class Fees(db.Model):
    __tablename__ = "fees"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_name = db.Column(db.String(100))
    amount = db.Column(db.Integer)

class StudentFees(db.Model):
    __tablename__ = "student_fees"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)

    academic_year = db.Column(db.String(9), nullable=False)
    total_fees = db.Column(db.Integer, nullable=False)
    paid_fees = db.Column(db.Integer, default=0)

    student = db.relationship("Student", backref="fees")


class FeeStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    academic_year = db.Column(db.String(9), nullable=False)  # 2025-26
    student_class = db.Column(db.String(10), nullable=False)

    tuition_fee = db.Column(db.Integer, nullable=False)
    language_fee = db.Column(db.Integer, nullable=False)

    total_fee = db.Column(db.Integer, nullable=False)



class FeePayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    amount_paid = db.Column(db.Integer, nullable=False)

    payment_date = db.Column(db.Date, default=datetime.utcnow)
    payment_mode = db.Column(db.String(20))  # cash / upi / card


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.String(300))


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    course = db.Column(db.String(100))
    date = db.Column(db.Date, default=datetime.utcnow)

from extensions import db

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(50))   # test / exam / homework / notice




class Homework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    description = db.Column(db.String(300))
    status = db.Column(db.String(20), default="Pending")

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(10), nullable=False)



from datetime import date, datetime
from extensions import db

class StudentAttendance(db.Model):
    __tablename__ = "student_attendance"

    id = db.Column(db.Integer, primary_key=True)

    # lecture info (from timetable)
    class_name = db.Column(db.String(20), nullable=False)
    day = db.Column(db.String(10), nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)

    # faculty
    faculty_name = db.Column(db.String(100), nullable=False)

    # student
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)

    # status
    status = db.Column(db.String(1), nullable=False, default="P")  # P / A

    # attendance date
    att_date = db.Column(db.Date, nullable=False, default=date.today)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
