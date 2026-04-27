from flask import Blueprint, render_template, redirect, url_for

setup_bp = Blueprint("setup", __name__, url_prefix="/setup")


@setup_bp.route("/1", methods=["GET", "POST"])
def step1():
    return render_template("setup/step1_welcome.html")
