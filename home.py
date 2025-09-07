git checkout -b home-page
git add home.py
git commit -m "Add home page blueprint"
git push origin home-page

from flask import Blueprint, render_template_string
from templates import HOME_TEMPLATE

home_blueprint = Blueprint("home", _name_)

@home_blueprint.route("/")
def home():
    return render_template_string(HOME_TEMPLATE)