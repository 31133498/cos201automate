# ============================================================
# pipeline/notebook_builder.py
#
# Builds a complete .ipynb notebook for each student using
# nbformat. The notebook is built cell by cell in Python —
# no string hacks, proper notebook format.
#
# Template index = int(matric_no) % 10
# Each template differs in: dataframe variable name, plot
# colors, model build order, comment style, and extra cells.
#
# All templates produce the same 4 models and 3 graphs.
# The variation is cosmetic but meaningful enough that two
# notebooks look structurally different side by side.
# ============================================================

import nbformat as nbf
import os

# ============================================================
# TEMPLATE STYLE REGISTRY
# Defines the cosmetic variation per template index.
# ============================================================

TEMPLATE_STYLES = [
    # 0
    {"df_var": "df",         "heatmap_cmap": "coolwarm",  "scatter_color": "blue",
     "resid_color": "purple",      "model_order": "ols_first",  "extra_cell": "pairplot"},
    # 1
    {"df_var": "data",       "heatmap_cmap": "viridis",   "scatter_color": "darkorange",
     "resid_color": "teal",        "model_order": "ridge_first","extra_cell": "target_dist"},
    # 2
    {"df_var": "records",    "heatmap_cmap": "RdYlGn",    "scatter_color": "green",
     "resid_color": "crimson",     "model_order": "ols_first",  "extra_cell": "coef_bar"},
    # 3
    {"df_var": "dataset",    "heatmap_cmap": "plasma",    "scatter_color": "steelblue",
     "resid_color": "darkolivegreen","model_order":"ridge_first","extra_cell": "target_dist"},
    # 4
    {"df_var": "df_main",    "heatmap_cmap": "magma",     "scatter_color": "tomato",
     "resid_color": "slategray",   "model_order": "ols_first",  "extra_cell": "pairplot"},
    # 5
    {"df_var": "raw",        "heatmap_cmap": "crest",     "scatter_color": "mediumpurple",
     "resid_color": "chocolate",   "model_order": "ridge_first","extra_cell": "coef_bar"},
    # 6
    {"df_var": "frame",      "heatmap_cmap": "mako",      "scatter_color": "dodgerblue",
     "resid_color": "darkred",     "model_order": "ols_first",  "extra_cell": "target_dist"},
    # 7
    {"df_var": "table",      "heatmap_cmap": "flare",     "scatter_color": "seagreen",
     "resid_color": "darkorchid",  "model_order": "ridge_first","extra_cell": "pairplot"},
    # 8
    {"df_var": "entries",    "heatmap_cmap": "rocket",    "scatter_color": "firebrick",
     "resid_color": "cadetblue",   "model_order": "ols_first",  "extra_cell": "coef_bar"},
    # 9
    {"df_var": "df_records", "heatmap_cmap": "icefire",   "scatter_color": "goldenrod",
     "resid_color": "indigo",      "model_order": "ridge_first","extra_cell": "target_dist"},
]


def build_notebook(matric_no: str, student_name: str, dataset_info: dict, save_dir: str) -> str:
    """
    Build a complete .ipynb notebook for the student.

    Parameters
    ----------
    matric_no    : str  — e.g. '190401001'
    student_name : str  — e.g. 'Ada Okonkwo'
    dataset_info : dict — output from dataset_engine.generate_dataset()
    save_dir     : str  — temp folder to save the notebook into

    Returns
    -------
    Path to the saved .ipynb file
    """
    style    = TEMPLATE_STYLES[int(matric_no) % len(TEMPLATE_STYLES)]
    nb       = nbf.v4.new_notebook()
    cells    = []

    v        = style["df_var"]          # dataframe variable name
    cmap     = style["heatmap_cmap"]    # heatmap colour
    sc       = style["scatter_color"]   # scatter dot colour
    rc       = style["resid_color"]     # residual dot colour
    filename = dataset_info["filename"]
    target   = dataset_info["target"]
    features = dataset_info["features"]
    dname    = dataset_info["display_name"]
    n_rows   = dataset_info["n_rows"]

    # Build explicit Python list literals for injection into notebook code cells.
    # We use json.dumps to guarantee valid Python list syntax regardless of
    # column name content — avoids any set/dict ambiguity from str(list).
    import json
    feat_str  = json.dumps(features)        # e.g. '["col1", "col2", "col3"]'
    feat3_str = json.dumps(features[:3])    # first 3 only, for reduced model

    # ------------------------------------------------------------------
    # CELL 1 — Title markdown
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_markdown_cell(f"""# Multiple Linear Regression — {dname}
**Student:** {student_name} &nbsp;|&nbsp; **Matric No:** {matric_no}

---
This notebook performs Multiple Linear Regression on the **{dname}** dataset
({n_rows} rows). We build and compare four models, evaluate their performance,
and visualise the results.

**Dataset:** `{filename}`  
**Target variable:** `{target}`  
**Features:** {', '.join(features)}
"""))
    print(f"Building notebook for {student_name} ({matric_no}) with template {int(matric_no) % 10}")

    # ------------------------------------------------------------------
    # CELL 2 — Section 1 markdown
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_markdown_cell("## Section 1: Import Libraries"))

    # ------------------------------------------------------------------
    # CELL 3 — Imports code
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_code_cell("""\
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')
print("Libraries loaded successfully.")"""))

    # ------------------------------------------------------------------
    # CELL 4 — Section 2 markdown
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_markdown_cell(f"""\
## Section 2: Load and Explore the Dataset

We load `{filename}` and inspect its shape, column types, and summary statistics."""))

    # ------------------------------------------------------------------
    # CELL 5 — Load data
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_code_cell(f"""\
{v} = pd.read_csv('{filename}')
print("Shape:", {v}.shape)
print("Columns:", list({v}.columns))
{v}.head()"""))

    # ------------------------------------------------------------------
    # CELL 6 — Describe
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_code_cell(f"""\
print("Summary Statistics:")
{v}.describe()"""))

    # ------------------------------------------------------------------
    # CELL 7 — Section 3 markdown
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_markdown_cell("""\
## Section 3: Exploratory Data Analysis (EDA)

### 3.1 Correlation Heatmap

A heatmap shows how strongly each feature is linearly related to every other
feature and to the target. Values close to 1 or -1 indicate strong correlation."""))

    # ------------------------------------------------------------------
    # CELL 8 — Heatmap
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_code_cell(f"""\
plt.figure(figsize=(10, 8))
sns.heatmap({v}.corr(numeric_only=True), annot=True, cmap='{cmap}', fmt='.2f', linewidths=0.5)
plt.title('Feature Correlation Matrix — {dname}')
plt.tight_layout()
plt.savefig('heatmap.png', dpi=150, bbox_inches='tight')
plt.show()
print("Heatmap saved.")"""))

    # ------------------------------------------------------------------
    # CELL 9 — Extra cell (varies per template)
    # ------------------------------------------------------------------
    extra = style["extra_cell"]

    if extra == "pairplot":
        cells.append(nbf.v4.new_markdown_cell("### 3.2 Pairplot\nScatter plots of every feature pair coloured by density."))
        cells.append(nbf.v4.new_code_cell(f"""\
sample = {v}.sample(min(200, len({v})), random_state=42)
sns.pairplot(sample, diag_kind='kde', plot_kws={{'alpha': 0.5}})
plt.suptitle('Pairplot — {dname}', y=1.02)
plt.tight_layout()
plt.savefig('pairplot.png', dpi=100, bbox_inches='tight')
plt.show()"""))

    elif extra == "target_dist":
        cells.append(nbf.v4.new_markdown_cell(f"### 3.2 Target Variable Distribution\nHistogram of `{target}` to understand its spread."))
        cells.append(nbf.v4.new_code_cell(f"""\
plt.figure(figsize=(8, 5))
{v}['{target}'].hist(bins=30, color='{sc}', edgecolor='black', alpha=0.8)
plt.xlabel('{target}')
plt.ylabel('Frequency')
plt.title('Distribution of {target}')
plt.tight_layout()
plt.savefig('target_dist.png', dpi=150, bbox_inches='tight')
plt.show()"""))

    elif extra == "coef_bar":
        cells.append(nbf.v4.new_markdown_cell("### 3.2 Feature-Target Correlations\nBar chart of correlation between each feature and the target."))
        cells.append(nbf.v4.new_code_cell(f"""\
correlations = {v}[{feat_str} + ['{target}']].corr(numeric_only=True)['{target}'].drop('{target}')
correlations = correlations.sort_values()
plt.figure(figsize=(8, 5))
correlations.plot(kind='barh', color=['{sc}' if c > 0 else '{rc}' for c in correlations])
plt.axvline(0, color='black', linewidth=0.8)
plt.xlabel('Correlation with {target}')
plt.title('Feature Correlations with Target')
plt.tight_layout()
plt.savefig('correlation_bar.png', dpi=150, bbox_inches='tight')
plt.show()"""))

    # ------------------------------------------------------------------
    # CELL — Section 4 markdown
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_markdown_cell("""\
## Section 4: Define Features and Target"""))

    cells.append(nbf.v4.new_code_cell(f"""\
features = list({feat_str})
target   = '{target}'

X = {v}[{feat_str}]
y = {v}[target]

print(f"Features : {{features}}")
print(f"Target   : {{target}}")
print(f"X shape  : {{X.shape}}")
print(f"y shape  : {{y.shape}}")"""))

    # ------------------------------------------------------------------
    # CELL — Train/test split
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_markdown_cell("""\
## Section 5: Train / Test Split

We hold back 20% of the data for testing. The model is trained on 80% and
evaluated on the 20% it has never seen. This tests generalisation."""))

    cells.append(nbf.v4.new_code_cell(f"""\
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)
print(f"Training rows : {{len(X_train)}}")
print(f"Testing rows  : {{len(X_test)}}")"""))

    # ------------------------------------------------------------------
    # MODEL BUILD ORDER varies per template
    # ------------------------------------------------------------------
    if style["model_order"] == "ols_first":
        cells += _statsmodels_cells(v, feat_str, feat3_str, target, dname)
        cells += _sklearn_cells(v, feat_str, target, sc, rc, dname)
    else:
        cells += _sklearn_cells(v, feat_str, target, sc, rc, dname)
        cells += _statsmodels_cells(v, feat_str, feat3_str, target, dname)

    # ------------------------------------------------------------------
    # CELL — Final metrics marker (parsed by notebook_runner.py)
    # ------------------------------------------------------------------
    cells.append(nbf.v4.new_markdown_cell("## Section 8: Summary of Results"))
    cells.append(nbf.v4.new_code_cell(f"""\
# This cell prints metric markers that the system parses to build your defense guide
print("--- FINAL METRICS ---")
print(f"SKLEARN_R2={{lr_r2:.4f}}")
print(f"SKLEARN_MSE={{lr_mse:.2f}}")
print(f"SKLEARN_MAE={{lr_mae:.2f}}")
print(f"RIDGE_R2={{ridge_r2:.4f}}")
print(f"TOP_FEATURE={{features[0]}}")
print(f"TOP_COEF={{list(lr_model.coef_)[0]:.4f}}")
print("DONE")"""))

    # ------------------------------------------------------------------
    # Save notebook
    # ------------------------------------------------------------------
    nb.cells = cells
    theme_base    = dataset_info["filename"].replace(".csv", "")
    notebook_name = f"{theme_base}_regression.ipynb"
    notebook_path = os.path.join(save_dir, notebook_name)

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    print(f"✅ Notebook built: {notebook_name} | template {int(matric_no) % 10}")
    return notebook_path, notebook_name


# ============================================================
# HELPER FUNCTIONS — return lists of cells for each model block
# ============================================================

def _statsmodels_cells(v, feat_str, feat3_str, target, dname):
    """Returns the Statsmodels OLS cells (full + reduced model)."""
    return [
        nbf.v4.new_markdown_cell("""\
## Section 6: Statsmodels OLS Regression

Statsmodels gives a full academic statistical report including p-values,
confidence intervals, and the F-statistic for each predictor.

### 6.1 Full Model (all features)"""),
        nbf.v4.new_code_cell(f"""\
X_full_sm = sm.add_constant(X)
ols_full  = sm.OLS(y, X_full_sm).fit()
print(ols_full.summary())"""),
        nbf.v4.new_markdown_cell("""\
### 6.2 Reduced Model (top 3 features only)

We re-run with only the first 3 features to compare whether simplifying the
model significantly changes R². A similar R² with fewer features is preferred."""),
        nbf.v4.new_code_cell(f"""\
X_red_sm  = sm.add_constant({v}[list({feat3_str})])
ols_red   = sm.OLS(y, X_red_sm).fit()
print(ols_red.summary())
print(f"\\nFull model R²    : {{ols_full.rsquared:.4f}}")
print(f"Reduced model R² : {{ols_red.rsquared:.4f}}")"""),
    ]


def _sklearn_cells(v, feat_str, target, sc, rc, dname):
    """Returns the scikit-learn Linear Regression + Ridge cells and plots."""
    return [
        nbf.v4.new_markdown_cell("""\
## Section 7: scikit-learn Regression Models

### 7.1 Ordinary Least Squares (Linear Regression)

scikit-learn's LinearRegression uses the same OLS math but is optimised for
machine learning workflows with train/test splits."""),
        nbf.v4.new_code_cell(f"""\
lr_model  = LinearRegression()
lr_model.fit(X_train, y_train)
y_pred    = lr_model.predict(X_test)

lr_r2  = r2_score(y_test, y_pred)
lr_mse = mean_squared_error(y_test, y_pred)
lr_mae = mean_absolute_error(y_test, y_pred)

print(f"R-squared : {{lr_r2:.4f}}")
print(f"MSE       : {{lr_mse:,.2f}}")
print(f"MAE       : {{lr_mae:,.2f}}")
print(f"Intercept : {{lr_model.intercept_:,.2f}}")
print("\\nCoefficients:")
for name, coef in zip(list({feat_str}), lr_model.coef_):
    print(f"  {{name}}: {{coef:.4f}}")"""),
        nbf.v4.new_markdown_cell("""\
### 7.2 Ridge Regression

Ridge adds an L2 penalty to reduce overfitting when features are correlated."""),
        nbf.v4.new_code_cell(f"""\
ridge_model  = Ridge(alpha=1.0)
ridge_model.fit(X_train, y_train)
ridge_pred   = ridge_model.predict(X_test)

ridge_r2  = r2_score(y_test, ridge_pred)
ridge_mse = mean_squared_error(y_test, ridge_pred)

print(f"Ridge R²  : {{ridge_r2:.4f}}")
print(f"Ridge MSE : {{ridge_mse:,.2f}}")
print(f"\\nOLS R²    : {{lr_r2:.4f}}")
print(f"Difference: {{abs(ridge_r2 - lr_r2):.4f}}")"""),
        nbf.v4.new_markdown_cell("""\
### 7.3 Actual vs Predicted Plot

Points close to the red dashed line indicate accurate predictions."""),
        nbf.v4.new_code_cell(f"""\
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.7, color='{sc}', edgecolor='black', s=60)
plt.plot([y_test.min(), y_test.max()],
         [y_test.min(), y_test.max()],
         'r--', lw=2, label='Perfect Prediction Line')
plt.xlabel('Actual {target}')
plt.ylabel('Predicted {target}')
plt.title('Actual vs Predicted — {dname}')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('scatter.png', dpi=150, bbox_inches='tight')
plt.show()
print("Scatter plot saved.")"""),
        nbf.v4.new_markdown_cell("""\
### 7.4 Residual Plot

Residuals (actual minus predicted) should be randomly scattered around zero.
Any visible pattern suggests the model is missing a relationship."""),
        nbf.v4.new_code_cell(f"""\
residuals = y_test - y_pred
plt.figure(figsize=(10, 6))
plt.scatter(y_pred, residuals, alpha=0.7, color='{rc}', edgecolor='black', s=60)
plt.axhline(y=0, color='red', linestyle='--', lw=2)
plt.xlabel('Predicted {target}')
plt.ylabel('Residuals')
plt.title('Residual Plot — {dname}')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('residual.png', dpi=150, bbox_inches='tight')
plt.show()
print("Residual plot saved.")"""),
    ]
