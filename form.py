git checkout -b forms-module
git add forms.py
git commit -m "Add WTForms UserForm"
git push origin forms-module

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=60)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    role = SelectField(
        "Role",
        choices=[("viewer", "Viewer"), ("editor", "Editor"), ("admin", "Admin")],
        validators=[DataRequired()]
    )
    bio = TextAreaField("Bio", validators=[Length(max=280)])
    submit = SubmitField("Save")