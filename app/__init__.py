import os
from flask import Flask, redirect, url_for, request


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "changeme")

    from app.routes.setup import setup_bp
    from app.routes.main import main_bp
    from app.routes.archive import archive_bp
    from app.routes.todo import todo_bp

    app.register_blueprint(setup_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(archive_bp)
    app.register_blueprint(todo_bp)

    @app.before_request
    def check_setup():
        from app.config import load as load_config
        if request.path.startswith("/setup") or request.path.startswith("/static"):
            return
        cfg = load_config()
        if not cfg["firstlight"]["setup_complete"]:
            return redirect(url_for("setup.step1"))

    from app.config import load as load_config
    cfg = load_config()
    if cfg["firstlight"]["setup_complete"]:
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app
