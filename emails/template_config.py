"""
Fictional phishing simulation templates for authorized security awareness training.
Each template pairs an email with a matching login landing page.
"""

TEMPLATE_CONFIG = {
    "corporate": {
        "label": "Corporate Email Login",
        "email_template": "emails/corporate_email.html",
        "landing_template": "landing/corporate_login.html",
        "subject": "Action Required: Sign in to your Liquid account",
        "org_name": "liquid now",
        "sender_name": "Liquid Support",
        "cta_text": "Login to Continue",
        "accent_color": "#1da1f2",
        "plain_intro": (
            "Your corporate Liquid account session has expired. Please sign in again "
            "to restore access to your workspace and shared resources."
        ),
        "plain_urgency": (
            "Complete sign-in before {deadline} to avoid temporary account suspension."
        ),
    },
    "social_media": {
        "label": "Social Media Login",
        "email_template": "emails/social_media_email.html",
        "landing_template": "landing/social_media_login.html",
        "subject": "Unusual activity on your Pinterest account",
        "org_name": "Pinterest",
        "sender_name": "Pinterest Security",
        "cta_text": "Review Activity",
        "accent_color": "#e60023",
        "plain_intro": (
            "We noticed a sign-in attempt on your Pinterest account from a new device "
            "and location. If this wasn't you, please secure your account immediately."
        ),
        "plain_urgency": (
            "Please review this activity before {deadline} to prevent unauthorized access."
        ),
    },
    "banking": {
        "label": "Banking Portal",
        "email_template": "emails/banking_email.html",
        "landing_template": "landing/banking_login.html",
        "subject": "Sampath Vishwa: Verify your online banking access",
        "org_name": "Sampath Bank",
        "sender_name": "Sampath Vishwa Security",
        "cta_text": "Sign In to Vishwa",
        "accent_color": "#f47920",
        "plain_intro": (
            "As part of our routine security review, we need you to sign in to Sampath Vishwa "
            "and confirm your profile to continue accessing your accounts."
        ),
        "plain_urgency": (
            "Complete verification before {deadline} to avoid temporary restrictions on your account."
        ),
    },
    "university": {
        "label": "University Portal",
        "email_template": "emails/university_email.html",
        "landing_template": "landing/university_login.html",
        "subject": "Student portal: Password reset required",
        "org_name": "Student Portal",
        "sender_name": "University IT Support",
        "cta_text": "Login to Portal",
        "accent_color": "#7c3aed",
        "plain_intro": (
            "Your student portal password is scheduled to expire. To maintain access to "
            "course materials, grades, and registration services, you must sign in and update your credentials."
        ),
        "plain_urgency": (
            "Please sign in before {deadline} to avoid losing portal access."
        ),
    },
}

DEFAULT_TEMPLATE = "corporate"


def get_template(template_key):
    return TEMPLATE_CONFIG.get(template_key, TEMPLATE_CONFIG[DEFAULT_TEMPLATE])


def get_template_choices():
    return [(key, cfg["label"]) for key, cfg in TEMPLATE_CONFIG.items()]
