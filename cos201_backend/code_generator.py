from openai import AsyncOpenAI
import os

async def generate_ml_script_with_ai(folder_path: str, target_var: str, feature_list: list, theme: str, openai_api_key: str):
    client = AsyncOpenAI(api_key=openai_api_key)
    
    prompt = f"""You are a Python code generator. Write a complete Python script for a Multiple Linear Regression analysis.

REQUIREMENTS:
- Read 'dataset.csv' from the current directory
- Predict '{target_var}' using features: {feature_list}
- Use statsmodels.api for OLS summary
- Use scikit-learn for train_test_split, LinearRegression, and metrics (R-squared, MAE, MSE)
- Generate 3 plots with seaborn/matplotlib:
  1. Correlation heatmap (save as 'heatmap.png')
  2. Actual vs Predicted scatter plot (save as 'scatter.png')
  3. Residual plot (save as 'residual.png')

CRITICAL RULES:
1. DO NOT use plt.show() - ONLY use plt.savefig() for all plots
2. Use random, unique variable names (NOT 'df', 'X', 'y' - be creative like 'data_frame', 'predictors', 'target_vals')
3. Use a random colormap for heatmap (choose from: viridis, plasma, coolwarm, RdYlBu, magma, cividis)
4. Add unique comments throughout the code
5. Output ONLY valid Python code with NO markdown formatting, NO backticks, NO explanations
6. CRITICAL: You MUST NOT use any non-ASCII or special characters in code or comments. Use 'R-squared' instead of 'R²', 'degrees' instead of '°', etc. Keep all text strictly standard ASCII.

Theme context: {theme}

Generate the complete script now:"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    
    code = response.choices[0].message.content.strip()
    
    # Remove markdown code blocks if present
    if code.startswith("```"):
        code = "\n".join(code.split("\n")[1:-1])
    
    # Prepend UTF-8 encoding declaration
    code = "# -*- coding: utf-8 -*-\n" + code
    
    script_path = os.path.join(folder_path, "main.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)
