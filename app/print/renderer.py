import logging
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import pytz

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_digest(data: dict, config: dict) -> bytes:
    """Render digest data dict to PDF bytes via Jinja2 + WeasyPrint."""
    try:
        tz = pytz.timezone(config["firstlight"]["timezone"])
    except Exception:
        logging.warning("Unknown timezone %r, falling back to UTC", config["firstlight"]["timezone"])
        tz = pytz.utc
    now = datetime.now(tz)
    date_str = now.strftime("%A, %B %d, %Y").replace(" 0", " ")

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("digest.html")
    html_str = template.render(
        date_str=date_str,
        config=config,
        weather=data.get("weather"),
        quote=data.get("quote"),
        calendar=data.get("calendar", []),
        calendar_tomorrow=data.get("calendar_tomorrow", []),
        sports=data.get("sports", []),
        news=data.get("news", []),
        todos=data.get("todos", []),
        history=data.get("history", []),
        world_cup=data.get("world_cup", []),
        errors=data.get("errors", []),
    )

    # base_url lets WeasyPrint resolve "static/css/digest.css" relative to app/
    base_url = str(TEMPLATES_DIR.parent) + "/"
    return HTML(string=html_str, base_url=base_url).write_pdf()
