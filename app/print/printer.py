import subprocess
import tempfile
import os
import logging


def get_printers() -> list:
    """Returns list of CUPS printer names. Returns [] if CUPS is unavailable."""
    try:
        result = subprocess.run(
            ["lpstat", "-p"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        printers = []
        for line in result.stdout.splitlines():
            if line.startswith("printer "):
                parts = line.split()
                if len(parts) >= 2:
                    printers.append(parts[1])
        return printers
    except Exception:
        return []


def print_pdf(pdf_bytes: bytes, printer_name: str) -> bool:
    """Print PDF bytes to named CUPS printer via lpr. Returns True on success."""
    if not printer_name:
        return False

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            tmp_path = f.name

        result = subprocess.run(
            ["lpr", "-P", printer_name, tmp_path],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            logging.error("lpr failed: %s", result.stderr.decode())
            return False
        return True
    except Exception as e:
        logging.error("Print failed: %s", e)
        return False
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
