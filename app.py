from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- State ---
conversation = {
    "step": 0,
    "score": 0,
    "answers": {
        "symptom": "",
        "duration": "",
        "fever": "",
        "breathing": ""
    }
}

TOTAL_STEPS = 4

# --- Result ---
def get_result(score):
    if score >= 5:
        return "<span style='color:red;'>🔴 EMERGENCY</span>"
    elif score >= 3:
        return "<span style='color:orange;'>🟡 MODERATE</span>"
    else:
        return "<span style='color:green;'>🟢 LOW</span>"

# --- UI ---
def render_ui(question, options=None, result=None):
    step = conversation["step"] + 1
    progress = int((step / TOTAL_STEPS) * 100)

    # Show previous answers
    answers_html = ""
    for key, val in conversation["answers"].items():
        if val:
            answers_html += f"<div style='font-size:12px;'>✅ {key.capitalize()}: {val}</div>"

    dropdown = ""
    if options:
        dropdown = f"""
        <select id="dropdown" onchange="goNext()" style="padding:6px; font-size:12px;">
            <option value="">Select</option>
            {"".join([f'<option value="{o}">{o}</option>' for o in options])}
        </select>
        """

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>

    <body style="font-family:Arial; background:#f4f6f8; padding:10px;">

        <div style="max-width:520px; margin:auto; background:white;
                    padding:15px; border-radius:8px;">

            <h3>🏥 AI Triage</h3>

            <!-- Progress -->
            <div style="background:#ddd; height:5px;">
                <div style="width:{progress}%; height:5px; background:#4CAF50;"></div>
            </div>

            <p style="font-size:11px;">Step {step}/{TOTAL_STEPS}</p>

            <!-- Previous answers -->
            {answers_html}

            <!-- Question -->
            <div style="margin-top:10px; font-size:13px;">
                <b>{question}</b>
            </div>

            <div style="margin-top:8px;">
                {dropdown}
            </div>

            <!-- Buttons -->
            <div style="margin-top:15px; display:flex; gap:10px;">

                <button onclick="goBack()" style="padding:5px 10px;">Back</button>

                <button onclick="clearAll()" style="padding:5px 10px;">Clear</button>

            </div>

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

        function goBack() {{
            window.location.href = "/back";
        }}

        function clearAll() {{
            window.location.href = "/clear";
        }}
        </script>

    </body>
    </html>
    """

# --- Logic ---
def process(value):
    global conversation
    step = conversation["step"]

    if step == 0:
        conversation["answers"]["symptom"] = value
        conversation["score"] = 0
        conversation["step"] = 1
        return render_ui("Duration (days):", ["1","2","3","4","5+"])

    elif step == 1:
        conversation["answers"]["duration"] = value

        if value.isdigit() and int(value) > 3:
            conversation["score"] += 2
        elif value == "5+":
            conversation["score"] += 2

        conversation["step"] = 2
        return render_ui("Do you have fever?", ["yes","no"])

    elif step == 2:
        conversation["answers"]["fever"] = value

        if value == "yes":
            conversation["score"] += 2

        conversation["step"] = 3
        return render_ui("Breathing difficulty?", ["yes","no"])

    elif step == 3:
        conversation["answers"]["breathing"] = value

        if value == "yes":
            conversation["score"] += 5

        score = conversation["score"]
        result = get_result(score)

        return render_ui("Assessment Complete", result=result)

# --- Navigation Controls ---

@app.get("/back", response_class=HTMLResponse)
def back():
    if conversation["step"] > 0:
        conversation["step"] -= 1
    return home_step()

@app.get("/clear", response_class=HTMLResponse)
def clear():
    global conversation
    conversation = {
        "step": 0,
        "score": 0,
        "answers": {"symptom":"","duration":"","fever":"","breathing":""}
    }
    return home()

# --- Helper to load correct question ---
def home_step():
    step = conversation["step"]

    if step == 0:
        return render_ui("Select symptom:", ["fever","cough","headache","chest pain"])
    elif step == 1:
        return render_ui("Duration (days):", ["1","2","3","4","5+"])
    elif step == 2:
        return render_ui("Do you have fever?", ["yes","no"])
    elif step == 3:
        return render_ui("Breathing difficulty?", ["yes","no"])

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
def home():
    return home_step()

@app.get("/chat", response_class=HTMLResponse)
def chat(value: str = ""):
    return process(value)