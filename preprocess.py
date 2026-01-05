import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# -----------------------------
# Load dataset
# -----------------------------
df = pd.read_csv("COVID-19-Hospitals-Treatment-Plan.csv")

# -----------------------------
# Encode categorical features
# -----------------------------
categorical_cols = [
    'Hospital',
    'Hospital_type',
    'Hospital_city',
    'Hospital_region',
    'Department',
    'Ward_Type',
    'Ward_Facility',
    'Type_of_Admission',
    'Illness_Severity',
    'Age'
]

label_encoders = {}

for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# -----------------------------
# Features and target
# -----------------------------
X = df.drop(columns=['case_id', 'patientid', 'Stay_Days'])
y = df['Stay_Days']

# -----------------------------
# Train-test split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# Train Random Forest model
# -----------------------------
clf = RandomForestClassifier(
    n_estimators=50,
    random_state=42
)

clf.fit(X_train, y_train)

# -----------------------------
# Predict on full dataset
# -----------------------------
df['Predicted_Stay'] = clf.predict(X)

# -----------------------------
# Cost per day assumptions
# -----------------------------
cost_per_day = {
    'General': 2000,
    'Surgery': 5000,
    'TB & Chest': 3000
}

severity_multiplier = {
    'Minor': 1.0,
    'Moderate': 1.5,
    'Severe': 2.0
}

# -----------------------------
# Decode columns back to original labels
# -----------------------------
for col, le in label_encoders.items():
    df[col] = le.inverse_transform(df[col])

# -----------------------------
# Estimate treatment cost
# -----------------------------
def estimate_cost(row):
    dept = row['Department']
    severity = row['Illness_Severity']

    daily_rate = cost_per_day.get(dept, 2500)
    multiplier = severity_multiplier.get(severity, 1.0)

    stay_value = row['Predicted_Stay']
    
    # Handle ranges like "11-20"
    if isinstance(stay_value, str) and '-' in stay_value:
        stay_days = int(stay_value.split('-')[0])
    else:
        try:
            stay_days = int(stay_value)
        except:
            stay_days = 10  # default fallback

    return daily_rate * multiplier * stay_days

df['Estimated_Cost'] = df.apply(estimate_cost, axis=1)

# -----------------------------
# Save predictions
# -----------------------------
df.to_csv("predictions.csv", index=False)
print("✅ Training done. Predictions saved to predictions.csv")
