from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import pytz

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_digest(data: dict, config: dict) -> bytes:
    """Render digest data dict to PDF bytes via Jinja2 + WeasyPrint."""
    tz = pytz.timezone(config["firstlight"]["timezone"])
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
        sports=data.get("sports", []),
        news=data.get("news", []),
        todos=data.get("todos", []),
    )

    # base_url lets WeasyPrint resolve "static/css/digest.css" relative to app/
    base_url = str(TEMPLATES_DIR.parent) + "/"
    return HTML(string=html_str, base_url=base_url).write_pdf()
