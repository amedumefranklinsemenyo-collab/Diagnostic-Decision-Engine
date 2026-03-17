import streamlit as st
import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Clinical Decision Support System",
    layout="wide"
)

st.title("🏥 Clinical Decision Support System")
st.subheader("AI-Enhanced Patient Vital Monitoring Dashboard")

# ---------------- FOLDERS ----------------

if not os.path.exists("reports"):
    os.makedirs("reports")

if not os.path.exists("database"):
    os.makedirs("database")

# ---------------- DATABASE ----------------

conn = sqlite3.connect("database/patients.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
age INTEGER,
gender TEXT,
date TEXT,
weight REAL,
height REAL,
bmi REAL,
spo2 REAL,
pulse REAL,
temperature REAL,
systolic REAL,
diastolic REAL
)
""")

conn.commit()

# ---------------- LOAD CSV ----------------

advice_df = pd.read_csv("hospital_vital_decision_tables.csv")

# ---------------- FUNCTIONS ----------------

def get_advice(vital,value):

    df = advice_df[advice_df["Vital"] == vital]

    for _,row in df.iterrows():

        if row["Min Value"] <= value <= row["Max Value"]:
            return row["Notes"]

    return "No clinical interpretation available."

# BMI calculation

def calculate_bmi(weight,height):
    return round(weight/(height**2),1)

# Health status classification

def health_status(spo2,pulse,temp,sys):

    if spo2 < 90 or sys > 180 or temp > 39:
        return "🔴 Critical – Immediate Attention"

    elif spo2 < 95 or pulse > 110 or temp > 37.5:
        return "🟡 Needs Monitoring"

    else:
        return "🟢 Stable"

# ---------------- SIDEBAR ----------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
"Select Page",
["Patient Analysis","Patient Database"]
)

# =========================
# PAGE 1 – PATIENT ANALYSIS
# =========================

if page == "Patient Analysis":

    st.header("🧑‍⚕️ Patient Information")

    col1,col2,col3 = st.columns(3)

    with col1:
        name = st.text_input("Patient Name")

        age = st.number_input("Age",0,120)

        gender = st.selectbox(
        "Gender",
        ["Male","Female","Other"]
        )

    with col2:

        weight = st.number_input("Weight (kg)",0.0)

        height = st.number_input("Height (m)",0.0)

        date = st.date_input("Date")

    with col3:

        spo2 = st.number_input("SpO₂ (%)",0.0)

        pulse = st.number_input("Pulse Rate (bpm)",0.0)

        temp = st.number_input("Temperature (°C)",0.0)

    st.subheader("Blood Pressure")

    col4,col5 = st.columns(2)

    with col4:
        systolic = st.number_input("Systolic BP")

    with col5:
        diastolic = st.number_input("Diastolic BP")

    if st.button("Analyze Patient"):

        bmi = calculate_bmi(weight,height)

        status = health_status(spo2,pulse,temp,systolic)

        # Save to database

        cursor.execute("""
        INSERT INTO patients
        (name,age,gender,date,weight,height,bmi,spo2,pulse,temperature,systolic,diastolic)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,(name,age,gender,date,weight,height,bmi,spo2,pulse,temp,systolic,diastolic))

        conn.commit()

        st.success("Patient data stored successfully")

        # ---------------- METRICS DASHBOARD ----------------

        st.subheader("📊 Vital Signs Dashboard")

        c1,c2,c3,c4 = st.columns(4)

        c1.metric("BMI",bmi)

        c2.metric("SpO₂",spo2)

        c3.metric("Pulse",pulse)

        c4.metric("Temp",temp)

        # ---------------- HEALTH STATUS ----------------

        st.subheader("Patient Health Status")

        st.markdown(f"## {status}")

        # ---------------- CLINICAL ANALYSIS ----------------

        st.subheader("🧠 Clinical Decision Support")

        bmi_advice = get_advice("BMI",bmi)
        spo2_advice = get_advice("SpO2",spo2)
        pulse_advice = get_advice("Pulse",pulse)
        temp_advice = get_advice("Temperature",temp)

        st.write("**BMI Interpretation:**",bmi_advice)
        st.write("**SpO₂ Interpretation:**",spo2_advice)
        st.write("**Pulse Interpretation:**",pulse_advice)
        st.write("**Temperature Interpretation:**",temp_advice)

        # ---------------- GRAPH ----------------

        st.subheader("📈 Vital Signs Graph")

        vitals = ["BMI","SpO2","Pulse","Temp","SysBP"]
        values = [bmi,spo2,pulse,temp,systolic]

        fig,ax = plt.subplots()

        ax.bar(vitals,values)

        ax.set_title("Patient Vital Signs")

        st.pyplot(fig)

        # ---------------- PDF GENERATION ----------------
if st.button("Generate PDF Report"):
    import os
    import webbrowser
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet

    if not os.path.exists("reports"):
        os.makedirs("reports")

    filename = f"reports/{name}_report.pdf"

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Clinical Decision Report", styles["Title"]))
    story.append(Spacer(1, 20))

    story.append(Paragraph(f"Name: {name}", styles["Normal"]))
    story.append(Paragraph(f"Age: {age}", styles["Normal"]))
    story.append(Paragraph(f"Gender: {gender}", styles["Normal"]))
    story.append(Paragraph(f"Date: {date}", styles["Normal"]))
    story.append(Spacer(1, 20))

    bmi = calculate_bmi(weight, height)

    story.append(Paragraph(f"BMI: {bmi}", styles["Normal"]))
    story.append(Paragraph(f"SpO₂: {spo2}", styles["Normal"]))
    story.append(Paragraph(f"Pulse: {pulse}", styles["Normal"]))
    story.append(Paragraph(f"Temperature: {temp}", styles["Normal"]))
    story.append(Spacer(1, 20))

    # ✅ FIX: recompute advice in this scope
    bmi_advice = get_advice("BMI",bmi)
    spo2_advice = get_advice("SpO2",spo2)
    pulse_advice = get_advice("Pulse",pulse)
    temp_advice = get_advice("Temperature",temp)

    story.append(Paragraph("Clinical Advice", styles["Heading2"]))
    story.append(Paragraph(bmi_advice, styles["Normal"]))
    story.append(Paragraph(spo2_advice, styles["Normal"]))
    story.append(Paragraph(pulse_advice, styles["Normal"]))
    story.append(Paragraph(temp_advice, styles["Normal"]))

    pdf = SimpleDocTemplate(filename, pagesize=letter)
    pdf.build(story)

    absolute_path = os.path.abspath(filename)
    webbrowser.open(f'file://{absolute_path}')

    st.success("PDF Report Generated and Opened")

# =========================
# PAGE 2 – PATIENT DATABASE
# =========================

elif page == "Patient Database":

    st.header("🗄 Patient Records")

    df = pd.read_sql_query("SELECT * FROM patients", conn)
    st.dataframe(df)

    st.markdown("---")

    if st.button("⚠ Clear Patient Database"):
        cursor.execute("DELETE FROM patients")
        conn.commit()
        st.warning("All patient records have been cleared!")
        df = pd.read_sql_query("SELECT * FROM patients", conn)
        st.dataframe(df)
