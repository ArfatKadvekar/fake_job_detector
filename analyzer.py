import joblib
import re


# ============================================================
# LOAD TRAINED ML MODEL AND VECTORIZER
# ============================================================

model = joblib.load("model/model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")


# ============================================================
# RED FLAG CATEGORIES AND SUSPICIOUS KEYWORDS
# ============================================================

RED_FLAGS = {

    "Payment Request": [
        "registration fee",
        "joining fee",
        "processing fee",
        "security deposit",
        "activation fee",
        "pay rs",
        "payment required",
        "pay a fee"
    ],

    "Unrealistic Salary": [
        "earn 50000",
        "earn 60000",
        "earn 80000",
        "earn 1 lakh",
        "rs 50000",
        "rs 60000",
        "rs 80000",
        "rs. 50000",
        "rs. 60000",
        "rs. 80000",
        "inr 50000",
        "inr 60000",
        "inr 80000",
        "₹50000",
        "₹60000",
        "₹80000",
        "₹50,000",
        "₹60,000",
        "₹80,000",
        "rs 50,000",
        "rs 60,000",
        "rs 80,000",
        "inr 50,000",
        "inr 60,000",
        "inr 80,000"
    ],

    "Suspicious Contact": [
        "whatsapp",
        "telegram",
        "upi id"
    ],

    "Personal Information": [
        "otp",
        "bank account",
        "bank details",
        "aadhaar",
        "password"
    ],

    "Urgency": [
        "urgent hiring",
        "limited seats",
        "within 2 hours",
        "immediately",
        "today",
        "act now"
    ]
}


# ============================================================
# DETECT RED FLAGS
# ============================================================

def detect_red_flags(text):

    text = text.lower()

    detected_flags = []


    # --------------------------------------------------------
    # NEGATION WORDS
    # Used to prevent false positives such as:
    #
    # "No registration fee"
    # "No application fee"
    # "We do not charge any fee"
    # "There is no payment required"
    # --------------------------------------------------------

    NEGATION_WORDS = [
        "no",
        "not",
        "without",
        "never",
        "don't",
        "do not",
        "doesn't",
        "does not",
        "isn't",
        "is not",
        "aren't",
        "are not",
        "free of",
        "zero"
    ]


    # --------------------------------------------------------
    # KEYWORD DETECTION
    # --------------------------------------------------------

    for category, keywords in RED_FLAGS.items():

        for keyword in keywords:

            position = text.find(keyword)

            if position == -1:
                continue


            # ------------------------------------------------
            # CHECK THE TEXT BEFORE THE KEYWORD
            # ------------------------------------------------

            start = max(0, position - 60)

            context_before = text[start:position]


            is_negated = False


            for negation in NEGATION_WORDS:

                if negation in context_before:

                    is_negated = True

                    break


            # ------------------------------------------------
            # IGNORE NEGATED SUSPICIOUS KEYWORDS
            # ------------------------------------------------

            if is_negated:

                continue


            # ------------------------------------------------
            # ADD RED FLAG
            # ------------------------------------------------

            detected_flags.append(
                (category, keyword)
            )


            # Count each category only once
            break


    # ========================================================
    # ADDITIONAL SALARY DETECTION
    # ========================================================

    salary_patterns = [

        # Indian Rupee
        r"₹\s*80[,\s]?000",
        r"₹\s*60[,\s]?000",
        r"₹\s*50[,\s]?000",

        # Rs / Rs.
        r"rs\.?\s*80[,\s]?000",
        r"rs\.?\s*60[,\s]?000",
        r"rs\.?\s*50[,\s]?000",

        # INR
        r"inr\s*80[,\s]?000",
        r"inr\s*60[,\s]?000",
        r"inr\s*50[,\s]?000",

        # Earn
        r"earn\s*80[,\s]?000",
        r"earn\s*60[,\s]?000",
        r"earn\s*50[,\s]?000"
    ]


    salary_already_detected = any(
        flag[0] == "Unrealistic Salary"
        for flag in detected_flags
    )


    if not salary_already_detected:

        for pattern in salary_patterns:

            if re.search(pattern, text):

                detected_flags.append(
                    ("Unrealistic Salary", "high salary")
                )

                break


    return detected_flags


# ============================================================
# CALCULATE RISK SCORE
# ============================================================

def calculate_risk(prediction, confidence, red_flags):

    risk_score = 0


    # --------------------------------------------------------
    # FAKE PREDICTION
    # --------------------------------------------------------

    if prediction == "fake":

        risk_score += 50


    # --------------------------------------------------------
    # ML CONFIDENCE
    # --------------------------------------------------------

    if confidence >= 80:

        risk_score += 20

    elif confidence >= 60:

        risk_score += 10


    # --------------------------------------------------------
    # RED FLAGS
    # --------------------------------------------------------

    risk_score += len(red_flags) * 10


    # Maximum risk score = 100
    risk_score = min(risk_score, 100)


    return risk_score


# ============================================================
# GET RISK LEVEL
# ============================================================

def get_risk_level(risk_score):

    if risk_score >= 60:

        return "HIGH RISK"

    elif risk_score >= 30:

        return "MEDIUM RISK"

    else:

        return "LOW RISK"


# ============================================================
# MAIN PREDICTION FUNCTION
# ============================================================

def predict_job(text):

    # --------------------------------------------------------
    # Convert text into ML features
    # --------------------------------------------------------

    text_vector = vectorizer.transform([text])


    # --------------------------------------------------------
    # Predict REAL or FAKE
    # --------------------------------------------------------

    prediction = model.predict(text_vector)[0]


    # --------------------------------------------------------
    # Get prediction probabilities
    # --------------------------------------------------------

    probabilities = model.predict_proba(text_vector)[0]


    # Highest probability = confidence
    confidence = max(probabilities) * 100


    # --------------------------------------------------------
    # Detect red flags
    # --------------------------------------------------------

    red_flags = detect_red_flags(text)


    # --------------------------------------------------------
    # Calculate risk score
    # --------------------------------------------------------

    risk_score = calculate_risk(
        prediction,
        confidence,
        red_flags
    )


    # --------------------------------------------------------
    # Determine risk level
    # --------------------------------------------------------

    risk_level = get_risk_level(risk_score)


    # --------------------------------------------------------
    # Return all results
    # --------------------------------------------------------

    return (
        prediction,
        confidence,
        red_flags,
        risk_score,
        risk_level
    )