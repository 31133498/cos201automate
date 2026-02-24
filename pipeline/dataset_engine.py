# ============================================================
# pipeline/dataset_engine.py
#
# Generates a unique synthetic dataset for each student.
#
# HOW IT WORKS:
#   np.random.seed(int(matric_no)) sets the random generator
#   to a deterministic state. Same matric = same data every
#   time. Different matric = completely different data.
#
#   Theme index = int(matric_no) % 10
#   This splits students across 10 different dataset topics.
#   The CSV is named after the theme, not the student.
# ============================================================

import numpy as np
import pandas as pd
import os

# ============================================================
# THEME REGISTRY
# Each theme defines the filename, target variable, and
# feature column names. The actual data generation for
# each theme is in the generate_dataset() function below.
# ============================================================

THEMES = [
    # 0
    {
        "filename":     "housing_market.csv",
        "display_name": "Housing Market",
        "target":       "price",
        "features":     ["square_feet", "num_bedrooms", "num_bathrooms",
                         "lot_size", "year_built", "distance_to_center"],
    },
    # 1
    {
        "filename":     "ecommerce_sales.csv",
        "display_name": "E-commerce Sales",
        "target":       "revenue",
        "features":     ["daily_visitors", "conversion_rate", "avg_order_value",
                         "ad_spend", "return_rate", "session_duration"],
    },
    # 2
    {
        "filename":     "student_performance.csv",
        "display_name": "Student Performance",
        "target":       "final_score",
        "features":     ["study_hours", "attendance_pct", "prev_gpa",
                         "sleep_hours", "assignment_avg", "extracurricular_hrs"],
    },
    # 3
    {
        "filename":     "hospital_records.csv",
        "display_name": "Hospital Records",
        "target":       "treatment_cost",
        "features":     ["patient_age", "bmi", "num_conditions",
                         "hospital_days", "num_medications", "distance_km"],
    },
    # 4
    {
        "filename":     "retail_inventory.csv",
        "display_name": "Retail Inventory",
        "target":       "monthly_sales",
        "features":     ["shelf_position", "price_per_unit", "discount_pct",
                         "stock_level", "foot_traffic", "competitor_price"],
    },
    # 5
    {
        "filename":     "crop_yield.csv",
        "display_name": "Crop Yield",
        "target":       "yield_tonnes",
        "features":     ["rainfall_mm", "temperature_avg", "fertilizer_kg",
                         "farm_size_ha", "sunlight_hours", "soil_quality_index"],
    },
    # 6
    {
        "filename":     "loan_risk.csv",
        "display_name": "Loan Risk",
        "target":       "loan_amount",
        "features":     ["annual_income", "credit_score", "employment_years",
                         "existing_debt", "num_dependants", "property_value"],
    },
    # 7
    {
        "filename":     "traffic_volume.csv",
        "display_name": "Traffic Volume",
        "target":       "daily_vehicles",
        "features":     ["road_width_m", "num_lanes", "nearby_population",
                         "traffic_signals", "distance_from_city", "avg_speed_kmh"],
    },
    # 8
    {
        "filename":     "energy_consumption.csv",
        "display_name": "Energy Consumption",
        "target":       "kwh_used",
        "features":     ["floor_area_sqm", "num_occupants", "avg_temperature",
                         "num_appliances", "insulation_rating", "solar_panels"],
    },
    # 9
    {
        "filename":     "employee_salary.csv",
        "display_name": "Employee Salary",
        "target":       "annual_salary",
        "features":     ["years_experience", "education_level", "num_skills",
                         "department_size", "performance_score", "overtime_hrs"],
    },
]


def generate_dataset(matric_no: str, save_dir: str) -> dict:
    """
    Generate a personalized dataset and save it as a CSV.

    Parameters
    ----------
    matric_no : str  — e.g. '190401001'
    save_dir  : str  — temp folder path to save the CSV into

    Returns
    -------
    dict with: csv_path, filename, display_name, target, features, n_rows
    """
    seed        = int(matric_no)
    np.random.seed(seed)

    theme_index = seed % len(THEMES)
    theme       = THEMES[theme_index]
    features    = theme["features"]
    target      = theme["target"]

    # Row count varies per student: 500–800
    n_rows = int(np.random.randint(500, 801))

    # ------------------------------------------------------------------
    # DATA GENERATION
    # Each theme uses realistic value ranges and a linear formula
    # with Gaussian noise. The noise is also seeded so it's unique
    # per student but reproducible on retry.
    # ------------------------------------------------------------------

    if theme_index == 0:   # Housing Market
        f0 = np.random.randint(800, 4500, n_rows).astype(float)
        f1 = np.random.randint(1, 7, n_rows).astype(float)
        f2 = np.round(np.random.uniform(1.0, 4.5, n_rows) * 2) / 2
        f3 = np.round(np.random.uniform(0.10, 2.50, n_rows), 2)
        f4 = np.random.randint(1960, 2024, n_rows).astype(float)
        f5 = np.round(np.random.uniform(0.5, 45.0, n_rows), 1)
        noise = np.random.normal(0, 18000, n_rows)
        y = 150*f0 + 28000*f1 + 15000*f2 + 12000*f3 + 500*(f4-1960) - 3000*f5 + noise
        y = np.round(np.clip(y, 40000, 1500000), 2)

    elif theme_index == 1: # E-commerce Sales
        f0 = np.random.randint(200, 15000, n_rows).astype(float)
        f1 = np.round(np.random.uniform(0.005, 0.12, n_rows), 4)
        f2 = np.round(np.random.uniform(15.0, 350.0, n_rows), 2)
        f3 = np.round(np.random.uniform(50.0, 5000.0, n_rows), 2)
        f4 = np.round(np.random.uniform(0.01, 0.25, n_rows), 3)
        f5 = np.round(np.random.uniform(60, 900, n_rows), 1)
        noise = np.random.normal(0, 500, n_rows)
        y = 0.08*f0 + 1800*f1 + 12*f2 + 0.5*f3 - 800*f4 + 2*f5 + noise
        y = np.round(np.clip(y, 100, 80000), 2)

    elif theme_index == 2: # Student Performance
        f0 = np.round(np.random.uniform(0, 12, n_rows), 1)
        f1 = np.round(np.random.uniform(40, 100, n_rows), 1)
        f2 = np.round(np.random.uniform(1.0, 4.0, n_rows), 2)
        f3 = np.round(np.random.uniform(3, 10, n_rows), 1)
        f4 = np.round(np.random.uniform(30, 100, n_rows), 1)
        f5 = np.round(np.random.uniform(0, 15, n_rows), 1)
        noise = np.random.normal(0, 4, n_rows)
        y = 3.5*f0 + 0.3*f1 + 8*f2 + 1.2*f3 + 0.4*f4 + 0.5*f5 + noise
        y = np.round(np.clip(y, 20, 100), 1)

    elif theme_index == 3: # Hospital Records
        f0 = np.random.randint(18, 90, n_rows).astype(float)
        f1 = np.round(np.random.uniform(16.0, 45.0, n_rows), 1)
        f2 = np.random.randint(0, 6, n_rows).astype(float)
        f3 = np.random.randint(1, 30, n_rows).astype(float)
        f4 = np.random.randint(0, 12, n_rows).astype(float)
        f5 = np.round(np.random.uniform(0.5, 120, n_rows), 1)
        noise = np.random.normal(0, 1200, n_rows)
        y = 150*f0 + 200*f1 + 3000*f2 + 2500*f3 + 800*f4 + 20*f5 + noise
        y = np.round(np.clip(y, 500, 250000), 2)

    elif theme_index == 4: # Retail Inventory
        f0 = np.random.randint(1, 6, n_rows).astype(float)
        f1 = np.round(np.random.uniform(2.0, 200.0, n_rows), 2)
        f2 = np.round(np.random.uniform(0, 0.5, n_rows), 3)
        f3 = np.random.randint(10, 500, n_rows).astype(float)
        f4 = np.random.randint(50, 5000, n_rows).astype(float)
        f5 = np.round(np.random.uniform(2.0, 210.0, n_rows), 2)
        noise = np.random.normal(0, 50, n_rows)
        y = 80*f0 - 2*f1 + 300*f2 + 0.2*f3 + 0.15*f4 - 1.5*f5 + noise
        y = np.round(np.clip(y, 5, 3000), 1)

    elif theme_index == 5: # Crop Yield
        f0 = np.round(np.random.uniform(200, 1500, n_rows), 1)
        f1 = np.round(np.random.uniform(15, 40, n_rows), 1)
        f2 = np.round(np.random.uniform(50, 600, n_rows), 1)
        f3 = np.round(np.random.uniform(0.5, 50, n_rows), 2)
        f4 = np.round(np.random.uniform(4, 12, n_rows), 1)
        f5 = np.round(np.random.uniform(1, 10, n_rows), 1)
        noise = np.random.normal(0, 0.8, n_rows)
        y = 0.005*f0 - 0.02*f1 + 0.01*f2 + 0.3*f3 + 0.4*f4 + 0.5*f5 + noise
        y = np.round(np.clip(y, 0.5, 30), 2)

    elif theme_index == 6: # Loan Risk
        f0 = np.random.randint(20000, 200000, n_rows).astype(float)
        f1 = np.random.randint(300, 850, n_rows).astype(float)
        f2 = np.random.randint(0, 30, n_rows).astype(float)
        f3 = np.round(np.random.uniform(0, 80000, n_rows), 2)
        f4 = np.random.randint(0, 6, n_rows).astype(float)
        f5 = np.round(np.random.uniform(0, 500000, n_rows), 2)
        noise = np.random.normal(0, 3000, n_rows)
        y = 0.2*f0 + 30*f1 + 500*f2 - 0.1*f3 - 200*f4 + 0.05*f5 + noise
        y = np.round(np.clip(y, 1000, 500000), 2)

    elif theme_index == 7: # Traffic Volume
        f0 = np.round(np.random.uniform(3, 30, n_rows), 1)
        f1 = np.random.randint(1, 8, n_rows).astype(float)
        f2 = np.random.randint(1000, 500000, n_rows).astype(float)
        f3 = np.random.randint(0, 10, n_rows).astype(float)
        f4 = np.round(np.random.uniform(0.5, 50, n_rows), 1)
        f5 = np.round(np.random.uniform(20, 120, n_rows), 1)
        noise = np.random.normal(0, 800, n_rows)
        y = 200*f0 + 3000*f1 + 0.05*f2 - 400*f3 - 500*f4 + 100*f5 + noise
        y = np.round(np.clip(y, 500, 80000), 0)

    elif theme_index == 8: # Energy Consumption
        f0 = np.round(np.random.uniform(30, 500, n_rows), 1)
        f1 = np.random.randint(1, 10, n_rows).astype(float)
        f2 = np.round(np.random.uniform(-5, 45, n_rows), 1)
        f3 = np.random.randint(1, 20, n_rows).astype(float)
        f4 = np.random.randint(1, 10, n_rows).astype(float)
        f5 = np.random.randint(0, 2, n_rows).astype(float)
        noise = np.random.normal(0, 30, n_rows)
        y = 1.5*f0 + 50*f1 + 8*f2 + 20*f3 - 15*f4 - 80*f5 + noise
        y = np.round(np.clip(y, 50, 3000), 1)

    else:                  # theme_index == 9 — Employee Salary
        f0 = np.random.randint(0, 35, n_rows).astype(float)
        f1 = np.random.randint(1, 5, n_rows).astype(float)
        f2 = np.random.randint(1, 20, n_rows).astype(float)
        f3 = np.random.randint(5, 200, n_rows).astype(float)
        f4 = np.round(np.random.uniform(1, 5, n_rows), 1)
        f5 = np.round(np.random.uniform(0, 20, n_rows), 1)
        noise = np.random.normal(0, 5000, n_rows)
        y = 3000*f0 + 8000*f1 + 1500*f2 + 100*f3 + 4000*f4 + 200*f5 + noise
        y = np.round(np.clip(y, 15000, 300000), 2)

    # Build the dataframe
    df = pd.DataFrame({
        features[0]: f0, features[1]: f1, features[2]: f2,
        features[3]: f3, features[4]: f4, features[5]: f5,
        target: y
    })

    # Save to student's temp folder
    os.makedirs(save_dir, exist_ok=True)
    csv_path = os.path.join(save_dir, theme["filename"])
    df.to_csv(csv_path, index=False)

    print(f"✅ Dataset: {theme['filename']} | {n_rows} rows | theme {theme_index}: {theme['display_name']}")

    return {
        "csv_path":     csv_path,
        "filename":     theme["filename"],
        "display_name": theme["display_name"],
        "target":       target,
        "features":     features,
        "n_rows":       n_rows,
        "theme_index":  theme_index,
    }
