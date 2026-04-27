from flask import Blueprint, render_template, redirect, url_for, jsonify, Response, request
from app.config import load as load_config
import logging

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/preview")
def preview():
    try:
        from app.print.pipeline import collect_data
        from app.print.renderer import render_digest
        cfg = load_config()
        data = collect_data(cfg)
        pdf_bytes = render_digest(data, cfg)
        return Response(pdf_bytes, mimetype="application/pdf")
    except Exception as e:
        logging.exception("Preview failed")
        return Response(f"Preview error: {e}", status=500, mimetype="text/plain")


@main_bp.route("/print", methods=["POST"])
def print_digest():
    return jsonify({"status": "ok", "message": "pipeline not yet wired"})


@main_bp.route("/settings", methods=["GET", "POST"])
def settings():
    return render_template("settings.html")
