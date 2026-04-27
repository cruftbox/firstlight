import smtplib
import logging
from email.message import EmailMessage
from datetime import date


def send(pdf_bytes: bytes, today: date, email_config: dict) -> bool:
    """Send digest PDF as email attachment. Returns True on success, False on any failure."""
    date_str = today.strftime("%A, %B %d, %Y").replace(" 0", " ")
    filename = f"firstlight-{today.isoformat()}.pdf"

    msg = EmailMessage()
    msg["Subject"] = f"Firstlight — {date_str}"
    msg["From"] = email_config["from_address"]
    msg["To"] = email_config["to_address"]
    msg.set_content("Your daily Firstlight digest is attached.")
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )

    host = email_config["smtp_host"]
    port = email_config["smtp_port"]
    user = email_config.get("smtp_user", "")
    password = email_config.get("smtp_password", "")

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port) as smtp:
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as smtp:
                smtp.starttls()
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        return True
    except Exception as e:
        logging.error("Email send failed: %s", e)
        return False
