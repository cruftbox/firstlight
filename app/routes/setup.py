from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from datetime import date
import pytz
from app.config import load as load_config, save as save_config


def _safe_int(val, default: int) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


setup_bp = Blueprint("setup", __name__, url_prefix="/setup")


@setup_bp.route("/1", methods=["GET", "POST"])
def step1():
    cfg = load_config()
    if request.method == "POST":
        cfg["firstlight"]["paper_size"] = request.form.get("paper_size", "letter")
        save_config(cfg)
        return redirect(url_for("setup.step2"))
    return render_template("setup/step1_welcome.html", config=cfg)


@setup_bp.route("/2", methods=["GET", "POST"])
def step2():
    cfg = load_config()
    geocode_result = session.get("geocode_result")
    error = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "search":
            from app.providers.weather import geocode
            city = request.form.get("city", "").strip()
            result = geocode(city)
            if result:
                session["geocode_result"] = result
                geocode_result = result
            else:
                error = f'City "{city}" not found. Try a different name or spelling.'
        elif action == "confirm":
            result = session.pop("geocode_result", None)
            if result:
                cfg["location"]["city"] = result["name"]
                cfg["location"]["lat"] = result["lat"]
                cfg["location"]["lon"] = result["lon"]
                save_config(cfg)
                return redirect(url_for("setup.step3"))
            else:
                error = "Location search expired. Please search again."
    return render_template("setup/step2_location.html", config=cfg,
                           result=geocode_result, error=error)


@setup_bp.route("/3", methods=["GET", "POST"])
def step3():
    cfg = load_config()
    if request.method == "POST":
        cfg["firstlight"]["print_time"] = request.form.get("print_time", "06:30")
        cfg["firstlight"]["timezone"] = request.form.get("timezone", "America/Los_Angeles")
        cfg["weather"]["units"] = request.form.get("units", "imperial")
        save_config(cfg)
        return redirect(url_for("setup.step4"))
    return render_template("setup/step3_printtime.html", config=cfg,
                           timezones=pytz.all_timezones)


@setup_bp.route("/4", methods=["GET", "POST"])
def step4():
    cfg = load_config()
    if request.method == "POST":
        if request.form.get("action") != "skip":
            cfg["firstlight"]["printer"] = request.form.get("printer", "")
            save_config(cfg)
        return redirect(url_for("setup.step5"))
    from app.print.printer import get_printers
    return render_template("setup/step4_printer.html", config=cfg,
                           printers=get_printers())


@setup_bp.route("/5", methods=["GET", "POST"])
def step5():
    cfg = load_config()
    if request.method == "POST":
        cfg["quote"]["enabled"] = request.form.get("quote_enabled") == "on"
        save_config(cfg)
        return redirect(url_for("setup.step6"))
    preview_quote = None
    if cfg["quote"].get("enabled", True):
        from app.providers.quote import get_quote
        preview_quote = get_quote()
    return render_template("setup/step5_quote.html", config=cfg,
                           preview_quote=preview_quote)


@setup_bp.route("/6", methods=["GET", "POST"])
def step6():
    cfg = load_config()
    if request.method == "POST":
        if request.form.get("action") == "skip":
            return redirect(url_for("setup.step7"))
        creds_json = request.form.get("credentials_json", "").strip()
        if creds_json:
            from pathlib import Path
            creds_path = Path("/app/config/google_credentials.json")
            creds_path.parent.mkdir(parents=True, exist_ok=True)
            creds_path.write_text(creds_json, encoding="utf-8")
            cfg["calendar"]["enabled"] = True
            save_config(cfg)
        return redirect(url_for("setup.step7"))
    return render_template("setup/step6_calendar.html", config=cfg)


@setup_bp.route("/7", methods=["GET", "POST"])
def step7():
    cfg = load_config()
    if request.method == "POST":
        for league in ["mlb", "nfl", "nba", "wnba", "mls", "premier_league"]:
            raw = request.form.get(league, "").strip()
            cfg["sports"][league] = [t.strip() for t in raw.split(",") if t.strip()]
        save_config(cfg)
        return redirect(url_for("setup.step8"))
    return render_template("setup/step7_sports.html", config=cfg)


@setup_bp.route("/8", methods=["GET", "POST"])
def step8():
    cfg = load_config()
    if request.method == "POST":
        urls = request.form.getlist("feed_url")
        labels = request.form.getlist("feed_label")
        cfg["news"]["feeds"] = [
            {"url": u.strip(), "label": l.strip()}
            for u, l in zip(urls, labels)
            if u.strip()
        ]
        cfg["news"]["max_items"] = _safe_int(request.form.get("max_items"), 10)
        cfg["news"]["max_age_hours"] = _safe_int(request.form.get("max_age_hours"), 24)
        save_config(cfg)
        return redirect(url_for("setup.step9"))
    return render_template("setup/step8_news.html", config=cfg)


@setup_bp.route("/9", methods=["GET", "POST"])
def step9():
    cfg = load_config()
    if request.method == "POST":
        if request.form.get("action") == "skip":
            return redirect(url_for("setup.step10"))
        cfg["email"]["enabled"] = True
        cfg["email"]["smtp_host"] = request.form.get("smtp_host", "")
        cfg["email"]["smtp_port"] = _safe_int(request.form.get("smtp_port"), 587)
        cfg["email"]["smtp_user"] = request.form.get("smtp_user", "")
        cfg["email"]["smtp_password"] = request.form.get("smtp_password", "")
        cfg["email"]["from_address"] = request.form.get("from_address", "")
        cfg["email"]["to_address"] = request.form.get("to_address", "")
        save_config(cfg)
        return redirect(url_for("setup.step10"))
    return render_template("setup/step9_email.html", config=cfg)


@setup_bp.route("/9/test-email", methods=["POST"])
def test_email():
    import smtplib
    from email.message import EmailMessage
    data = request.get_json(silent=True) or {}
    cfg = load_config()

    # Password field is type=password so browsers never pre-fill it.
    # Fall back to the saved value when the form field is left blank.
    password = data.get("smtp_password") or cfg["email"]["smtp_password"]

    host = data.get("smtp_host", "")
    port = int(data.get("smtp_port") or 587)
    user = data.get("smtp_user", "")
    from_addr = data.get("from_address", "")
    to_addr = data.get("to_address", "")

    msg = EmailMessage()
    msg["Subject"] = "Firstlight — test email"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content("This is a test email from Firstlight. Your delivery settings are working.")

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port) as smtp:
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as smtp:
                smtp.starttls()
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@setup_bp.route("/10", methods=["GET", "POST"])
def step10():
    cfg = load_config()
    if request.method == "POST":
        cfg["firstlight"]["setup_complete"] = True
        save_config(cfg)
        from app.scheduler import start_scheduler
        from flask import current_app
        start_scheduler(current_app._get_current_object())
        return redirect(url_for("main.index"))
    return render_template("setup/step10_review.html", config=cfg)
