import streamlit as st
import pandas as pd

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Hospital Cost Estimation Dashboard",
    layout="wide"
)

st.title("🏥 Hospital Cost Estimation & Role-Based Access System")
st.markdown("Interactive dashboard for hospital stay analysis and cost estimation")

# ---------------- Load Data ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("COVID-19-Hospitals-Treatment-Plan.csv")
    return df

df = load_data()

# ---------------- Helper Functions ----------------
def parse_stay_days(stay_val):
    s = str(stay_val).strip()
    if "-" in s:
        low, high = s.split("-")
        est = (int(low) + int(high)) / 2
        return est, f"{low}-{high}"
    if s.isdigit():
        return float(s), s
    return 1.0, s


def estimate_cost(dept, severity, stay_days):
    DAILY_COST_MATRIX = {
        "General": {"Low": 3000, "Moderate": 5000, "High": 7000},
        "ICU": {"Low": 10000, "Moderate": 15000, "High": 20000}
    }
    daily_rate = DAILY_COST_MATRIX.get(
        dept, DAILY_COST_MATRIX["General"]
    ).get(severity, 3000)

    total = round(stay_days * daily_rate, 2)

    breakdown = {
        "Bed": round(total * 0.4, 2),
        "Procedures": round(total * 0.3, 2),
        "Nursing": round(total * 0.2, 2),
        "Misc": round(total * 0.1, 2),
        "Daily Rate": daily_rate
    }

    return total, breakdown


# ---------------- Sidebar Controls ----------------
st.sidebar.header("🔐 Access Control")

role = st.sidebar.selectbox(
    "Select Role",
    ["doctor", "nurse", "admin", "patient"]
)

patient_ids = sorted(df["patientid"].dropna().astype(int).unique())
patient_id = st.sidebar.selectbox(
    "Select Patient ID",
    patient_ids
)

# ---------------- Fetch Patient ----------------
p = df[df["patientid"] == patient_id].iloc[0]

stay_days, stay_label = parse_stay_days(p["Stay_Days"])
total_cost, cost_breakdown = estimate_cost(
    p["Department"],
    p["Illness_Severity"],
    stay_days
)

# ---------------- Role-Based Views ----------------
st.subheader(f"📌 Role View: {role.capitalize()}")

if role == "doctor":
    st.info("👨‍⚕️ Doctor View")
    st.write(f"**Patient ID:** {patient_id}")
    st.write(f"**Department:** {p['Department']}")
    st.write(f"**Illness Severity:** {p['Illness_Severity']}")
    st.write(f"**Type of Admission:** {p['Type_of_Admission']}")
    st.write(f"**Recorded Stay:** {p['Stay_Days']}")

elif role == "nurse":
    st.info("👩‍⚕️ Nurse View")
    st.write(f"**Patient ID:** {patient_id}")
    st.write(f"**Ward Type:** {p['Ward_Type']}")
    st.write(f"**Ward Facility:** {p['Ward_Facility']}")
    st.write(f"**Visitors Allowed:** {p['Patient_Visitors']}")
    st.write(f"**Illness Severity:** {p['Illness_Severity']}")

elif role == "admin":
    st.warning("🧑‍💼 Admin View")
    st.write(f"**Patient ID:** {patient_id}")
    st.write(f"**Hospital:** {p['Hospital']}")
    st.write(f"**Available Extra Rooms:** {p['Available_Extra_Rooms_in_Hospital']}")
    st.metric("💰 Estimated Total Cost (₹)", total_cost)

    st.subheader("📊 Cost Breakdown")
    st.json(cost_breakdown)

elif role == "patient":
    st.success("🧑 Patient View")
    st.write(f"**Type of Admission:** {p['Type_of_Admission']}")
    st.write(f"**Illness Severity:** {p['Illness_Severity']}")
    st.write(f"**Estimated Stay:** {stay_label} (~ {stay_days:.1f} days)")
    st.metric("💵 Total Expected Cost (₹)", total_cost)

    st.subheader("🧾 Cost Breakdown")
    for k, v in cost_breakdown.items():
        if k != "Daily Rate":
            st.write(f"- **{k}:** ₹{v}")

    per_day = round(total_cost / stay_days, 2)
    st.write(f"**Per Day Cost:** ₹{per_day}")
    st.write(
        f"**Calculation:** ₹{cost_breakdown['Daily Rate']} × {stay_days:.1f} days = ₹{total_cost}"
    )

# ---------------- Footer ----------------
st.markdown("---")
st.caption("🎓 Academic Project | Hospital Analytics | Streamlit Dashboard")
