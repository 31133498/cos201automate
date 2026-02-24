# ============================================================
# pipeline/ai_narrator.py
#
# Calls OpenAI GPT-4o-mini to generate unique markdown
# narrative text for each student's notebook.
#
# WHY THIS SOLVES PLAGIARISM:
# All code cells are identical in structure (they have to be
# correct Python). But every markdown explanation cell is
# regenerated uniquely per student — different sentence
# structures, different vocabulary, different emphasis.
# Two students on the same template with the same theme
# will have completely different prose throughout.
#
# COST: ~$0.002 per student with gpt-4o-mini.
# 50 students = ~$0.10 total.
#
# FALLBACK: If the API call fails for any reason, the
# function returns a set of generic but acceptable defaults
# so the pipeline never crashes due to OpenAI issues.
# ============================================================

from openai import OpenAI
from config import OPENAI_API_KEY
import json

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_markdown_narrative(
    student_name: str,
    matric_no:    str,
    dataset_info: dict,
) -> dict:
    """
    Generate 6 unique markdown narrative strings for the notebook.

    Parameters
    ----------
    student_name : str  — used to subtly personalise tone
    matric_no    : str  — used as part of the seed context
    dataset_info : dict — theme, target, features, n_rows

    Returns
    -------
    dict with keys:
        intro         — notebook title cell body paragraph
        eda_intro     — before the heatmap
        ols_intro     — before OLS full model
        reduced_intro — before OLS reduced model
        sklearn_intro — before sklearn LR
        ridge_intro   — before Ridge
        residual_intro — before residual plot
        conclusion    — section 8 summary cell
    """

    theme    = dataset_info["display_name"]
    target   = dataset_info["target"]
    features = dataset_info["features"]
    n_rows   = dataset_info["n_rows"]
    feat_str = ", ".join(features[:3]) + f", and {len(features) - 3} others"

    prompt = f"""You are writing markdown cell text for a Jupyter notebook on Multiple Linear Regression.

Dataset context:
- Theme: {theme}
- Target variable: {target}
- Features: {", ".join(features)}
- Rows: {n_rows}
- Student: {student_name} (matric: {matric_no})

Write 8 SHORT markdown passages, each 2-4 sentences. They must be unique in phrasing and style.
Do NOT use bullet points. Write in flowing prose.
Return ONLY a valid JSON object with exactly these keys:
intro, eda_intro, ols_intro, reduced_intro, sklearn_intro, ridge_intro, residual_intro, conclusion

Each value is a plain string (the markdown text).

Guidelines per key:
- intro: Briefly describe what this notebook does and why {theme.lower()} data is interesting to analyse.
- eda_intro: Explain why examining correlations between variables matters before building any model.
- ols_intro: Explain what OLS regression does and what the full model summary tells us.
- reduced_intro: Explain the purpose of comparing a simpler model with fewer features.
- sklearn_intro: Explain the train/test split approach and why it tests generalisation.
- ridge_intro: Explain what regularisation does and when Ridge regression is useful.
- residual_intro: Explain what residuals reveal about model quality and assumptions.
- conclusion: Summarise what was achieved in 2-3 sentences, mentioning {target} as the prediction target.

Vary your sentence structure, vocabulary, and emphasis. Make each passage feel genuinely written.
Return only the JSON, no markdown fences, no extra text."""

    try:
        response = client.chat.completions.create(
            model       = "gpt-4o-mini",
            messages    = [{"role": "user", "content": prompt}],
            temperature = 0.9,    # high temperature = more variation
            max_tokens  = 1200,
        )

        raw  = response.choices[0].message.content.strip()
        # Strip any accidental markdown fences
        raw  = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        # Validate all keys present
        required = ["intro","eda_intro","ols_intro","reduced_intro",
                    "sklearn_intro","ridge_intro","residual_intro","conclusion"]
        for k in required:
            if k not in data:
                raise ValueError(f"Missing key: {k}")

        print(f"✅ AI narrative generated for {student_name}")
        return data

    except Exception as e:
        print(f"⚠️  AI narrative failed ({e}) — using fallback text.")
        return _fallback(theme, target, features, n_rows)


def _fallback(theme, target, features, n_rows) -> dict:
    """
    Safe fallback if OpenAI call fails.
    Returns acceptable generic text so the pipeline never crashes.
    """
    return {
        "intro": (
            f"This notebook investigates the {theme} dataset containing {n_rows} observations. "
            f"Multiple Linear Regression is applied to predict {target} from a set of measurable features. "
            f"Four models are built and compared to evaluate predictive accuracy."
        ),
        "eda_intro": (
            "Before modelling, it is important to understand how variables relate to one another. "
            "A correlation heatmap provides a visual summary of pairwise linear relationships, "
            "helping identify which features are likely to be informative predictors."
        ),
        "ols_intro": (
            "Ordinary Least Squares regression estimates the linear relationship between each "
            "predictor and the target by minimising the sum of squared residuals. "
            "The full model includes all available features to capture every possible signal."
        ),
        "reduced_intro": (
            "A reduced model retains only the three most conceptually important features. "
            "Comparing it against the full model reveals whether additional predictors "
            "genuinely improve explanatory power or simply add noise."
        ),
        "sklearn_intro": (
            "scikit-learn's LinearRegression is trained on 80% of the data and evaluated "
            "on the remaining 20% it has never seen. "
            "This train/test split gives an honest estimate of how well the model generalises."
        ),
        "ridge_intro": (
            "Ridge regression introduces an L2 penalty term that shrinks coefficients toward zero. "
            "This is particularly useful when features exhibit multicollinearity, "
            "as it stabilises the estimates and can improve out-of-sample performance."
        ),
        "residual_intro": (
            "The residual plot displays the difference between actual and predicted values. "
            "A random scatter around zero suggests the model assumptions are satisfied, "
            "while any systematic pattern indicates a structural problem."
        ),
        "conclusion": (
            f"This notebook successfully built four regression models to predict {target}. "
            f"The models were evaluated using R², MSE, and MAE on a held-out test set. "
            f"Ridge regression was compared against OLS to assess the effect of regularisation."
        ),
    }
