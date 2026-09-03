
const textarea = document.querySelector("textarea");
const analyzeButton = document.querySelector(".analyze-btn");


// =========================================================
// CHARACTER COUNTER
// =========================================================

if (textarea) {

    const counter = document.createElement("div");

    counter.className = "character-counter";

    textarea.parentNode.insertBefore(
        counter,
        textarea.nextSibling
    );

    function updateCounter() {

        const count = textarea.value.length;

        counter.textContent =
            `${count.toLocaleString()} characters`;

    }

    textarea.addEventListener(
        "input",
        updateCounter
    );

    updateCounter();
}


// =========================================================
// ANALYZE BUTTON LOADING
// =========================================================

if (analyzeButton) {

    const form = analyzeButton.closest("form");

    if (form) {

        form.addEventListener(
            "submit",
            function () {

                analyzeButton.disabled = true;

                analyzeButton.innerHTML =
                    '<span class="loading-spinner"></span> Analyzing Job Offer...';

            }
        );

    }
}


// =========================================================
// RISK METER
// =========================================================

const riskMeter = document.querySelector(
    ".meter-fill"
);

if (riskMeter) {

    const riskScore = Number(
        riskMeter.dataset.riskScore
    );

    if (!Number.isNaN(riskScore)) {

        const safeScore = Math.min(
            Math.max(riskScore, 0),
            100
        );

        riskMeter.style.width =
            `${safeScore}%`;

    }

}

