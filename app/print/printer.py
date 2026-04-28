import subprocess
import tempfile
import os
import logging

CUPS_PRINTER_NAME = "Firstlight"


def get_printers() -> list:
    """Returns list of CUPS printer names. Returns [] if CUPS is unavailable."""
    try:
        result = subprocess.run(
            ["lpstat", "-p"],
            capture_output=True, text=True, timeout=5,
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


def setup_network_printer(printer_ip: str) -> bool:
    """Register a network IPP printer with the local CUPS instance."""
    if not printer_ip:
        return False
    try:
        subprocess.run(
            ["lpadmin", "-p", CUPS_PRINTER_NAME, "-E",
             "-v", f"ipp://{printer_ip}/ipp/print",
             "-m", "everywhere"],
            capture_output=True, timeout=20, check=True,
        )
        subprocess.run(
            ["lpadmin", "-d", CUPS_PRINTER_NAME],
            capture_output=True, timeout=5,
        )
        logging.info("Registered printer %s at %s", CUPS_PRINTER_NAME, printer_ip)
        return True
    except Exception as e:
        logging.error("Failed to register printer: %s", e)
        return False


def print_pdf(pdf_bytes: bytes, printer_name: str, printer_ip: str = "") -> bool:
    """Print PDF bytes via lpr. Registers the printer first if printer_ip given."""
    if not printer_name:
        return False

    if printer_ip and CUPS_PRINTER_NAME not in get_printers():
        setup_network_printer(printer_ip)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            tmp_path = f.name

        result = subprocess.run(
            ["lpr", "-P", printer_name, tmp_path],
            capture_output=True, timeout=30,
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
