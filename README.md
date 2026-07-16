# PSAT - Phishing Simulation & Awareness Tool

## Setup Instructions

### 1. Clone the repository
git clone <repo_url>
cd PSAT

### 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt
pip install Flask-Mail
pip install flask-paginate

### 4. Setup environment variables
Copy `.env.example` to `.env` and update values.

### 5. Setup database
Run `database/schema.sql` in MySQL.

### 6. Run Flask application
flask run

Open: http://127.0.0.1:5000/