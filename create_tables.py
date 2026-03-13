from main import create_app, db  # make sure main.py has create_app() function
import models  # import all your SQLAlchemy models here

app = create_app()

with app.app_context():
    db.create_all()
    print("Tables created successfully!")
