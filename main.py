import sys
import pandas as pd

# ---------------- Configuration ----------------
CSV_PATH = "COVID-19-Hospitals-Treatment-Plan.csv"

ROLE_ALIASES = {
    "doctor": "doctor", "doc": "doctor", "dr": "doctor",
    "nurse": "nurse",
    "admin": "admin", "administrator": "admin",
    "patient": "patient"
}

VALID_ROLES = {"doctor", "nurse", "admin", "patient"}

REQUIRED_COLUMNS = {
    "patientid", "Department", "Illness_Severity", "Type_of_Admission",
    "Stay_Days", "Ward_Type", "Ward_Facility", "Patient_Visitors",
    "Hospital", "Available_Extra_Rooms_in_Hospital", "Admission_Deposit"
}

# ---------------- Helpers ----------------
def normalize_role(s: str) -> str:
    if s is None:
        return ""
    return ROLE_ALIASES.get(s.strip().lower(), s.strip().lower())


def coerce_patientid(df: pd.DataFrame) -> pd.DataFrame:
    df["patientid"] = pd.to_numeric(df["patientid"], errors="coerce")
    df = df.dropna(subset=["patientid"]).copy()
    df["patientid"] = df["patientid"].astype(int)
    return df


def parse_stay_days(stay_val):
    s = str(stay_val).strip()
    if "-" in s:
        parts = s.split("-")
        try:
            low = int(parts[0].strip())
            high = int(parts[1].strip())
            est = (low + high) / 2
            return max(est, 1.0), f"{low}-{high}"
        except:
            pass
    if s.isdigit():
        return max(float(s), 1.0), s
    return 1.0, s


def safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default


# ---------------- Main ----------------
# Load CSV
try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    print(f"❌ File not found: {CSV_PATH}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Failed to read CSV: {e}")
    sys.exit(1)

# Validate required columns
missing_cols = REQUIRED_COLUMNS - set(df.columns)
if missing_cols:
    print(f"❌ Missing columns in CSV: {sorted(missing_cols)}")
    sys.exit(1)

# Coerce patientid
df = coerce_patientid(df)

# Role input
role_raw = input("Enter your role (Doctor / Nurse / Admin / Patient): ")
role = normalize_role(role_raw)

if role not in VALID_ROLES:
    print("❌ Invalid role entered! Access denied.")
    sys.exit(1)

# Patient ID input
pid_raw = input("Enter Patient ID (exact, numeric): ").strip()
if not pid_raw.isdigit():
    print("❌ Invalid ID entered. Must be numeric.")
    sys.exit(1)

patient_id = int(pid_raw)

# Strict match
matches = df[df["patientid"] == patient_id]
if matches.empty:
    print(f"❌ Patient ID {patient_id} not found!")
    sample_ids = df["patientid"].drop_duplicates().head(20).tolist()
    print(f"🔎 Example valid IDs: {sample_ids}")
    sys.exit(1)

p = matches.iloc[0]
if len(matches) > 1:
    print(f"⚠ Found {len(matches)} records for Patient ID {patient_id}. Showing first record.")

# ---------------- Cost Calculation ----------------
est_days, label_text = parse_stay_days(p["Stay_Days"])

DAILY_COST_MATRIX = {
    "General": {"Low": 3000, "Moderate": 5000, "High": 7000},
    "ICU": {"Low": 10000, "Moderate": 15000, "High": 20000}
}

dept = p.get("Department", "General")
severity = p.get("Illness_Severity", "Low")

daily_rate = DAILY_COST_MATRIX.get(
    dept, DAILY_COST_MATRIX["General"]
).get(severity, 3000)

total_cost = round(est_days * daily_rate, 2)

cost_breakdown = {
    "Bed": round(total_cost * 0.4, 2),
    "Procedures": round(total_cost * 0.3, 2),
    "Nursing": round(total_cost * 0.2, 2),
    "Misc": round(total_cost * 0.1, 2)
}

# ---------------- Role Views ----------------
if role == "doctor":
    print(f"""
👨‍⚕️ Doctor View
Patient ID: {p['patientid']}
Department: {dept}
Illness Severity: {severity}
Type of Admission: {p['Type_of_Admission']}
Recorded Stay: {p['Stay_Days']}
""")

elif role == "nurse":
    print(f"""
👩‍⚕️ Nurse View
Patient ID: {p['patientid']}
Ward Type: {p['Ward_Type']}
Ward Facility: {p['Ward_Facility']}
Visitors Allowed: {p['Patient_Visitors']}
Illness Severity: {severity}
""")

elif role == "admin":
    print(f"""
🧑‍💼 Admin View
Patient ID: {p['patientid']}
Hospital: {p['Hospital']}
Available Extra Rooms: {p['Available_Extra_Rooms_in_Hospital']}
Estimated Total Cost: ₹{total_cost} (based on {dept} & {severity})

Cost Breakdown:
- Bed: ₹{cost_breakdown['Bed']}
- Procedures: ₹{cost_breakdown['Procedures']}
- Nursing: ₹{cost_breakdown['Nursing']}
- Misc: ₹{cost_breakdown['Misc']}
""")

elif role == "patient":
    per_day_cost = round(total_cost / est_days, 2)
    print(f"""
🧑 Patient View
Dear Patient {p['patientid']},

- Type of Admission: {p['Type_of_Admission']}
- Illness Severity: {severity}
- Estimated Stay: {label_text} (~ {est_days:.1f} days)
- Total Expected Cost: ₹{total_cost}

Cost Breakdown:
- Bed: ₹{cost_breakdown['Bed']}
- Procedures: ₹{cost_breakdown['Procedures']}
- Nursing: ₹{cost_breakdown['Nursing']}
- Misc: ₹{cost_breakdown['Misc']}
- Per Day Cost: ₹{per_day_cost}

Calculation:
₹{daily_rate} × {est_days:.1f} days = ₹{total_cost}
""")
