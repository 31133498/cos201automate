# ============================================================
# pipeline/notebook_runner.py  (Modal version)
#
# Replaces the old local nbconvert call.
# Sends the notebook + CSV to Modal for remote execution,
# receives the executed notebook + PNG bytes back,
# writes them to the student's temp folder,
# and parses metrics from stdout.
#
# Your Render process never loads numpy/sklearn/matplotlib.
# All heavy computation happens inside Modal's container.
# ============================================================

import os
import re
import modal
from pipeline.modal_runner import app, execute_notebook_remote


def run_notebook(notebook_path: str, save_dir: str, csv_path: str) -> dict:
    """
    Execute a notebook remotely on Modal and write outputs locally.

    Parameters
    ----------
    notebook_path : str — path to the unexecuted .ipynb on Render
    save_dir      : str — student's temp folder (for writing outputs)
    csv_path      : str — path to the student's CSV file

    Returns
    -------
    dict of parsed metrics, or None on failure
    """
    print("→ Sending notebook to Modal for remote execution...")

    # Read files as bytes to send over the wire
    with open(notebook_path, "rb") as f:
        notebook_json = f.read()

    csv_filename = os.path.basename(csv_path)
    with open(csv_path, "rb") as f:
        csv_bytes = f.read()

    # Call the Modal remote function
    # .remote() sends it to Modal's cloud — this call blocks until done
    try:
        with app.run():
            result = execute_notebook_remote.remote(
                notebook_json = notebook_json,
                csv_bytes     = csv_bytes,
                csv_filename  = csv_filename,
            )
    except Exception as e:
        print(f"❌ Modal call failed: {e}")
        return None

    if not result["success"]:
        print(f"❌ Remote execution failed:\n{result['error'][-1000:]}")
        return None

    # Write executed notebook back (with embedded outputs)
    with open(notebook_path, "wb") as f:
        f.write(result["executed_nb"])
    print("✅ Executed notebook written back.")

    # Write extracted PNG files
    png_map = {
        "heatmap.png":  result["heatmap_png"],
        "scatter.png":  result["scatter_png"],
        "residual.png": result["residual_png"],
    }

    for fname, data in png_map.items():
        if data:
            fpath = os.path.join(save_dir, fname)
            with open(fpath, "wb") as f:
                f.write(data)
            print(f"  ✅ Extracted: {fname}")
        else:
            print(f"  ⚠️  {fname} not found in notebook outputs")

    # Parse metrics from stdout
    stdout = result["stdout_text"]
    metrics = _parse_metrics(stdout)

    if metrics is None:
        print("❌ Could not parse metrics from notebook output.")
        print("STDOUT tail:", stdout[-500:])
        return None

    print(f"✅ Metrics parsed: R²={metrics['r2']:.4f} | MAE={metrics['mae']:.2f}")
    return metrics


def _parse_metrics(stdout: str) -> dict:
    """Parse the FINAL METRICS block printed by the notebook."""
    if "DONE" not in stdout:
        return None

    def extract_float(key):
        m = re.search(rf"{key}=([\d\.\-]+)", stdout)
        return float(m.group(1)) if m else 0.0

    def extract_str(key):
        m = re.search(rf"{key}=([^\n]+)", stdout)
        return m.group(1).strip() if m else "N/A"

    return {
        "r2":          extract_float("SKLEARN_R2"),
        "mse":         extract_float("SKLEARN_MSE"),
        "mae":         extract_float("SKLEARN_MAE"),
        "ridge_r2":    extract_float("RIDGE_R2"),
        "top_feature": extract_str("TOP_FEATURE"),
        "top_coef":    extract_str("TOP_COEF"),
    }
