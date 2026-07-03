from flask import Blueprint, render_template, request, redirect, url_for
from database.db import get_connection

track_bp = Blueprint('track', __name__)

@track_bp.route('/track/click/<int:user_id>', methods=['GET'])
def track_click(user_id):
    """
    Intercepts the link click, records user agent, IP address, and timestamp 
    into the click_logs table, then shows the educational landing mockup.
    """
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Get the campaign_id associated with this user's email log
        cursor.execute(
            "SELECT campaign_id FROM email_logs WHERE user_id = %s ORDER BY sent_time DESC LIMIT 1",
            (user_id,)
        )
        log_entry = cursor.fetchone()
        campaign_id = log_entry[0] if log_entry else 1

        # 2. Log the click event to your click_logs table matching schema.sql
        query = """
            INSERT INTO click_logs (campaign_id, user_id, click_time, ip_address, user_agent)
            VALUES (%s, %s, NOW(), %s, %s)
        """
        cursor.execute(query, (campaign_id, user_id, ip_address, user_agent))
        conn.commit()
        
        cursor.close()
        conn.close()
        print(f"[TRACKER] Successfully registered click event for User ID: {user_id}")

    except Exception as e:
        print(f"[TRACKER ERROR] Failed to record click metrics: {str(e)}")
        if conn:
            conn.close()

    # Render your mock login page form
    return render_template('phish_landing.html', user_id=user_id)


@track_bp.route('/track/login-attempt/<int:user_id>', methods=['POST'])
def track_login_attempt(user_id):
    """
    Records a mock login attempt event in the database for metric tracking,
    then redirects cleanly to our dedicated public training path.
    """
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')

    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Fetch the relevant campaign ID linked to this user's logs
        cursor.execute(
            "SELECT campaign_id FROM email_logs WHERE user_id = %s ORDER BY sent_time DESC LIMIT 1",
            (user_id,)
        )
        log_entry = cursor.fetchone()
        campaign_id = log_entry[0] if log_entry else 1

        # 2. Log the details to the login_attempts table (matching schema.sql)
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

    # 3. Cleanly redirect the browser to the public training view
    return redirect(url_for('track.education_page'))


@track_bp.route('/awareness_education', methods=['GET'])
def education_page():
    """
    Publicly handles loading and displaying the educational security awareness screen.
    """
    return render_template('awareness_education.html')