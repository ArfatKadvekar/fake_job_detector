
from flask import Flask, render_template, request
from analyzer import predict_job
import sqlite3
from datetime import datetime
import os


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

DATABASE = "database/history.db"


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    database_folder = os.path.dirname(DATABASE)

    if database_folder:
        os.makedirs(
            database_folder,
            exist_ok=True
        )

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
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

    conn.commit()
    conn.close()


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

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
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
        datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        )
    ))

    conn.commit()
    conn.close()


# =========================================================
# GET HISTORY
# =========================================================

def get_history(
    search_text="",
    prediction_filter="ALL",
    risk_filter="ALL"
):

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    query = """
        SELECT *
        FROM scans
        WHERE 1 = 1
    """

    parameters = []


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search_text.strip():

        query += """
            AND LOWER(job_description) LIKE ?
        """

        parameters.append(
            "%" + search_text.strip().lower() + "%"
        )


    # -----------------------------------------------------
    # PREDICTION FILTER
    # -----------------------------------------------------

    if prediction_filter in [
        "REAL",
        "FAKE"
    ]:

        query += """
            AND UPPER(prediction) = ?
        """

        parameters.append(
            prediction_filter
        )


    # -----------------------------------------------------
    # RISK FILTER
    # -----------------------------------------------------

    if risk_filter in [
        "LOW RISK",
        "MEDIUM RISK",
        "HIGH RISK"
    ]:

        query += """
            AND UPPER(risk_level) = ?
        """

        parameters.append(
            risk_filter
        )


    # -----------------------------------------------------
    # ORDER
    # -----------------------------------------------------

    query += """
        ORDER BY id DESC
    """


    cursor.execute(
        query,
        parameters
    )

    scans = cursor.fetchall()

    conn.close()

    return scans


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

def get_dashboard_stats():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()


    # -----------------------------------------------------
    # TOTAL SCANS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM scans
    """)

    total_scans = cursor.fetchone()[0]


    # -----------------------------------------------------
    # FAKE JOBS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM scans
        WHERE UPPER(prediction) = 'FAKE'
    """)

    fake_jobs = cursor.fetchone()[0]


    # -----------------------------------------------------
    # REAL JOBS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM scans
        WHERE UPPER(prediction) = 'REAL'
    """)

    real_jobs = cursor.fetchone()[0]


    # -----------------------------------------------------
    # HIGH RISK
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM scans
        WHERE UPPER(risk_level) = 'HIGH RISK'
    """)

    high_risk = cursor.fetchone()[0]


    # -----------------------------------------------------
    # MEDIUM RISK
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM scans
        WHERE UPPER(risk_level) = 'MEDIUM RISK'
    """)

    medium_risk = cursor.fetchone()[0]


    # -----------------------------------------------------
    # LOW RISK
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM scans
        WHERE UPPER(risk_level) = 'LOW RISK'
    """)

    low_risk = cursor.fetchone()[0]


    # -----------------------------------------------------
    # AVERAGE RISK
    # -----------------------------------------------------

    cursor.execute("""
        SELECT AVG(risk_score)
        FROM scans
    """)

    average_risk = cursor.fetchone()[0]

    if average_risk is None:
        average_risk = 0


    # -----------------------------------------------------
    # AVERAGE ML CONFIDENCE
    # -----------------------------------------------------

    cursor.execute("""
        SELECT AVG(confidence)
        FROM scans
    """)

    average_confidence = cursor.fetchone()[0]

    if average_confidence is None:
        average_confidence = 0


    # -----------------------------------------------------
    # LATEST FIVE SCANS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT *
        FROM scans
        ORDER BY id DESC
        LIMIT 5
    """)

    latest_scans = cursor.fetchall()

    conn.close()


    return {
        "total_scans": total_scans,
        "fake_jobs": fake_jobs,
        "real_jobs": real_jobs,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "average_risk": round(
            average_risk,
            2
        ),
        "average_confidence": round(
            average_confidence,
            2
        ),
        "latest_scans": latest_scans
    }


# =========================================================
# HOME / JOB ANALYZER
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def home():

    result = None

    job_description = ""


    if request.method == "POST":

        job_description = request.form.get(
            "job_description",
            ""
        )


        if job_description.strip():

            (
                prediction,
                confidence,
                red_flags,
                risk_score,
                risk_level
            ) = predict_job(
                job_description
            )


            result = {

                "prediction": prediction,

                "confidence": round(
                    confidence,
                    2
                ),

                "red_flags": red_flags,

                "risk_score": risk_score,

                "risk_level": risk_level

            }


            # Save scan

            save_scan(

                job_description,

                prediction,

                round(
                    confidence,
                    2
                ),

                risk_score,

                risk_level

            )


    return render_template(

        "index.html",

        result=result,

        job_description=job_description

    )


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    search_text = request.args.get(
        "search",
        ""
    )


    prediction_filter = request.args.get(
        "prediction",
        "ALL"
    ).upper()


    risk_filter = request.args.get(
        "risk",
        "ALL"
    ).upper()


    # -----------------------------------------------------
    # VALIDATE PREDICTION FILTER
    # -----------------------------------------------------

    if prediction_filter not in [
        "ALL",
        "REAL",
        "FAKE"
    ]:

        prediction_filter = "ALL"


    # -----------------------------------------------------
    # VALIDATE RISK FILTER
    # -----------------------------------------------------

    if risk_filter not in [
        "ALL",
        "LOW RISK",
        "MEDIUM RISK",
        "HIGH RISK"
    ]:

        risk_filter = "ALL"


    scans = get_history(

        search_text,

        prediction_filter,

        risk_filter

    )


    return render_template(

        "history.html",

        scans=scans,

        search_text=search_text,

        prediction_filter=prediction_filter,

        risk_filter=risk_filter

    )


# =========================================================
# INDIVIDUAL SCAN DETAILS
# =========================================================

@app.route("/scan/<int:scan_id>")
def scan_details(scan_id):

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM scans
        WHERE id = ?
    """, (
        scan_id,
    ))


    scan = cursor.fetchone()

    conn.close()


    # -----------------------------------------------------
    # SCAN NOT FOUND
    # -----------------------------------------------------

    if scan is None:

        return render_template(

            "scan_details.html",

            scan=None,

            red_flags=[]

        ), 404


    # -----------------------------------------------------
    # GET RED FLAGS
    # -----------------------------------------------------
    #
    # Red flags are not currently stored separately
    # in the SQLite table.
    #
    # Therefore we run the analyzer again on the
    # stored job description to retrieve them.
    #

    try:

        (
            _prediction,
            _confidence,
            red_flags,
            _risk_score,
            _risk_level
        ) = predict_job(
            scan["job_description"]
        )

    except Exception:

        red_flags = []


    # -----------------------------------------------------
    # RENDER DETAILS PAGE
    # -----------------------------------------------------

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
# APPLICATION START
# =========================================================

if __name__ == "__main__":

    init_database()

    app.run(
        debug=True
    )
