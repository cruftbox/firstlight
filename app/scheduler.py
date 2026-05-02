import logging
import threading
from datetime import date, datetime
from pathlib import Path

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(daemon=True)

_LAST_PRINTED = Path("/app/config/last_printed.txt")


def start_scheduler(app) -> None:
    from app.config import load as load_config
    cfg = load_config()
    print_time = cfg["firstlight"]["print_time"]
    timezone = cfg["firstlight"]["timezone"]
    _add_job(print_time, timezone)
    if not scheduler.running:
        scheduler.start()
    job = scheduler.get_job("daily_digest")
    logger.info("Scheduler started; next run: %s", job.next_run_time if job else "unknown")
    _check_missed_print(print_time, timezone)


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
        misfire_grace_time=4 * 3600,
    )
    logger.info("Scheduled daily digest for %s:%s %s", hour, minute, timezone)


def _check_missed_print(print_time: str, timezone: str) -> None:
    """On startup, run the pipeline immediately if past print time and today's digest is missing."""
    today = date.today()
    try:
        last = date.fromisoformat(_LAST_PRINTED.read_text().strip())
        if last >= today:
            logger.info("Digest already ran today (%s), no catch-up needed", today)
            return
    except (FileNotFoundError, ValueError):
        pass

    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    hour, minute = (int(x) for x in print_time.split(":"))
    scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if now >= scheduled:
        logger.info(
            "Startup at %s is past print time %s with no digest for %s — running catch-up",
            now.strftime("%H:%M"), print_time, today,
        )
        threading.Thread(target=_run_pipeline, daemon=True, name="catch-up").start()
    else:
        logger.info(
            "Startup at %s is before print time %s, catch-up not needed",
            now.strftime("%H:%M"), print_time,
        )


def _run_pipeline() -> None:
    from app.print.pipeline import run_pipeline
    logger.info("Running digest pipeline")
    try:
        run_pipeline()
        logger.info("Digest pipeline completed successfully")
        _LAST_PRINTED.parent.mkdir(parents=True, exist_ok=True)
        _LAST_PRINTED.write_text(date.today().isoformat())
    except Exception as e:
        logger.error("Pipeline error: %s", e, exc_info=True)
