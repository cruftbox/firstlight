from flask import Blueprint, render_template, redirect, url_for, jsonify, Response, request
from app.config import load as load_config
import logging
import os
import time

main_bp = Blueprint("main", __name__)

_VERSION_CACHE = {"remote": None, "fetched_at": 0.0}
_VERSION_CACHE_TTL = 3600
_GITHUB_REPO = "cruftbox/firstlight"


@main_bp.route("/")
def index():
    from app.scheduler import scheduler
    next_run = None
    job = scheduler.get_job("daily_digest")
    if job and job.next_run_time:
        next_run = job.next_run_time.strftime("%I:%M %p").lstrip("0") or "12:00 AM"
    cfg = load_config()
    local_version = os.environ.get("FIRSTLIGHT_VERSION", "unknown")
    return render_template("index.html", next_run=next_run, config=cfg,
                           local_version=local_version)


@main_bp.route("/api/version")
def api_version():
    import requests
    local = os.environ.get("FIRSTLIGHT_VERSION", "unknown")
    if not local or local == "unknown":
        return jsonify({"local": local, "remote": None, "up_to_date": None,
                        "error": "version not baked into image"})
    now = time.time()
    remote = _VERSION_CACHE["remote"]
    if not remote or now - _VERSION_CACHE["fetched_at"] >= _VERSION_CACHE_TTL:
        try:
            r = requests.get(
                f"https://api.github.com/repos/{_GITHUB_REPO}/commits/master",
                headers={"Accept": "application/vnd.github+json"},
                timeout=5,
            )
            r.raise_for_status()
            remote = r.json()["sha"]
            _VERSION_CACHE["remote"] = remote
            _VERSION_CACHE["fetched_at"] = now
        except Exception as exc:
            logging.warning("Version check failed: %s", exc)
            return jsonify({"local": local, "remote": None, "up_to_date": None,
                            "error": "could not reach GitHub"})
    return jsonify({
        "local": local,
        "remote": remote,
        "up_to_date": local == remote,
    })


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
        printer_ip = request.form.get("printer_ip", "").strip()
        cfg["firstlight"]["printer_ip"] = printer_ip
        cfg["firstlight"]["printer"] = "Firstlight" if printer_ip else ""
        cfg["firstlight"]["paper_size"] = request.form.get("paper_size", "letter")
        cfg["quote"]["enabled"] = request.form.get("quote_enabled") == "on"
        cfg["history"]["enabled"] = request.form.get("history_enabled") == "on"
        cfg["weather"]["show_aqi"] = request.form.get("show_aqi") == "on"
        cfg["weather"]["show_rain_forecast"] = request.form.get("show_rain_forecast") == "on"
        cfg["world_cup"]["enabled"] = request.form.get("world_cup_enabled") == "on"
        cfg["tasks"]["source"] = request.form.get("tasks_source", "builtin")
        tasks_file_path = request.form.get("tasks_file_path", "").strip()
        if tasks_file_path:
            cfg["tasks"]["file_path"] = tasks_file_path
        cfg["tasks"]["api_url"] = request.form.get("tasks_api_url", "").strip()
        tasks_api_key = request.form.get("tasks_api_key", "").strip()
        if tasks_api_key:
            cfg["tasks"]["api_key"] = tasks_api_key
        cfg["tasks"]["api_filter"] = request.form.get("tasks_api_filter", "").strip()
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
