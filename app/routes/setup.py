from flask import Blueprint, render_template

setup_bp = Blueprint("setup", __name__, url_prefix="/setup")


@setup_bp.route("/1")
def step1():
    return render_template("setup/step1_welcome.html")
