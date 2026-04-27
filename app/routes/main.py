from flask import Blueprint, render_template, redirect, url_for, jsonify, Response, request
from app.config import load as load_config
import logging

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    from app.scheduler import scheduler
    next_run = None
    job = scheduler.get_job("daily_digest")
    if job and job.next_run_time:
        next_run = job.next_run_time.strftime("%I:%M %p").lstrip("0") or "12:00 AM"
    return render_template("index.html", next_run=next_run)


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
    from app.print.pipeline import run_pipeline
    try:
        run_pipeline()
        return jsonify({"status": "ok"})
    except Exception as e:
        logging.error("Print route error: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@main_bp.route("/settings", methods=["GET", "POST"])
def settings():
    from app.config import save as save_config
    from app.print.printer import get_printers
    from app.scheduler import reschedule
    import pytz

    cfg = load_config()

    if request.method == "POST":
        cfg["firstlight"]["print_time"] = request.form.get("print_time", cfg["firstlight"]["print_time"])
        cfg["firstlight"]["timezone"] = request.form.get("timezone", cfg["firstlight"]["timezone"])
        cfg["firstlight"]["printer"] = request.form.get("printer", "")
        cfg["firstlight"]["paper_size"] = request.form.get("paper_size", "letter")
        cfg["quote"]["enabled"] = request.form.get("quote_enabled") == "on"
        cfg["archive"]["enabled"] = request.form.get("archive_enabled") == "on"
        cfg["archive"]["retention_days"] = int(request.form.get("retention_days", 30))
        cfg["email"]["enabled"] = request.form.get("email_enabled") == "on"
        cfg["email"]["smtp_host"] = request.form.get("smtp_host", "")
        cfg["email"]["smtp_port"] = int(request.form.get("smtp_port", 587))
        cfg["email"]["smtp_user"] = request.form.get("smtp_user", "")
        smtp_password = request.form.get("smtp_password", "")
        if smtp_password:
            cfg["email"]["smtp_password"] = smtp_password
        cfg["email"]["from_address"] = request.form.get("from_address", "")
        cfg["email"]["to_address"] = request.form.get("to_address", "")
        save_config(cfg)
        reschedule(cfg["firstlight"]["print_time"], cfg["firstlight"]["timezone"])
        return redirect(url_for("main.settings") + "?saved=1")

    saved = request.args.get("saved") == "1"
    printers = get_printers()
    timezones = pytz.all_timezones
    return render_template("settings.html", config=cfg, printers=printers,
                           timezones=timezones, saved=saved)
