import numpy as np
import pandas as pd
import os

def generate_student_dataset(matric_no: str) -> tuple[str, str, list]:
    seed = int(matric_no[-4:])
    np.random.seed(seed)
    
    themes = [
        {
            "name": "Housing_Prices",
            "features": ["square_feet", "num_bedrooms", "age_of_house", "distance_to_center", "crime_rate"],
            "target": "price",
            "generators": lambda: {
                "square_feet": np.random.randint(800, 4000, 550),
                "num_bedrooms": np.random.randint(1, 6, 550),
                "age_of_house": np.random.randint(0, 50, 550),
                "distance_to_center": np.random.uniform(0.5, 30, 550),
                "crime_rate": np.random.uniform(0, 100, 550)
            },
            "coefficients": [150, 20000, -500, -2000, -300],
            "intercept": 50000
        },
        {
            "name": "Car_Efficiency",
            "features": ["engine_size", "weight", "horsepower", "age", "cylinders"],
            "target": "mpg",
            "generators": lambda: {
                "engine_size": np.random.uniform(1.0, 5.0, 550),
                "weight": np.random.randint(2000, 5000, 550),
                "horsepower": np.random.randint(80, 400, 550),
                "age": np.random.randint(0, 20, 550),
                "cylinders": np.random.choice([4, 6, 8], 550)
            },
            "coefficients": [-3, -0.005, -0.02, -0.5, -2],
            "intercept": 50
        },
        {
            "name": "Student_Performance",
            "features": ["study_hours", "attendance_rate", "previous_score", "sleep_hours", "tutoring_sessions"],
            "target": "final_score",
            "generators": lambda: {
                "study_hours": np.random.uniform(0, 40, 550),
                "attendance_rate": np.random.uniform(50, 100, 550),
                "previous_score": np.random.uniform(40, 100, 550),
                "sleep_hours": np.random.uniform(4, 10, 550),
                "tutoring_sessions": np.random.randint(0, 20, 550)
            },
            "coefficients": [0.8, 0.3, 0.4, 1.5, 0.5],
            "intercept": 10
        },
        {
            "name": "Employee_Salary",
            "features": ["years_experience", "performance_score", "training_hours", "projects_completed", "age"],
            "target": "salary",
            "generators": lambda: {
                "years_experience": np.random.randint(0, 30, 550),
                "performance_score": np.random.uniform(1, 10, 550),
                "training_hours": np.random.randint(0, 200, 550),
                "projects_completed": np.random.randint(0, 50, 550),
                "age": np.random.randint(22, 65, 550)
            },
            "coefficients": [3000, 5000, 50, 800, 500],
            "intercept": 30000
        },
        {
            "name": "Health_Metrics",
            "features": ["exercise_hours", "calorie_intake", "water_intake", "stress_level", "sleep_quality"],
            "target": "health_score",
            "generators": lambda: {
                "exercise_hours": np.random.uniform(0, 15, 550),
                "calorie_intake": np.random.randint(1200, 4000, 550),
                "water_intake": np.random.uniform(0.5, 4, 550),
                "stress_level": np.random.uniform(1, 10, 550),
                "sleep_quality": np.random.uniform(1, 10, 550)
            },
            "coefficients": [2, 0.01, 5, -3, 4],
            "intercept": 50
        }
    ]
    
    theme = themes[np.random.randint(0, len(themes))]
    data = theme["generators"]()
    
    target_values = float(theme["intercept"])
    for i, feature in enumerate(theme["features"]):
        target_values += theme["coefficients"][i] * np.array(data[feature], dtype=float)
    
    noise = np.random.normal(0, np.std(target_values) * 0.15, 550)
    data[theme["target"]] = target_values + noise
    
    df = pd.DataFrame(data)
    
    output_dir = f"./temp/{matric_no}"
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "dataset.csv")
    df.to_csv(csv_path, index=False)
    
    return (os.path.abspath(output_dir), theme["target"], theme["features"])
