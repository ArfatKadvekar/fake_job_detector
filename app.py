
from flask import Flask, render_template, request
from analyzer import predict_job
import sqlite3
from datetime import datetime
import os
import logging


# =========================================================
# FLASK APP CONFIGURATION
# =========================================================

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE = os.path.join(DATABASE_DIR, "history.db")


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():
    """Create the database directory and scans table if needed."""

    os.makedirs(DATABASE_DIR, exist_ok=True)

    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_description TEXT NOT NULL,
                prediction TEXT NOT NULL,
                confidence REAL NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                scan_time TEXT NOT NULL
            )
        """)


# IMPORTANT:
# Gunicorn imports this module instead of running it as __main__.
# Therefore, initialize the database during module import.
init_database()


# =========================================================
# SAVE SCAN
# =========================================================

def save_scan(
    job_description,
    prediction,
    confidence,
    risk_score,
    risk_level
):
    """Save an analyzed job description and its results."""

    scan_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            INSERT INTO scans (
                job_description,
                prediction,
                confidence,
                risk_score,
                risk_level,
                scan_time
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job_description,
            prediction,
            confidence,
            risk_score,
            risk_level,
            scan_time
        ))


# =========================================================
# GET HISTORY
# =========================================================

def get_history(
    search="",
    prediction_filter="",
    risk_filter=""
):
    """Retrieve scan history with optional filters."""

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        query = """
            SELECT *
            FROM scans
            WHERE 1=1
        """

        params = []

        # Search job descriptions
        if search:
            query += " AND job_description LIKE ?"
            params.append("%" + search + "%")

        # Filter by prediction
        if prediction_filter:
            query += " AND UPPER(prediction) = UPPER(?)"
            params.append(prediction_filter)

        # Filter by risk level
        if risk_filter:
            query += " AND UPPER(risk_level) = UPPER(?)"
            params.append(risk_filter)

        query += " ORDER BY id DESC"

        cursor = conn.execute(query, params)
        history = cursor.fetchall()

    return history


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

def get_dashboard_stats():
    """Calculate statistics and retrieve the latest five scans."""

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # Total scans
        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
        """)
        total_scans = cursor.fetchone()[0]

        # Fake jobs
        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
            WHERE UPPER(prediction) = 'FAKE'
        """)
        fake_jobs = cursor.fetchone()[0]

        # Real jobs
        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
            WHERE UPPER(prediction) = 'REAL'
        """)
        real_jobs = cursor.fetchone()[0]

        # High-risk jobs
        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
            WHERE UPPER(risk_level) = 'HIGH RISK'
        """)
        high_risk = cursor.fetchone()[0]

        # Medium-risk jobs
        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
            WHERE UPPER(risk_level) = 'MEDIUM RISK'
        """)
        medium_risk = cursor.fetchone()[0]

        # Low-risk jobs
        cursor.execute("""
            SELECT COUNT(*)
            FROM scans
            WHERE UPPER(risk_level) = 'LOW RISK'
        """)
        low_risk = cursor.fetchone()[0]

        # Average risk score
        cursor.execute("""
            SELECT AVG(risk_score)
            FROM scans
        """)
        average_risk = cursor.fetchone()[0]

        if average_risk is None:
            average_risk = 0

        # Average ML confidence
        cursor.execute("""
            SELECT AVG(confidence)
            FROM scans
        """)
        average_confidence = cursor.fetchone()[0]

        if average_confidence is None:
            average_confidence = 0

        # Latest five scans
        cursor.execute("""
            SELECT *
            FROM scans
            ORDER BY id DESC
            LIMIT 5
        """)
        latest_scans = cursor.fetchall()

    return {
        "total_scans": total_scans,
        "fake_jobs": fake_jobs,
        "real_jobs": real_jobs,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "average_risk": round(average_risk, 2),
        "average_confidence": round(average_confidence, 2),
        "latest_scans": latest_scans
    }


# =========================================================
# HOME / JOB ANALYZER
# =========================================================

@app.route("/", methods=["GET", "POST"])
def home():

    result = None

    if request.method == "POST":

        job_description = request.form.get(
            "job_description",
            ""
        ).strip()

        # Empty input check
        if not job_description:
            result = {
                "error": "Please enter a job description."
            }

            return render_template(
                "index.html",
                result=result
            )

        try:
            # Analyze job description using the ML model
            analysis = predict_job(job_description)

            prediction = analysis.get(
                "prediction",
                "UNKNOWN"
            )

            confidence = analysis.get(
                "confidence",
                0
            )

            risk_score = analysis.get(
                "risk_score",
                0
            )

            risk_level = analysis.get(
                "risk_level",
                "LOW RISK"
            )

            red_flags = analysis.get(
                "red_flags",
                []
            )

            # Save result in SQLite
            save_scan(
                job_description,
                prediction,
                confidence,
                risk_score,
                risk_level
            )

            # Prepare result for index.html
            result = {
                "prediction": prediction,
                "confidence": confidence,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "red_flags": red_flags
            }

        except Exception:
            # Keep the full traceback in Render runtime logs
            logging.exception("Job analysis or scan saving failed")

            result = {
                "error": (
                    "Unable to analyze this job description. "
                    "Please check the server logs and try again."
                )
            }

    return render_template(
        "index.html",
        result=result
    )


# =========================================================
# HISTORY PAGE
# =========================================================

@app.route("/history")
def history():

    search = request.args.get("search", "").strip()
    prediction_filter = request.args.get("prediction", "").strip()
    risk_filter = request.args.get("risk", "").strip()

    scans = get_history(
        search=search,
        prediction_filter=prediction_filter,
        risk_filter=risk_filter
    )

    return render_template(
        "history.html",
        scans=scans,
        search=search,
        prediction_filter=prediction_filter,
        risk_filter=risk_filter
    )


# =========================================================
# SCAN DETAILS
# =========================================================

@app.route("/scan/<int:scan_id>")
def scan_details(scan_id):

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row

        scan = conn.execute("""
            SELECT *
            FROM scans
            WHERE id = ?
        """, (scan_id,)).fetchone()

    # Scan not found
    if scan is None:
        return "Scan not found", 404

    # Re-analyze the stored description to retrieve red flags
    try:
        analysis = predict_job(scan["job_description"])

        red_flags = analysis.get(
            "red_flags",
            []
        )

    except Exception:
        logging.exception(
            "Could not retrieve red flags for scan %s",
            scan_id
        )
        red_flags = []

    return render_template(
        "scan_details.html",
        scan=scan,
        red_flags=red_flags
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    stats = get_dashboard_stats()

    return render_template(
        "dashboard.html",
        stats=stats
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    # The database is already initialized above.
    # Debug mode is for local development only.
    app.run(debug=True)
