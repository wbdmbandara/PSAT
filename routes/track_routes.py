from flask import Blueprint, render_template, request, redirect, url_for
from database.db import get_connection
from emails.template_config import get_template, DEFAULT_TEMPLATE

track_bp = Blueprint('track', __name__)


def _get_campaign_context(user_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT el.campaign_id, c.template_name
            FROM email_logs el
            JOIN campaigns c ON el.campaign_id = c.id
            WHERE el.user_id = %s
            ORDER BY el.sent_time DESC
            LIMIT 1
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row[0], row[1] or DEFAULT_TEMPLATE
        return 1, DEFAULT_TEMPLATE
    except Exception as e:
        print(f"[TRACKER ERROR] Failed to fetch campaign context: {e}")
        if conn:
            conn.close()
        return 1, DEFAULT_TEMPLATE


@track_bp.route('/track/click/<int:user_id>', methods=['GET'])
def track_click(user_id):
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')

    campaign_id, template_key = _get_campaign_context(user_id)
    landing_template = get_template(template_key)["landing_template"]

    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO click_logs (campaign_id, user_id, click_time, ip_address, user_agent)
            VALUES (%s, %s, NOW(), %s, %s)
        """
        cursor.execute(query, (campaign_id, user_id, ip_address, user_agent))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[TRACKER] Click registered for User ID: {user_id} (template: {template_key})")
    except Exception as e:
        print(f"[TRACKER ERROR] Failed to record click metrics: {str(e)}")
        if conn:
            conn.close()

    return render_template(landing_template, user_id=user_id)


@track_bp.route('/track/login-attempt/<int:user_id>', methods=['POST'])
def track_login_attempt(user_id):
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')

    campaign_id, _ = _get_campaign_context(user_id)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO login_attempts (campaign_id, user_id, attempt_time, ip_address, user_agent)
            VALUES (%s, %s, NOW(), %s, %s)
        """
        cursor.execute(query, (campaign_id, user_id, ip_address, user_agent))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[TRACKER] Logged simulation login interaction for User ID: {user_id}")
    except Exception as e:
        print(f"[TRACKER ERROR] Failed to record login attempt metrics: {str(e)}")
        if conn:
            conn.close()

    return redirect(url_for('track.education_page'))


@track_bp.route('/awareness_education', methods=['GET'])
def education_page():
    return render_template('awareness_education.html')
