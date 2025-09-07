from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)

class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=60)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    role = SelectField("Role",
                       choices=[("viewer", "Viewer"), ("editor", "Editor"), ("admin", "Admin")],
                       validators=[DataRequired()])
    submit = SubmitField("Save")

# Routes
@app.route("/")
def list_users():
    users = User.query.all()
    return render_template("list.html", users=users)

@app.route("/create", methods=["GET", "POST"])
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data
        )
        db.session.add(user)
        db.session.commit()
        flash("✅ User created successfully", "success")
        return redirect(url_for("list_users"))
    return render_template("form.html", form=form, title="Create User")

@app.route("/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.role = form.role.data
        db.session.commit()
        flash("✏️ User updated successfully", "success")
        return redirect(url_for("list_users"))
    return render_template("form.html", form=form, title=f"Edit User #{user.id}")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
