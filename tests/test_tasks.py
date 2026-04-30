import pytest
from pathlib import Path


def _write(tmp_path, content):
    p = tmp_path / "tasks.txt"
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_returns_now_tasks(tmp_path):
    path = _write(tmp_path, "## Now\nMounts for back plexi\nFront Room UPS install\n\n## Soon\nDoor seals for Tesla\n")
    from app.providers.tasks import get_tasks
    assert get_tasks(path) == ["Mounts for back plexi", "Front Room UPS install"]


def test_ignores_blank_lines(tmp_path):
    path = _write(tmp_path, "## Now\n\nFirst task\n\nSecond task\n\n## Soon\nOther\n")
    from app.providers.tasks import get_tasks
    assert get_tasks(path) == ["First task", "Second task"]


def test_stops_at_next_section(tmp_path):
    path = _write(tmp_path, "## Now\nTask A\n## Later\nTask B\n")
    from app.providers.tasks import get_tasks
    result = get_tasks(path)
    assert result == ["Task A"]
    assert "Task B" not in result


def test_returns_empty_when_file_missing():
    from app.providers.tasks import get_tasks
    assert get_tasks("/nonexistent/path/tasks.txt") == []


def test_returns_empty_when_now_section_missing(tmp_path):
    path = _write(tmp_path, "## Soon\nDoor seals\n## Later\nTelescope\n")
    from app.providers.tasks import get_tasks
    assert get_tasks(path) == []


def test_returns_empty_when_now_section_empty(tmp_path):
    path = _write(tmp_path, "## Now\n\n## Soon\nSomething\n")
    from app.providers.tasks import get_tasks
    assert get_tasks(path) == []


def test_handles_now_at_end_of_file(tmp_path):
    path = _write(tmp_path, "## Soon\nOther\n## Now\nLast task\n")
    from app.providers.tasks import get_tasks
    assert get_tasks(path) == ["Last task"]


def test_strips_whitespace(tmp_path):
    path = _write(tmp_path, "## Now\n  spaced task  \n")
    from app.providers.tasks import get_tasks
    assert get_tasks(path) == ["spaced task"]
