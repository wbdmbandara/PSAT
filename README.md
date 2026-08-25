# PSAT - Phishing Simulation & Awareness Tool

PSAT is a Flask-based phishing awareness and simulation platform designed for security awareness training. It allows administrators to register, manage target email addresses, launch realistic phishing simulations, and track how users react through email opens, link clicks, and credential-entry attempts.

The application is intended for authorized security awareness testing and educational purposes only.

## Overview

The system includes:

-   Admin authentication and session-based access
-   Email list management with add, edit, delete, and CSV import support
-   Campaign creation and simulation dispatch
-   Realistic phishing email templates for common scenarios such as:
    -   Corporate account access
    -   Social media security alerts
    -   Banking verification prompts
    -   University portal password resets
-   Tracking for:
    -   Email dispatch logs
    -   Link clicks
    -   Login/credential submission attempts
-   Dashboard summaries and report pages for monitoring results
-   SMTP-based email delivery with template-driven content

## Tech Stack

-   Python 3
-   Flask
-   MySQL
-   Flask-Mail
-   python-dotenv
-   Flask-Paginate
-   HTML, CSS, JavaScript, Bootstrap

## Project Structure

```text
PSAT/
├── app.py                 # Flask app entry point
├── config.py              # Mail configuration from environment variables
├── extensions.py          # Flask-Mail extension initialization
├── requirements.txt       # Python dependencies
├── Procfile               # Heroku/Railway process config
├── .env.example           # Sample environment file
├── README.md
├── database/
│   ├── db.py              # MySQL connection pool and schema migration helpers
│   └── schema.sql         # Database schema setup
├── emails/
│   ├── email_service.py   # Sends simulation emails
│   ├── template_config.py # Template definitions and landing pages
│   └── templates/...      # Email HTML templates
├── routes/
│   ├── admin_routes.py    # Admin dashboard, campaigns, reports, login flow
│   └── track_routes.py    # Click/login tracking endpoints
├── static/
├── templates/
│   ├── landing/           # Fake login pages for simulated phishing traps
│   ├── emails/            # Email templates
│   ├── partials/          # Shared layout fragments
│   └── *.html             # Main app pages
└── .env                   # Local environment (not committed)
```

## Features

### Admin Dashboard

Administrators can:

-   register and log in
-   view metrics such as total emails sent, click rate, and compromise rate
-   see recent activity and campaign trends
-   navigate to reports and campaign creation tools

### Target Management

The app supports managing a list of target users:

-   add individual recipients
-   edit or delete entries
-   import users from CSV files
-   download a sample CSV template

### Simulated Campaigns

Campaigns can be created with one or more targets and a selected template. Each campaign can simulate phishing messages themed around realistic business or user scenarios.

### Tracking and Reporting

The app logs:

-   email dispatch records
-   click events with IP address and user-agent information
-   login attempt submissions

Reports can be filtered by email, date range, and status for:

-   Email dispatches
-   Click activity
-   Login attempts
-   Campaign overview

## Environment Configuration

Create a `.env` file based on `.env.example` and fill in your own values.

Example:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=psat_db
DB_PORT=3307

SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USE_TLS=false
SMTP_USE_SSL=true
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_SENDER=IT Security <your_email@gmail.com>

BASE_URL=http://127.0.0.1:5000
SECRET_KEY=your_secret_key
```

### Important notes

-   `DB_*` values configure the MySQL database connection.
-   `SMTP_*` values configure the email sending account used for campaign emails.
-   `BASE_URL` should be the public URL of your app so simulated links point to the correct site.
-   `SECRET_KEY` should be a strong secret value in production.

## Database Setup

This project uses MySQL.

1. Create a MySQL database.
2. Configure the environment variables in `.env`.
3. Run the schema script:

```bash
mysql -u your_user -p your_database < database/schema.sql
```

The app also includes schema migration checks in `database/db.py` to add newer columns automatically if the database is missing them.

## Installation

### 1. Clone the repository

```bash
git clone <repository_url>
cd PSAT
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

### Local development

```bash
python app.py
```

or

```bash
flask run
```

Then open:

```text
http://127.0.0.1:5000/
```

## User Flow

1. Register an admin account.
2. Log in to the dashboard.
3. Add or import target recipients.
4. Create a campaign and choose a phishing template.
5. Send the simulation emails.
6. Track recipient clicks and submitted credentials.
7. Review reports and dashboard metrics for awareness outcomes.

## Security and Compliance Notice

This project is intended for ethical, authorized phishing awareness exercises. It should only be used in environments where the organization has explicit permission to conduct simulated phishing tests and training.

Do not deploy this tool for malicious or unauthorized phishing activity.

## License

This project is provided for educational and internal training use. Please review the repository license if one is added by the project owner.

## Contributing

Contributions are welcome. If you improve templates, fix tracking logic, or add functionality, open a pull request with a clear description of the change.

## Support

For local setup help, review the environment variables in `.env.example` and confirm that MySQL and SMTP credentials are configured correctly before running the app.
