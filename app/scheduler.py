import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler(daemon=True)


def start_scheduler(app) -> None:
    from app.config import load as load_config
    cfg = load_config()
    _add_job(cfg["firstlight"]["print_time"], cfg["firstlight"]["timezone"])
    if not scheduler.running:
        scheduler.start()


def reschedule(print_time: str, timezone: str) -> None:
    _add_job(print_time, timezone)
    if not scheduler.running:
        scheduler.start()


def _add_job(print_time: str, timezone: str) -> None:
    hour, minute = print_time.split(":")
    scheduler.add_job(
        func=_run_pipeline,
        trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=timezone),
        id="daily_digest",
        replace_existing=True,
    )


def _run_pipeline() -> None:
    from app.print.pipeline import run_pipeline
    try:
        run_pipeline()
    except Exception as e:
        logging.error("Scheduled pipeline error: %s", e)
