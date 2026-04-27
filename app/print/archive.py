from pathlib import Path
from datetime import date, timedelta
import logging

ARCHIVE_DIR = Path("/app/config/archive")


def save(pdf_bytes: bytes, today: date) -> None:
    archive_dir = ARCHIVE_DIR
    archive_dir.mkdir(parents=True, exist_ok=True)
    path = archive_dir / f"{today.isoformat()}.pdf"
    try:
        path.write_bytes(pdf_bytes)
    except OSError as e:
        logging.error("Archive save failed: %s", e)


def cleanup(retention_days: int) -> None:
    archive_dir = ARCHIVE_DIR
    if not archive_dir.exists():
        return
    cutoff = date.today() - timedelta(days=retention_days)
    for pdf_file in archive_dir.glob("*.pdf"):
        try:
            file_date = date.fromisoformat(pdf_file.stem)
            if file_date < cutoff:
                pdf_file.unlink()
        except (ValueError, OSError) as e:
            logging.error("Archive cleanup error for %s: %s", pdf_file, e)


def list_all() -> list:
    archive_dir = ARCHIVE_DIR
    if not archive_dir.exists():
        return []
    files = []
    for pdf_file in sorted(archive_dir.glob("*.pdf"), reverse=True):
        try:
            file_date = date.fromisoformat(pdf_file.stem)
            size_kb = round(pdf_file.stat().st_size / 1024, 1)
            files.append({
                "date": file_date.strftime("%A, %B %d, %Y").replace(" 0", " "),
                "filename": pdf_file.name,
                "size_kb": size_kb,
            })
        except (ValueError, OSError):
            continue
    return files
