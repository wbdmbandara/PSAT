from flask_mail import Message
from flask import render_template
from extensions import mail
from datetime import datetime
import os

def send_email(to, subject, template, **kwargs):
    kwargs["year"] = datetime.now().year
    kwargs["subject"] = subject

    html_body = render_template(template, **kwargs)

    msg = Message(subject=subject, recipients=[to])
    msg.html = html_body
    mail.send(msg)


def send_simulation_email(target_email, user_id):
    """
    Sends an authorized educational simulation email containing a link back to the local tracker.
    """
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:5000")
    
    # Build the tracking link pointing straight to the target user's database record ID
    tracking_url = f"{base_url}/track/click/{user_id}"
    
    subject = "Simulated Security Awareness Test"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h3 style="color: #d9534f;">Security Verification Required</h3>
        <p>This is an automated simulation test to evaluate internal security awareness protocols.</p>
        <p>To confirm your workstation compliance configuration, please review your portal credentials:</p>
        <p style="margin: 20px 0;">
            <a href="{tracking_url}" style="background-color: #0275d8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Verify Account Configuration Here
            </a>
        </p>
        <br>
        <hr style="border: 0; border-top: 1px solid #ccc;">
        <p style="font-size: 11px; color: #777;">
            <strong>Notice:</strong> This message is part of an authorized internal cybersecurity awareness campaign.
        </p>
      </body>
    </html>
    """
    
    try:
        msg = Message(subject=subject, recipients=[target_email])
        msg.html = html_content
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending simulation email: {str(e)}")
        return False