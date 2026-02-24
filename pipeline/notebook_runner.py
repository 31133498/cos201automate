# ============================================================
# pipeline/notebook_runner.py
#
# Executes the student's notebook using nbconvert.
# After execution, the notebook file contains rendered cell
# outputs — plots are embedded as base64 PNG data inside
# the notebook JSON itself.
#
# We then:
#   1. Re-open the executed notebook
#   2. Find image output cells and save them as standalone PNGs
#   3. Parse the FINAL METRICS block from stdout output cells
# ============================================================

import subprocess
import sys
import os
import re
import json
import base64


def run_notebook(notebook_path: str, save_dir: str) -> dict:
    """
    Execute the notebook in-place using nbconvert --execute.
    This runs every code cell and writes the output (including
    rendered plots) back into the .ipynb file.

    Parameters
    ----------
    notebook_path : str — path to the unexecuted .ipynb file
    save_dir      : str — working directory (must contain the CSV)

    Returns
    -------
    dict of parsed metrics, or None on failure
    """
    print("→ Executing notebook...")

    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "jupyter", "nbconvert",
                "--to", "notebook",
                "--execute",
                "--inplace",                           # overwrite the same file
                "--ExecutePreprocessor.timeout=60",    # 60s max per cell
                "--ExecutePreprocessor.kernel_name=python3",
                notebook_path
            ],
            cwd=save_dir,
            capture_output=True,
            text=True,
            timeout=120    # total pipeline timeout
        )
    except subprocess.TimeoutExpired:
        print("❌ Notebook execution timed out.")
        return None

    if result.returncode != 0:
        print("❌ Notebook execution failed.")
        print("STDERR:", result.stderr[-2000:])
        return None

    print("✅ Notebook executed successfully.")

    # ------------------------------------------------------------------
    # Extract standalone PNGs from the executed notebook's cell outputs.
    # nbconvert embeds plots as base64 image/png data in the notebook
    # JSON. We decode these and save them as separate files.
    # ------------------------------------------------------------------
    metrics = _extract_outputs(notebook_path, save_dir)
    return metrics


def _extract_outputs(notebook_path: str, save_dir: str) -> dict:
    """
    Open the executed notebook JSON, find image outputs and stdout,
    save images as PNGs, and parse metrics from stdout text.

    Returns parsed metrics dict or None.
    """
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    stdout_text = ""
    image_index = 0

    # Map of expected image filenames in the order they appear
    image_names = ["heatmap.png", "scatter.png", "residual.png"]

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue

        for output in cell.get("outputs", []):
            # Collect all stdout for metric parsing
            if output.get("output_type") in ("stream",) and output.get("name") == "stdout":
                stdout_text += "".join(output.get("text", []))

            # Extract embedded PNG images
            data = output.get("data", {})
            if "image/png" in data:
                png_b64 = data["image/png"]
                if isinstance(png_b64, list):
                    png_b64 = "".join(png_b64)

                # Determine which image this is based on order
                # The notebook saves them in order: heatmap, scatter, residual
                if image_index < len(image_names):
                    img_path = os.path.join(save_dir, image_names[image_index])
                    with open(img_path, "wb") as img_f:
                        img_f.write(base64.b64decode(png_b64))
                    print(f"  ✅ Extracted: {image_names[image_index]}")
                    image_index += 1

    # ------------------------------------------------------------------
    # Parse metrics from the FINAL METRICS block in stdout
    # ------------------------------------------------------------------
    if "DONE" not in stdout_text:
        print("❌ Notebook did not reach the DONE marker — execution may be incomplete.")
        return None

    def extract(key):
        match = re.search(rf"{key}=([\d\.\-]+)", stdout_text)
        return match.group(1) if match else "N/A"

    def extract_str(key):
        match = re.search(rf"{key}=([^\n]+)", stdout_text)
        return match.group(1).strip() if match else "N/A"

    metrics = {
        "r2":          float(extract("SKLEARN_R2"))  if extract("SKLEARN_R2")  != "N/A" else 0.0,
        "mse":         float(extract("SKLEARN_MSE")) if extract("SKLEARN_MSE") != "N/A" else 0.0,
        "mae":         float(extract("SKLEARN_MAE")) if extract("SKLEARN_MAE") != "N/A" else 0.0,
        "ridge_r2":    float(extract("RIDGE_R2"))    if extract("RIDGE_R2")    != "N/A" else 0.0,
        "top_feature": extract_str("TOP_FEATURE"),
        "top_coef":    extract("TOP_COEF"),
    }

    print(f"  ✅ Metrics parsed: R²={metrics['r2']:.4f} | MAE={metrics['mae']:.2f}")

    # Verify all 3 plot files exist
    for img_name in image_names:
        img_path = os.path.join(save_dir, img_name)
        if not os.path.exists(img_path):
            print(f"⚠️  Warning: {img_name} not found — may not have been generated.")

    return metrics
