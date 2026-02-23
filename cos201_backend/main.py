from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db_manager import init_db, validate_token
from data_engine import generate_student_dataset
from code_generator import generate_ml_script_with_ai
from mailer import zip_and_email
import subprocess
import shutil
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    name: str
    matric_no: str
    email: str
    token: str

@app.post("/generate")
async def generate(request: GenerateRequest):
    if not validate_token(request.token):
        raise HTTPException(status_code=401, detail="Invalid or already used token")
    
    folder_path, target_var, feature_list = generate_student_dataset(request.matric_no)
    
    # Extract theme from folder structure
    import pandas as pd
    df = pd.read_csv(os.path.join(folder_path, "dataset.csv"))
    columns = df.columns.tolist()
    
    # Determine theme based on target variable
    theme_map = {
        "price": "Housing_Prices",
        "mpg": "Car_Efficiency",
        "final_score": "Student_Performance",
        "salary": "Employee_Salary",
        "health_score": "Health_Metrics"
    }
    theme = theme_map.get(target_var, "Unknown")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    await generate_ml_script_with_ai(folder_path, target_var, feature_list, theme, openai_api_key)
    
    try:
        result = subprocess.run(
            ["python", "main.py"],
            cwd=folder_path,
            timeout=20,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            shutil.rmtree(folder_path)
            raise HTTPException(status_code=500, detail=f"Script execution failed: {result.stderr}")
        
        # Generate defense guide
        defense_text = f"""ML Assignment Defense Guide

Your Model Overview:
- Target Variable: {target_var}
- Key Features: {', '.join(feature_list[:3])}
- Theme: {theme}
- Dataset Size: 550 rows

Your model uses Multiple Linear Regression to predict {target_var} based on factors like {feature_list[0]} and {feature_list[1]}.

Key Points for Defense:
1. Explain why {feature_list[0]} affects {target_var}
2. Discuss the R-squared value from your OLS summary
3. Interpret the coefficients for each feature
4. Explain the residual plot and what it shows about model fit
"""
        
        with open(os.path.join(folder_path, "defense_guide.txt"), "w") as f:
            f.write(defense_text)
        
        # Zip and email
        zip_and_email(folder_path, request.email)
        
        return {"status": "success", "message": "Analysis complete and emailed"}
        
    except subprocess.TimeoutExpired:
        shutil.rmtree(folder_path)
        raise HTTPException(status_code=500, detail="Script execution timed out")
    except Exception as e:
        shutil.rmtree(folder_path)
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
