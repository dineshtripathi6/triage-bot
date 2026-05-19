from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI()

# ---------- DATABASE ----------
engine = create_engine("sqlite:///triage.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    symptom = Column(String)
    duration = Column(String)
    fever = Column(String)
    breathing = Column(String)
    result = Column(String)

Base.metadata.create_all(bind=engine)

# ---------- STATE ----------
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

# ---------- LOGIC ----------
def get_result(score):
    if score >= 5:
        return "EMERGENCY"
    elif score >= 3:
        return "MODERATE"
    return "LOW"

def get_color(res):
    return {
        "EMERGENCY": "#e53935",
        "MODERATE": "#fb8c00",
        "LOW": "#43a047"
    }.get(res, "#333")

# ---------- TRIAGE UI ----------
def render_ui(question=None, options=None, result=None):

    # answer chips
    answers_html = ""
    labels = ["Symptom","Duration","Fever","Breathing"]

    for i,(k,v) in enumerate(conversation["answers"].items()):
        if v:
            answers_html += f"""
            <span style="background:#eef3fc;padding:4px 10px;
                         border-radius:12px;font-size:11px;margin-right:5px;">
                {labels[i]}: {v}
            </span>
            """

    dropdown = ""
    if options:
        dropdown = f"""
        <select id="dd" onchange="goNext()"
                style="padding:6px;font-size:13px;border-radius:5px;">
            <option value="">Select</option>
            {"".join([f"<option>{o}</option>" for o in options])}
        </select>
        """

    qblock = ""
    if not result:
        qblock = f"""
        <div style="margin-top:20px">
            <b>{question}</b><br><br>
            {dropdown}
        </div>
        """

    return f"""
    <html>
    <body style="font-family:Segoe UI;background:#f4f6f8;margin:0">

        <div style="max-width:600px;margin:40px auto;background:white;
                    padding:20px;border-radius:10px;
                    box-shadow:0 3px 10px rgba(0,0,0,0.08)">

            <h2>🏥 AI Triage</h2>

            <!-- Progress -->
            <div style="background:#eee;height:6px;border-radius:4px">
                <div style="width:{(conversation["step"]/TOTAL_STEPS)*100}%;
                            height:6px;background:#4CAF50"></div>
            </div>

            <div style="font-size:11px;color:#666">
                Step {conversation["step"]+1}/{TOTAL_STEPS}
            </div>

            <div style="margin:10px 0">{answers_html}</div>

            {qblock}

            {f"""
            <div style="margin-top:20px;background:#f9fafc;
                        padding:15px;border-radius:6px">
                <div style="font-size:12px;color:#666">Risk</div>
                <div style="font-size:20px;font-weight:bold;
                            color:{get_color(result)}">
                    {result}
                </div>
            </div>
            """ if result else ""}

            <br>

            <!-- Buttons -->
            <button onclick="goBack()" style="padding:5px 10px;font-size:12px;">Back</button>
            <button onclick="clearAll()" style="padding:5px 10px;font-size:12px;">Clear</button>

            <!-- ✅ FIXED LINK -->
            <div style="margin-top:20px">
                <a href="/records" style="text-decoration:none;">
                    📋 View Patient Records →
                </a>
            </div>

        </div>

        <script>
        function goNext(){{
            let v = document.getElementById("dd").value;
            if(v) window.location="/chat?value="+v;
        }}
        function goBack(){{window.location="/back";}}
        function clearAll(){{window.location="/clear";}}
        </script>

    </body>
    </html>
    """

# ---------- FLOW ----------
def process(val):
    s = conversation["step"]

    if s == 0:
        conversation["answers"]["symptom"] = val
        conversation["score"] = 0
        conversation["step"] = 1
        return render_ui("Duration (days)", ["1","2","3","4","5+"])

    elif s == 1:
        conversation["answers"]["duration"] = val
        if val == "5+" or (val.isdigit() and int(val) > 3):
            conversation["score"] += 2
        conversation["step"] = 2
        return render_ui("Fever?", ["yes","no"])

    elif s == 2:
        conversation["answers"]["fever"] = val
        if val == "yes":
            conversation["score"] += 2
        conversation["step"] = 3
        return render_ui("Breathing issue?", ["yes","no"])

    elif s == 3:
        conversation["answers"]["breathing"] = val
        if val == "yes":
            conversation["score"] += 5

        res = get_result(conversation["score"])

        db = Session()
        db.add(Patient(**conversation["answers"], result=res))
        db.commit()
        db.close()

        return render_ui(result=res)

# ---------- NAV ----------
@app.get("/back", response_class=HTMLResponse)
def back():
    if conversation["step"] > 0:
        keys = list(conversation["answers"].keys())
        conversation["step"] -= 1
        conversation["answers"][keys[conversation["step"]]] = ""
    return home()

@app.get("/clear", response_class=HTMLResponse)
def clear():
    global conversation
    conversation = {
        "step": 0,"score":0,
        "answers":{"symptom":"","duration":"","fever":"","breathing":""}
    }
    return home()

@app.get("/", response_class=HTMLResponse)
def home():
    return render_ui("Select symptom",["fever","cough","headache","chest pain"])

@app.get("/chat", response_class=HTMLResponse)
def chat(value: str=""):
    return process(value)

# ---------- ✅ PROFESSIONAL GRID ----------
@app.get("/records", response_class=HTMLResponse)
def records():

    db = Session()
    data = db.query(Patient).all()
    db.close()

    rows = ""
    for p in data:
        rows += f"""
        <tr>
            <td>{p.id}</td>
            <td>{p.symptom}</td>
            <td>{p.duration}</td>
            <td class="{p.result}">{p.result}</td>
            <td>
                <button class="btn">🔍</button>
                <button class="btn">✏️</button>
            </td>
        </tr>
        """

    return f"""
<html>
<head>
<style>

body {{font-family:Segoe UI;background:#f4f6f8}}

.container {{
    max-width:1000px;margin:30px auto;
    background:white;padding:20px;border-radius:10px;
}}

table {{
    width:100%;
    border-collapse:collapse;
    table-layout:fixed;
}}

th {{
    background:#4a90e2;
    color:white;
    padding:10px;
    font-size:13px;
}}

td {{
    padding:10px;
    border-bottom:1px solid #eee;
}}

tr:nth-child(even) {{background:#fafafa}}

th select {{
    width:100%;
    font-size:12px;
}}

.EMERGENCY {{color:red;font-weight:bold}}
.MODERATE {{color:orange;font-weight:bold}}
.LOW {{color:green;font-weight:bold}}

.btn {{
    padding:4px 6px;
    font-size:11px;
}}

</style>
</head>

<body>

<div class="container">
<h2>📊 Patient Records</h2>

<table id="tbl">

<tr>
<th>ID<br><select onchange="f(0,this.value)"></select></th>

<th>Symptom<br>
<select onchange="f(1,this.value)">
<option></option>
<option>fever</option><option>cough</option>
<option>headache</option><option>chest pain</option>
</select></th>

<th>Duration<br>
<select onchange="f(2,this.value)">
<option></option>
<option>1</option><option>2</option><option>3</option>
<option>4</option><option>5+</option>
</select></th>

<th>Risk<br>
<select onchange="f(3,this.value)">
<option></option>
<option>EMERGENCY</option><option>MODERATE</option><option>LOW</option>
</select></th>

<th>Action</th>
</tr>

{rows}

</table>

<br>
<a href="/">← Back</a>

</div>

<script>
function f(c,v){{
let r=document.querySelectorAll("#tbl tr");
r.forEach((row,i)=>{{
if(i==0)return;
let t=row.cells[c].innerText;
row.style.display=(v==""||t==v)?"":"none";
}});
}}
</script>

</body>
</html>
"""