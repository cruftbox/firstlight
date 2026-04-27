import re
from flask import Blueprint, render_template, send_file, abort
from app.print.archive import list_all, ARCHIVE_DIR

archive_bp = Blueprint("archive", __name__)

_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.pdf$")


@archive_bp.route("/archive")
def index():
    files = list_all()
    return render_template("archive.html", files=files)


@archive_bp.route("/archive/<filename>")
def download(filename):
    if not _FILENAME_RE.match(filename):
        abort(404)
    path = ARCHIVE_DIR / filename
    if not path.exists():
        abort(404)
    return send_file(path, mimetype="application/pdf",
                     as_attachment=True, download_name=filename)
