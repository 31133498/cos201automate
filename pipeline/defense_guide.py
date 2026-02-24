# ============================================================
# pipeline/defense_guide.py
#
# Generates a plain-English defense guide using the real
# metric values extracted from the executed notebook.
#
# The guide is saved as defense_guide.txt and included in
# the student's ZIP. It prepares them for a lab viva by
# explaining their specific numbers in plain language.
# ============================================================

import os
from datetime import datetime


def generate_defense_guide(
    save_dir:     str,
    student_name: str,
    matric_no:    str,
    dataset_info: dict,
    metrics:      dict
) -> str:
    """
    Write defense_guide.txt using the student's actual results.

    Parameters
    ----------
    save_dir     : str  — folder to save the file into
    student_name : str  — student's full name
    matric_no    : str  — matric number
    dataset_info : dict — from dataset_engine.generate_dataset()
    metrics      : dict — from notebook_runner.run_notebook()

    Returns
    -------
    Path to the saved defense_guide.txt
    """
    r2      = metrics["r2"]
    r2_pct  = round(r2 * 100, 1)
    mse     = metrics["mse"]
    mae     = metrics["mae"]
    rid_r2  = metrics["ridge_r2"]
    t_feat  = metrics["top_feature"]
    t_coef  = float(metrics["top_coef"]) if metrics["top_coef"] != "N/A" else 0.0

    accuracy = (
        "highly accurate" if r2 >= 0.80
        else "moderately accurate" if r2 >= 0.60
        else "reasonably fitted"
    )
    coef_direction = "increases" if t_coef > 0 else "decreases"
    ridge_comment  = (
        "regularisation had minimal effect on accuracy"
        if abs(rid_r2 - r2) < 0.02
        else "regularisation noticeably changed the model"
    )

    guide = f"""ASSIGNMENT DEFENSE GUIDE
========================================================
Student   : {student_name}
Matric No : {matric_no}
Dataset   : {dataset_info['filename']} ({dataset_info['display_name']})
Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}
========================================================

WHAT YOUR ANALYSIS DID
--------------------------------------------------------
Your notebook performs Multiple Linear Regression on the
{dataset_info['display_name']} dataset ({dataset_info['n_rows']} rows).
The goal is to predict '{dataset_info['target']}' using these
6 features: {', '.join(dataset_info['features'])}.

You built four models:
  Model 1 — Statsmodels OLS, all 6 features (full model)
  Model 2 — Statsmodels OLS, top 3 features (reduced model)
  Model 3 — scikit-learn Linear Regression (train/test split)
  Model 4 — scikit-learn Ridge Regression (regularised)

YOUR RESULTS — say these numbers confidently
--------------------------------------------------------
R-squared (R²)         = {r2:.4f}
  Your model is {accuracy}. It explains {r2_pct}% of the
  variation in '{dataset_info['target']}'. If asked, say:
  "My model explains {r2_pct}% of the variance in the target."

Mean Squared Error     = {mse:,.2f}
  Average squared gap between actual and predicted values.
  Lower is better. Large values are normal when the target
  variable itself has large values (e.g. house prices).

Mean Absolute Error    = {mae:,.2f}
  On average, your predictions are off by {mae:,.2f} units.
  This is easier to interpret than MSE because it is in the
  same unit as '{dataset_info['target']}'.

Ridge R²               = {rid_r2:.4f}
  Compared to your OLS R² of {r2:.4f}, this means {ridge_comment}.

MOST INFLUENTIAL FEATURE
--------------------------------------------------------
Feature     : {t_feat}
Coefficient : {t_coef:.4f}
  For every 1-unit increase in '{t_feat}', the predicted
  '{dataset_info['target']}' {coef_direction} by {abs(t_coef):,.4f} units,
  assuming all other features stay constant. This is called
  a partial effect or marginal effect.

VIVA QUESTIONS AND HOW TO ANSWER THEM
--------------------------------------------------------
Q: What does R-squared mean?
A: It measures how much of the variation in {dataset_info['target']}
   my model explains. Mine is {r2:.4f}, so {r2_pct}%.

Q: Why did you use Ridge Regression?
A: To handle potential multicollinearity between features.
   Ridge adds an L2 penalty that shrinks coefficients and
   reduces overfitting when features are correlated.

Q: What is the difference between MSE and MAE?
A: MSE squares each error, heavily penalising large mistakes.
   MAE takes the absolute value, treating all errors equally.
   MSE is more sensitive to outliers than MAE.

Q: What is a train/test split and why do you use it?
A: I split the data 80/20. The model trains on 80% and is
   evaluated on the 20% it has never seen. This tests whether
   the model generalises to new data, not just memorises
   the training set.

Q: What does the residual plot tell you?
A: Residuals (actual minus predicted) should be randomly
   scattered around zero with no pattern. A random scatter
   means the model assumptions are satisfied. Any visible
   curve or funnel shape would suggest a problem.

Q: What is the difference between Model 1 and Model 2?
A: Model 1 uses all 6 features. Model 2 uses only the top 3.
   Comparing their R² tells us whether the extra 3 features
   add meaningful predictive power or just noise.

Q: What does the heatmap show?
A: It shows the Pearson correlation between every pair of
   variables. Values near 1 mean strong positive correlation,
   near -1 mean strong negative, near 0 mean no linear
   relationship. It helps identify which features are most
   related to the target.
"""

    guide_path = os.path.join(save_dir, "defense_guide.txt")
    with open(guide_path, "w") as f:
        f.write(guide)

    print("✅ Defense guide written.")
    return guide_path
