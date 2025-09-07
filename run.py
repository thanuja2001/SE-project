git checkout -b students-module
git add students.py
git commit -m "Add student CRUD blueprint"
git push origin students-module

from flask import Flask
from models import db
from home import home_blueprint
from run import students_blueprint

app = Flask(_name_)
app.secret_key = "supersecretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///students.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
app.register_blueprint(home_blueprint)
app.register_blueprint(students_blueprint)

if _name_ == "_main_":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)