from flask_mail import Message
from flask import render_template
from extensions import mail
from datetime import datetime, timedelta
import os

from emails.template_config import get_template, DEFAULT_TEMPLATE


def send_email(to, subject, template, **kwargs):
    kwargs["year"] = datetime.now().year
    kwargs["subject"] = subject

    html_body = render_template(template, **kwargs)

    msg = Message(subject=subject, recipients=[to])
    msg.html = html_body
    mail.send(msg)


def _build_plain_text(cfg, recipient_name, tracking_url, deadline):
    urgency = cfg["plain_urgency"].format(deadline=deadline)
    return (
        f"Hello {recipient_name},\n\n"
        f"{cfg['plain_intro']}\n\n"
        f"{urgency}\n\n"
        f"{cfg['cta_text']}: {tracking_url}\n\n"
        f"Thank you,\n{cfg['sender_name']}\n\n"
        f"---\n"
        f"This is an automated message from {cfg['org_name']}. Please do not reply to this email.\n"
    )


def send_campaign_email(target_email, user_id, template_key=DEFAULT_TEMPLATE, recipient_name="User"):
    """
    Sends a template-specific simulation email for authorized awareness testing.
    """
    cfg = get_template(template_key)
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:5000")
    tracking_url = f"{base_url}/track/click/{user_id}"

    subject = os.getenv(f"SIMULATION_SUBJECT_{template_key.upper()}", cfg["subject"])
    deadline = (datetime.now() + timedelta(hours=24)).strftime("%B %d, %Y at %I:%M %p")

    context = {
        "subject": subject,
        "recipient_name": recipient_name,
        "tracking_url": tracking_url,
        "org_name": cfg["org_name"],
        "sender_name": cfg["sender_name"],
        "cta_text": cfg["cta_text"],
        "accent_color": cfg["accent_color"],
        "deadline": deadline,
        "year": datetime.now().year,
    }

    html_body = render_template(cfg["email_template"], **context)
    plain_body = _build_plain_text(cfg, recipient_name, tracking_url, deadline)
    sender = os.getenv("SMTP_SENDER") or os.getenv("SMTP_USER")

    try:
        msg = Message(
            subject=subject,
            recipients=[target_email],
            sender=sender,
            body=plain_body,
            html=html_body,
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending campaign email: {str(e)}")
        return False


def send_simulation_email(target_email, user_id, recipient_name="User", template_key=DEFAULT_TEMPLATE):
    """Backward-compatible wrapper used by the quick-launch action on the email list."""
    return send_campaign_email(target_email, user_id, template_key, recipient_name)
