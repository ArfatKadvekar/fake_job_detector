# JobGuard AI

## AI-Powered Fake Job & Internship Detector

JobGuard AI is a web-based application that analyzes job and internship descriptions to identify potentially fraudulent or suspicious opportunities.

The system combines **Machine Learning and NLP-based text analysis** with predefined red-flag detection to provide a classification, risk score, ML confidence, and detected warning signs.

## Features

* Fake/Real job classification
* Risk score and risk-level detection
* Machine Learning-based prediction
* NLP-based text analysis
* Detection of common scam indicators
* Red-flag identification
* Scan history using SQLite
* Dashboard with analysis statistics
* Simple web interface using Flask

## Technologies Used

* **Python**
* **Flask**
* **Scikit-learn**
* **NLTK / NLP techniques**
* **Joblib**
* **SQLite**
* **HTML5**
* **CSS3**
* **JavaScript**

## Project Structure

```text
fake_job_detector/
│
├── app.py
├── analyzer.py
├── train_model.py
├── dataset/
│   └── jobs.csv
│
├── model/
│   ├── model.pkl
│   └── vectorizer.pkl
│
├── templates/
│   ├── index.html
│   ├── history.html
│   └── dashboard.html
│
├── static/
│   └── style.css
│
├── database/
│   └── history.db
│
└── .gitignore
```

> The local SQLite database and Python cache files are excluded from version control through `.gitignore`.

## How It Works

1. The user enters or pastes a job/internship description.
2. The application processes the text.
3. The trained ML model predicts whether the opportunity is likely to be **REAL** or **FAKE**.
4. The system checks the description for suspicious indicators such as:

   * Payment or registration fee requests
   * Unrealistic salary claims
   * Suspicious communication channels
   * Requests for sensitive personal information
   * Urgency-based recruitment language
5. A risk score and risk level are generated.
6. The result is stored in the application's scan history.

## Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/chouglekhabira/fake_job_detector.git
cd fake_job_detector
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

### 3. Activate the virtual environment

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

Open the local Flask address shown in the terminal, usually:

```text
http://127.0.0.1:5000
```

## Model

The project uses a trained machine-learning model and text vectorizer stored in the `model/` directory.

* `model.pkl` — trained classification model
* `vectorizer.pkl` — text vectorizer used for processing job descriptions

## Disclaimer

JobGuard AI is an academic mini-project intended to demonstrate the use of machine learning and NLP for identifying potentially suspicious job and internship postings.

The prediction should not be considered a definitive determination that a job offer is fraudulent. Users should independently verify employers and job opportunities before sharing personal information or making payments.
