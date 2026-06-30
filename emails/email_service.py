from flask_mail import Message
from flask import render_template
from extensions import mail
from datetime import datetime

def send_email(to, subject, template, **kwargs):
    kwargs["year"] = datetime.now().year
    kwargs["subject"] = subject

    html_body = render_template(template, **kwargs)

    msg = Message(subject=subject, recipients=[to])
    msg.html = html_body
    mail.send(msg)