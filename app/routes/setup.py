from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from datetime import date
import json
import logging
import os
import pytz
from urllib.parse import urlencode
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
    from pathlib import Path
    cfg = load_config()
    creds_path = Path("/app/config/google_credentials.json")
    token_path = Path("/app/config/google_token.json")

    error = request.args.get("error")
    authorized = request.args.get("authorized") == "1"

    if request.method == "POST":
        if request.form.get("action") == "skip":
            return redirect(url_for("setup.step7"))

        creds_json = request.form.get("credentials_json", "").strip()
        if creds_json:
            try:
                json.loads(creds_json)
            except json.JSONDecodeError as exc:
                return render_template(
                    "setup/step6_calendar.html", config=cfg,
                    creds_exist=creds_path.exists(), token_exist=token_path.exists(),
                    error=f"Invalid JSON: {exc}",
                )
            creds_path.parent.mkdir(parents=True, exist_ok=True)
            creds_path.write_text(creds_json, encoding="utf-8")
            # Reset any existing token when credentials change
            if token_path.exists():
                token_path.unlink()
        return redirect(url_for("setup.step6"))

    # Pre-generate the Google auth URL so the template can link directly to it.
    # This avoids any Flask/Werkzeug redirect handling that mangles https:// URLs.
    auth_url = None
    if creds_path.exists() and not token_path.exists():
        try:
            from google_auth_oauthlib.flow import Flow
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
            callback_url = request.url_root.rstrip("/") + "/setup/6/callback"
            flow = Flow.from_client_secrets_file(
                str(creds_path),
                scopes=["https://www.googleapis.com/auth/calendar.readonly"],
                redirect_uri=callback_url,
            )
            auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
            session["oauth_state"] = state
            session["oauth_redirect_uri"] = callback_url
            logging.info("Step6 generated auth_url starting: %s", auth_url[:60])
        except Exception as exc:
            logging.error("Failed to generate OAuth URL: %s", exc)
            error = error or str(exc)[:200]

    return render_template(
        "setup/step6_calendar.html", config=cfg,
        creds_exist=creds_path.exists(), token_exist=token_path.exists(),
        error=error, authorized=authorized, auth_url=auth_url,
    )


@setup_bp.route("/6/authorize")
def calendar_authorize():
    from pathlib import Path
    from google_auth_oauthlib.flow import Flow
    import html as html_mod

    creds_path = Path("/app/config/google_credentials.json")
    if not creds_path.exists():
        return redirect(url_for("setup.step6") + "?" + urlencode({"error": "Credentials not saved yet"}))

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    callback_url = request.url_root.rstrip("/") + "/setup/6/callback"
    logging.info("Calendar OAuth authorize — callback_url: %s", callback_url)
    flow = Flow.from_client_secrets_file(
        str(creds_path),
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        redirect_uri=callback_url,
    )
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    session["oauth_state"] = state
    session["oauth_redirect_uri"] = callback_url

    # Werkzeug's redirect() mangles external https:// URLs in newer versions,
    # causing the browser to request them as relative paths. Serve an HTML page
    # that navigates directly instead.
    safe_url = html_mod.escape(auth_url)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="1; url={safe_url}">
<title>Redirecting to Google…</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body class="bg-light">
<div class="container py-5" style="max-width:640px;">
<div class="card shadow-sm"><div class="card-body p-4 text-center">
<h5 class="mb-3">Redirecting to Google…</h5>
<p class="text-muted">If you are not redirected automatically:</p>
<a href="{safe_url}" class="btn btn-primary">Sign in with Google →</a>
</div></div></div>
</body></html>"""


@setup_bp.route("/6/callback")
def calendar_callback():
    from pathlib import Path
    from google_auth_oauthlib.flow import Flow

    creds_path = Path("/app/config/google_credentials.json")
    token_path = Path("/app/config/google_token.json")

    if not creds_path.exists():
        return redirect(url_for("setup.step6") + "?error=Credentials+not+found")

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    redirect_uri = session.get("oauth_redirect_uri") or (
        request.url_root.rstrip("/") + "/setup/6/callback"
    )
    logging.info("Calendar OAuth callback — redirect_uri: %s  request.url: %s",
                 redirect_uri, request.url)
    flow = Flow.from_client_secrets_file(
        str(creds_path),
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        redirect_uri=redirect_uri,
        state=session.get("oauth_state"),
    )

    try:
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        token_path.write_text(creds.to_json(), encoding="utf-8")

        from googleapiclient.discovery import build
        service = build("calendar", "v3", credentials=creds)
        cal_list = service.calendarList().list().execute()
        cal_ids = [c["id"] for c in cal_list.get("items", [])]

        cfg = load_config()
        cfg["calendar"]["enabled"] = True
        cfg["calendar"]["calendar_ids"] = cal_ids
        save_config(cfg)
    except Exception as exc:
        logging.error("Calendar OAuth callback error: %s", exc)
        return redirect(url_for("setup.step6") + "?" + urlencode({"error": str(exc)[:300]}))

    return redirect(url_for("setup.step6") + "?authorized=1")


@setup_bp.route("/7", methods=["GET", "POST"])
def step7():
    cfg = load_config()
    if request.method == "POST":
        for league in ["mlb", "nfl", "nba", "nhl", "wnba", "mls", "premier_league"]:
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


@setup_bp.route("/8/validate-feeds", methods=["POST"])
def validate_feeds():
    import feedparser
    data = request.get_json(silent=True) or {}
    urls = data.get("urls", [])
    results = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            feed = feedparser.parse(url)
            if getattr(feed, "bozo", False) and not getattr(feed, "entries", []):
                exc = getattr(feed, "bozo_exception", None)
                results.append({"url": url, "ok": False, "error": str(exc) if exc else "parse error"})
            else:
                feed_title = getattr(getattr(feed, "feed", None), "title", None) or url
                count = len(getattr(feed, "entries", []))
                results.append({"url": url, "ok": True, "title": feed_title, "count": count})
        except Exception as exc:
            results.append({"url": url, "ok": False, "error": str(exc)})
    return jsonify({"results": results})


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
