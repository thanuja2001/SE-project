from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User
from forms import UserForm

students_blueprint = Blueprint("students", __name__)

# ------------------------
# List students with search
# ------------------------
@students_blueprint.route("/users")
def list_users():
    query = request.args.get("q", "")  # Search query from URL
    if query:
        users = User.query.filter(
            (User.name.ilike(f"%{query}%")) |
            (User.email.ilike(f"%{query}%")) |
            (User.role.ilike(f"%{query}%"))
        ).all()
    else:
        users = User.query.all()
    return render_template("list.html", users=users, query=query)

# ------------------------
# Create student
# ------------------------
@students_blueprint.route("/create", methods=["GET", "POST"])
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data,
            bio=form.bio.data,
        )
        db.session.add(user)
        db.session.commit()
        flash(f"Created student #{user.id}", "success")
        return redirect(url_for("students.list_users"))
    return render_template("form.html", form=form, title="Add New Student")

# ------------------------
# Edit student
# ------------------------
@students_blueprint.route("/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.role = form.role.data
        user.bio = form.bio.data
        db.session.commit()
        flash(f"Updated student #{user.id}", "success")
        return redirect(url_for("students.list_users"))
    return render_template("form.html", form=form, title=f"Edit Student #{user.id}")

# ------------------------
# Delete student
# ------------------------
@students_blueprint.route("/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"Deleted student #{user.id}", "info")
    return redirect(url_for("students.list_users"))
