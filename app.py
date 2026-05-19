from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- Conversation State ---
conversation = {
    "step": 0,
    "score": 0,
    "answers": {}
}

# --- Simple Patient Data Store (memory) ---
patient_records = []

TOTAL_STEPS = 4

# --- Result ---
def get_result(score):
    if score >= 5:
        return "🔴 EMERGENCY: Seek immediate care"
    elif score >= 3:
        return "🟡 MODERATE: Consult doctor"
    else:
        return "🟢 LOW: Rest and monitor"

# --- UI ---
def render_ui(question, options=None, result=None, summary=None):
    step = conversation["step"] + 1
    progress = int((step / TOTAL_STEPS) * 100)

    dropdown = ""
    if options:
        dropdown = f"""
        <select id="dropdown" onchange="goNext()" 
                style="padding:6px; font-size:13px; width:150px;">
            <option value="">Select</option>
            {"".join([f'<option value="{o}">{o}</option>' for o in options])}
        </select>
        """

    summary_html = ""
    if summary:
        summary_html = f"""
        <div style="margin-top:15px; font-size:13px;">
            <b>Summary:</b><br>
            Symptom: {summary['symptom']}<br>
            Duration: {summary['duration']}<br>
            Fever: {summary['fever']}<br>
            Breathing: {summary['breathing']}
        </div>
        """

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>

    <body style="font-family: Arial; background:#f4f6f8; padding:10px;">

        <div style="max-width:500px; margin:auto; background:white; 
                    padding:15px; border-radius:10px;">

            <h3>🏥 AI Triage</h3>

            <div style="background:#ddd; height:5px;">
                <div style="width:{progress}%; height:5px; background:#4CAF50;"></div>
            </div>

            <p style="font-size:12px;">Step {step}/{TOTAL_STEPS}</p>

            /chat
                <div style="display:flex; flex-wrap:wrap; gap:10px; font-size:13px;">
                    <span>{question}</span>
                    {dropdown}
                </div>
            </form>

            {summary_html}

            {f"<div style='margin-top:15px; font-weight:bold;'>{result}</div>" if result else ""}

            <p style="font-size:10px; color:gray;">
            ⚠️ Not a medical diagnosis
            </p>

        </div>

        <script>
        function goNext() {{
            let val = document.getElementById("dropdown").value;
            if(val !== "") {{
                window.location.href = "/chat?value=" + val;
            }}
        }}
        </script>

    </body>
    </html>
    """

# --- Logic ---
def process(value):
    global conversation

    step = conversation["step"]

    # Step 0
    if step == 0:
        conversation["answers"]["symptom"] = value
        conversation["score"] = 0
        conversation["step"] = 1
        return render_ui("Duration (days):", ["1", "2", "3", "4", "5+"])

    # Step 1
    elif step == 1:
        conversation["answers"]["duration"] = value

        if value.isdigit() and int(value) > 3:
            conversation["score"] += 2
        elif value == "5+":
            conversation["score"] += 2

        conversation["step"] = 2
        return render_ui("Fever?", ["yes", "no"])

    # Step 2
    elif step == 2:
        conversation["answers"]["fever"] = value

        if value == "yes":
            conversation["score"] += 2

        conversation["step"] = 3
        return render_ui("Breathing issue?", ["yes", "no"])

    # Step 3 → FINAL
    elif step == 3:
        conversation["answers"]["breathing"] = value

        if value == "yes":
            conversation["score"] += 5

        score = conversation["score"]
        result = get_result(score)

        # Save patient record ✅
        patient_records.append(conversation["answers"].copy())

        summary = conversation["answers"]

        # Reset
        conversation["step"] = 0
        conversation["score"] = 0
        conversation["answers"] = {}

        return render_ui(
            "Assessment Complete",
            result=result,
            summary=summary
        )

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
def home():
    return render_ui(
        "Select symptom:",
        ["fever", "cough", "headache", "chest pain"]
    )

@app.get("/chat", response_class=HTMLResponse)
def chat(value: str = ""):
    return process(value)