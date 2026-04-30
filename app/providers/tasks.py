import logging
from pathlib import Path


def get_tasks(file_path: str = "/tasks/tasks.txt") -> list:
    path = Path(file_path)
    if not path.exists():
        logging.warning("Task file not found: %s", path)
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        logging.warning("Could not read task file: %s", e)
        return []

    in_now = False
    tasks = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("##"):
            section = stripped.lstrip("#").strip().lower()
            if section == "now":
                in_now = True
            elif in_now:
                break
            continue
        if in_now and stripped:
            tasks.append(stripped)
    return tasks
