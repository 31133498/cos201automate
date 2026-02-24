# ============================================================
# pipeline/notebook_builder.py
#
# Builds the .ipynb notebook cell by cell using nbformat.
# Every markdown cell is filled with AI-generated narrative
# text from ai_narrator.py — unique prose per student.
# Code cells are templated (must be correct Python).
#
# Template index  = int(matric_no) % 10
# Narrative dict  = output of ai_narrator.generate_markdown_narrative()
# ============================================================

import nbformat as nbf
import os
import json

TEMPLATE_STYLES = [
    {"df_var": "df",         "heatmap_cmap": "coolwarm",  "scatter_color": "blue",
     "resid_color": "purple",        "model_order": "ols_first",   "extra_cell": "pairplot"},
    {"df_var": "data",       "heatmap_cmap": "viridis",   "scatter_color": "darkorange",
     "resid_color": "teal",          "model_order": "ridge_first", "extra_cell": "target_dist"},
    {"df_var": "records",    "heatmap_cmap": "RdYlGn",    "scatter_color": "green",
     "resid_color": "crimson",       "model_order": "ols_first",   "extra_cell": "coef_bar"},
    {"df_var": "dataset",    "heatmap_cmap": "plasma",    "scatter_color": "steelblue",
     "resid_color": "darkolivegreen","model_order": "ridge_first", "extra_cell": "target_dist"},
    {"df_var": "df_main",    "heatmap_cmap": "magma",     "scatter_color": "tomato",
     "resid_color": "slategray",     "model_order": "ols_first",   "extra_cell": "pairplot"},
    {"df_var": "raw",        "heatmap_cmap": "crest",     "scatter_color": "mediumpurple",
     "resid_color": "chocolate",     "model_order": "ridge_first", "extra_cell": "coef_bar"},
    {"df_var": "frame",      "heatmap_cmap": "mako",      "scatter_color": "dodgerblue",
     "resid_color": "darkred",       "model_order": "ols_first",   "extra_cell": "target_dist"},
    {"df_var": "table",      "heatmap_cmap": "flare",     "scatter_color": "seagreen",
     "resid_color": "darkorchid",    "model_order": "ridge_first", "extra_cell": "pairplot"},
    {"df_var": "entries",    "heatmap_cmap": "rocket",    "scatter_color": "firebrick",
     "resid_color": "cadetblue",     "model_order": "ols_first",   "extra_cell": "coef_bar"},
    {"df_var": "df_records", "heatmap_cmap": "icefire",   "scatter_color": "goldenrod",
     "resid_color": "indigo",        "model_order": "ridge_first", "extra_cell": "target_dist"},
]


def build_notebook(
    matric_no:    str,
    student_name: str,
    dataset_info: dict,
    save_dir:     str,
    narrative:    dict = None,
) -> tuple:
    """
    Build a complete pre-execution .ipynb file.

    Parameters
    ----------
    matric_no    : student matric number
    student_name : student full name
    dataset_info : from dataset_engine.generate_dataset()
    save_dir     : temp folder to write the .ipynb into
    narrative    : AI-generated markdown strings from ai_narrator.py
                   Keys: intro, eda_intro, ols_intro, reduced_intro,
                         sklearn_intro, ridge_intro, residual_intro, conclusion
    Returns
    -------
    (notebook_path, notebook_name)
    """
    if narrative is None:
        narrative = {}

    def n(key):
        """Retrieve narrative text, return empty string if missing."""
        return narrative.get(key, "")

    style    = TEMPLATE_STYLES[int(matric_no) % len(TEMPLATE_STYLES)]
    nb       = nbf.v4.new_notebook()
    cells    = []

    v        = style["df_var"]
    cmap     = style["heatmap_cmap"]
    sc       = style["scatter_color"]
    rc       = style["resid_color"]
    filename = dataset_info["filename"]
    target   = dataset_info["target"]
    features = dataset_info["features"]
    dname    = dataset_info["display_name"]
    n_rows   = dataset_info["n_rows"]

    feat_str  = json.dumps(features)
    feat3_str = json.dumps(features[:3])

    # ── CELL 1: Title + AI intro ──────────────────────────────────
    intro_text = n("intro") or (
        f"This notebook applies Multiple Linear Regression to the {dname} dataset "
        f"({n_rows} rows) to predict {target}. Four models are built and compared."
    )
    cells.append(nbf.v4.new_markdown_cell(
        f"# Multiple Linear Regression — {dname}\n"
        f"**Student:** {student_name} &nbsp;|&nbsp; **Matric No:** {matric_no}\n\n"
        f"---\n\n"
        f"{intro_text}\n\n"
        f"**Dataset:** `{filename}`  \n"
        f"**Target variable:** `{target}`  \n"
        f"**Features:** {', '.join(features)}\n"
    ))

    # ── CELL 2: Imports ───────────────────────────────────────────
    cells.append(nbf.v4.new_markdown_cell("## Section 1: Import Libraries"))
    cells.append(nbf.v4.new_code_cell(
        "import pandas as pd\n"
        "import numpy as np\n"
        "import matplotlib\n"
        "matplotlib.use('Agg')\n"
        "import matplotlib.pyplot as plt\n"
        "import seaborn as sns\n"
        "import statsmodels.api as sm\n"
        "from sklearn.model_selection import train_test_split\n"
        "from sklearn.linear_model import LinearRegression, Ridge\n"
        "from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error\n"
        "import warnings\n"
        "warnings.filterwarnings('ignore')\n"
        'print("Libraries loaded successfully.")'
    ))

    # ── CELL 3: Load data ─────────────────────────────────────────
    cells.append(nbf.v4.new_markdown_cell(
        f"## Section 2: Load and Explore the Dataset\n\n"
        f"We load `{filename}` and inspect its structure before any modelling."
    ))
    cells.append(nbf.v4.new_code_cell(
        f"{v} = pd.read_csv('{filename}')\n"
        f"print(f'Shape: {{{v}.shape}}')\n"
        f"print(f'Columns: {{list({v}.columns)}}')\n"
        f"{v}.head()"
    ))
    cells.append(nbf.v4.new_code_cell(
        f"print('Summary Statistics:')\n"
        f"{v}.describe()"
    ))

    # ── CELL 4: EDA — heatmap ─────────────────────────────────────
    eda_text = n("eda_intro") or (
        "Examining correlations between variables before modelling helps identify "
        "which features are most likely to be useful predictors of the target."
    )
    cells.append(nbf.v4.new_markdown_cell(
        f"## Section 3: Exploratory Data Analysis (EDA)\n\n"
        f"### 3.1 Correlation Heatmap\n\n"
        f"{eda_text}"
    ))
    cells.append(nbf.v4.new_code_cell(
        f"plt.figure(figsize=(10, 8))\n"
        f"sns.heatmap({v}.corr(numeric_only=True), annot=True, cmap='{cmap}', fmt='.2f', linewidths=0.5)\n"
        f"plt.title('Feature Correlation Matrix — {dname}')\n"
        f"plt.tight_layout()\n"
        f"plt.savefig('heatmap.png', dpi=150, bbox_inches='tight')\n"
        f"plt.show()\n"
        f'print("Heatmap saved.")'
    ))

    # ── CELL 5: Extra EDA cell (per template) ─────────────────────
    extra = style["extra_cell"]
    if extra == "pairplot":
        cells.append(nbf.v4.new_markdown_cell(
            "### 3.2 Pairplot\n\n"
            "Scatter plots between every pair of features reveal distributional patterns "
            "and potential non-linear relationships not visible in the heatmap."
        ))
        cells.append(nbf.v4.new_code_cell(
            f"sample = {v}.sample(min(200, len({v})), random_state=42)\n"
            f"sns.pairplot(sample, diag_kind='kde', plot_kws={{'alpha': 0.5}})\n"
            f"plt.suptitle('Pairplot — {dname}', y=1.02)\n"
            f"plt.tight_layout()\n"
            f"plt.savefig('pairplot.png', dpi=100, bbox_inches='tight')\n"
            f"plt.show()"
        ))
    elif extra == "target_dist":
        cells.append(nbf.v4.new_markdown_cell(
            f"### 3.2 Target Variable Distribution\n\n"
            f"Understanding the distribution of `{target}` before modelling reveals "
            f"skewness, outliers, or multimodality that could affect model performance."
        ))
        cells.append(nbf.v4.new_code_cell(
            f"plt.figure(figsize=(8, 5))\n"
            f"{v}['{target}'].hist(bins=30, color='{sc}', edgecolor='black', alpha=0.8)\n"
            f"plt.xlabel('{target}')\n"
            f"plt.ylabel('Frequency')\n"
            f"plt.title('Distribution of {target}')\n"
            f"plt.tight_layout()\n"
            f"plt.savefig('target_dist.png', dpi=150, bbox_inches='tight')\n"
            f"plt.show()"
        ))
    elif extra == "coef_bar":
        cells.append(nbf.v4.new_markdown_cell(
            f"### 3.2 Feature–Target Correlation Bar Chart\n\n"
            f"Ranking features by their correlation with `{target}` provides an initial "
            f"signal about which predictors are likely to be most informative."
        ))
        cells.append(nbf.v4.new_code_cell(
            f"correlations = {v}[list({feat_str}) + ['{target}']].corr(numeric_only=True)['{target}'].drop('{target}')\n"
            f"correlations = correlations.sort_values()\n"
            f"plt.figure(figsize=(8, 5))\n"
            f"correlations.plot(kind='barh', color=['{sc}' if c > 0 else '{rc}' for c in correlations])\n"
            f"plt.axvline(0, color='black', linewidth=0.8)\n"
            f"plt.xlabel('Correlation with {target}')\n"
            f"plt.title('Feature Correlations with Target')\n"
            f"plt.tight_layout()\n"
            f"plt.savefig('correlation_bar.png', dpi=150, bbox_inches='tight')\n"
            f"plt.show()"
        ))

    # ── CELL 6: Define X and y ────────────────────────────────────
    cells.append(nbf.v4.new_markdown_cell("## Section 4: Define Features and Target"))
    cells.append(nbf.v4.new_code_cell(
        f"features = list({feat_str})\n"
        f"target   = '{target}'\n\n"
        f"X = {v}[features]\n"
        f"y = {v}[target]\n\n"
        f"print(f'Features : {{features}}')\n"
        f"print(f'Target   : {{target}}')\n"
        f"print(f'X shape  : {{X.shape}}')\n"
        f"print(f'y shape  : {{y.shape}}')"
    ))

    # ── CELL 7: Train/test split ──────────────────────────────────
    sklearn_text = n("sklearn_intro") or (
        "The data is split 80/20 into training and test sets. "
        "The model is trained on 80% and evaluated on the 20% it has never seen, "
        "giving an honest estimate of generalisation performance."
    )
    cells.append(nbf.v4.new_markdown_cell(
        f"## Section 5: Train / Test Split\n\n{sklearn_text}"
    ))
    cells.append(nbf.v4.new_code_cell(
        "X_train, X_test, y_train, y_test = train_test_split(\n"
        "    X, y, test_size=0.20, random_state=42\n"
        ")\n"
        "print(f'Training rows : {len(X_train)}')\n"
        "print(f'Testing rows  : {len(X_test)}')"
    ))

    # ── CELLS 8+: Models (order varies per template) ──────────────
    if style["model_order"] == "ols_first":
        cells += _statsmodels_cells(v, feat_str, feat3_str, target, dname,
                                    n("ols_intro"), n("reduced_intro"))
        cells += _sklearn_cells(v, feat_str, target, sc, rc, dname,
                                n("ridge_intro"), n("residual_intro"))
    else:
        cells += _sklearn_cells(v, feat_str, target, sc, rc, dname,
                                n("ridge_intro"), n("residual_intro"))
        cells += _statsmodels_cells(v, feat_str, feat3_str, target, dname,
                                    n("ols_intro"), n("reduced_intro"))

    # ── CELL: Conclusion + metrics marker ────────────────────────
    conclusion_text = n("conclusion") or (
        f"Four regression models were built and evaluated on the {dname} dataset. "
        f"The results above quantify how well each model predicts {target}."
    )
    cells.append(nbf.v4.new_markdown_cell(
        f"## Section 8: Summary of Results\n\n{conclusion_text}"
    ))
    cells.append(nbf.v4.new_code_cell(
        'print("--- FINAL METRICS ---")\n'
        'print(f"SKLEARN_R2={lr_r2:.4f}")\n'
        'print(f"SKLEARN_MSE={lr_mse:.2f}")\n'
        'print(f"SKLEARN_MAE={lr_mae:.2f}")\n'
        'print(f"RIDGE_R2={ridge_r2:.4f}")\n'
        'print(f"TOP_FEATURE={features[0]}")\n'
        'print(f"TOP_COEF={list(lr_model.coef_)[0]:.4f}")\n'
        'print("DONE")'
    ))

    # ── Save ──────────────────────────────────────────────────────
    nb.cells = cells
    theme_base    = filename.replace(".csv", "")
    notebook_name = f"{theme_base}_regression.ipynb"
    notebook_path = os.path.join(save_dir, notebook_name)

    with open(notebook_path, "w") as f:
        nbf.write(nb, f)

    print(f"✅ Notebook built: {notebook_name} | template {int(matric_no) % 10} | AI narrative: {'yes' if narrative else 'fallback'}")
    return notebook_path, notebook_name


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def _statsmodels_cells(v, feat_str, feat3_str, target, dname, ols_intro, reduced_intro):
    ols_text = ols_intro or (
        "Statsmodels OLS produces a full academic statistical summary including "
        "p-values, confidence intervals, and the F-statistic for each predictor."
    )
    reduced_text = reduced_intro or (
        "A reduced model using only three features tests whether additional predictors "
        "meaningfully improve R² or simply add complexity without benefit."
    )
    return [
        nbf.v4.new_markdown_cell(
            f"## Section 6: Statsmodels OLS Regression\n\n"
            f"### 6.1 Full Model (all features)\n\n"
            f"{ols_text}"
        ),
        nbf.v4.new_code_cell(
            "X_full_sm = sm.add_constant(X)\n"
            "ols_full  = sm.OLS(y, X_full_sm).fit()\n"
            "print(ols_full.summary())"
        ),
        nbf.v4.new_markdown_cell(
            f"### 6.2 Reduced Model (top 3 features)\n\n{reduced_text}"
        ),
        nbf.v4.new_code_cell(
            f"X_red_sm = sm.add_constant({v}[list({feat3_str})])\n"
            f"ols_red  = sm.OLS(y, X_red_sm).fit()\n"
            f"print(ols_red.summary())\n"
            f"print(f'\\nFull model R²    : {{ols_full.rsquared:.4f}}')\n"
            f"print(f'Reduced model R² : {{ols_red.rsquared:.4f}}')"
        ),
    ]


def _sklearn_cells(v, feat_str, target, sc, rc, dname, ridge_intro, residual_intro):
    ridge_text = ridge_intro or (
        "Ridge regression applies an L2 penalty to shrink coefficients, "
        "which is useful when features exhibit multicollinearity."
    )
    residual_text = residual_intro or (
        "The residual plot checks model assumptions. "
        "A random scatter around zero confirms the linear model is appropriate."
    )
    return [
        nbf.v4.new_markdown_cell(
            "## Section 7: scikit-learn Regression Models\n\n"
            "### 7.1 Linear Regression (OLS via scikit-learn)\n\n"
            "scikit-learn's LinearRegression is trained on the 80% training split "
            "and scored on the held-out test set."
        ),
        nbf.v4.new_code_cell(
            "lr_model = LinearRegression()\n"
            "lr_model.fit(X_train, y_train)\n"
            "y_pred   = lr_model.predict(X_test)\n\n"
            "lr_r2  = r2_score(y_test, y_pred)\n"
            "lr_mse = mean_squared_error(y_test, y_pred)\n"
            "lr_mae = mean_absolute_error(y_test, y_pred)\n\n"
            "print(f'R-squared : {lr_r2:.4f}')\n"
            "print(f'MSE       : {lr_mse:,.2f}')\n"
            "print(f'MAE       : {lr_mae:,.2f}')\n"
            "print(f'Intercept : {lr_model.intercept_:,.2f}')\n"
            "print('\\nCoefficients:')\n"
            f"for name, coef in zip(list({feat_str}), lr_model.coef_):\n"
            "    print(f'  {name}: {coef:.4f}')"
        ),
        nbf.v4.new_markdown_cell(f"### 7.2 Ridge Regression\n\n{ridge_text}"),
        nbf.v4.new_code_cell(
            "ridge_model = Ridge(alpha=1.0)\n"
            "ridge_model.fit(X_train, y_train)\n"
            "ridge_pred  = ridge_model.predict(X_test)\n\n"
            "ridge_r2  = r2_score(y_test, ridge_pred)\n"
            "ridge_mse = mean_squared_error(y_test, ridge_pred)\n\n"
            "print(f'Ridge R²  : {ridge_r2:.4f}')\n"
            "print(f'Ridge MSE : {ridge_mse:,.2f}')\n"
            "print(f'\\nOLS R²    : {lr_r2:.4f}')\n"
            "print(f'Difference: {abs(ridge_r2 - lr_r2):.4f}')"
        ),
        nbf.v4.new_markdown_cell(
            "### 7.3 Actual vs Predicted Plot\n\n"
            f"Points close to the diagonal line indicate accurate predictions of `{target}`."
        ),
        nbf.v4.new_code_cell(
            "plt.figure(figsize=(10, 6))\n"
            f"plt.scatter(y_test, y_pred, alpha=0.7, color='{sc}', edgecolor='black', s=60)\n"
            f"plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Perfect Prediction Line')\n"
            f"plt.xlabel('Actual {target}')\n"
            f"plt.ylabel('Predicted {target}')\n"
            f"plt.title('Actual vs Predicted — {dname}')\n"
            "plt.legend()\n"
            "plt.grid(True, alpha=0.3)\n"
            "plt.tight_layout()\n"
            "plt.savefig('scatter.png', dpi=150, bbox_inches='tight')\n"
            "plt.show()\n"
            'print("Scatter plot saved.")'
        ),
        nbf.v4.new_markdown_cell(f"### 7.4 Residual Plot\n\n{residual_text}"),
        nbf.v4.new_code_cell(
            "residuals = y_test - y_pred\n"
            "plt.figure(figsize=(10, 6))\n"
            f"plt.scatter(y_pred, residuals, alpha=0.7, color='{rc}', edgecolor='black', s=60)\n"
            "plt.axhline(y=0, color='red', linestyle='--', lw=2)\n"
            f"plt.xlabel('Predicted {target}')\n"
            "plt.ylabel('Residuals')\n"
            f"plt.title('Residual Plot — {dname}')\n"
            "plt.grid(True, alpha=0.3)\n"
            "plt.tight_layout()\n"
            "plt.savefig('residual.png', dpi=150, bbox_inches='tight')\n"
            "plt.show()\n"
            'print("Residual plot saved.")'
        ),
    ]
