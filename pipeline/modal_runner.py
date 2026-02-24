# ============================================================
# pipeline/modal_runner.py
#
# Offloads notebook execution to Modal.com serverless.
#
# HOW IT WORKS:
# 1. This file defines a Modal "app" with an @app.function
#    decorated function called execute_notebook_remote().
# 2. When called from notebook_runner.py, Modal:
#    a. Spins up a fresh container in the cloud
#    b. Installs the required packages
#    c. Receives the notebook JSON + CSV bytes over the wire
#    d. Writes them to a temp dir inside the container
#    e. Runs nbconvert --execute
#    f. Reads back the executed notebook + PNG files
#    g. Returns everything as bytes back to your Render app
# 3. Your Render app writes the files locally and continues.
#
# MEMORY: Modal container uses its OWN memory (separate from
# Render). Your Render process only holds the file bytes
# during transfer — typically under 5MB.
#
# COST: ~$0.003 per execution. 50 students = $0.15 total.
# Modal free tier gives $30/month credit.
#
# SETUP:
# 1. Sign up at modal.com
# 2. Settings → API Tokens → create token
# 3. Add MODAL_TOKEN_ID and MODAL_TOKEN_SECRET to .env
#    and Render environment variables.
# ============================================================

import modal
import os

# Define the Modal app
app = modal.App("cos201-notebook-runner")

# Container image — installs everything needed to run the notebook
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install([
        "nbformat",
        "nbconvert",
        "jupyter",
        "ipykernel",
        "pandas",
        "numpy",
        "statsmodels",
        "scikit-learn",
        "matplotlib",
        "seaborn",
    ])
    .run_commands(
        # Register ipython kernel so nbconvert can find it
        "python -m ipykernel install --sys-prefix"
    )
)


@app.function(
    image   = image,
    timeout = 180,       # 3 minutes max — plenty for notebook execution
    memory  = 1024,      # 1GB RAM inside Modal container
)
def execute_notebook_remote(notebook_json: bytes, csv_bytes: bytes, csv_filename: str) -> dict:
    """
    Execute a notebook inside a Modal cloud container.

    Parameters (sent from Render)
    ----------
    notebook_json : bytes — the .ipynb file contents
    csv_bytes     : bytes — the student's CSV dataset
    csv_filename  : str   — e.g. 'housing_market.csv'

    Returns (sent back to Render)
    ----------
    dict with:
        success         : bool
        executed_nb     : bytes  — the executed .ipynb with outputs embedded
        heatmap_png     : bytes  — extracted PNG (may be empty b'' if not found)
        scatter_png     : bytes
        residual_png    : bytes
        stdout_text     : str    — all stdout from all cells combined
        error           : str    — error message if success=False
    """
    import subprocess
    import sys
    import tempfile
    import os
    import json
    import base64

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write notebook and CSV into the temp dir
        nb_path  = os.path.join(tmpdir, "notebook.ipynb")
        csv_path = os.path.join(tmpdir, csv_filename)

        with open(nb_path,  "wb") as f: f.write(notebook_json)
        with open(csv_path, "wb") as f: f.write(csv_bytes)

        # Execute the notebook in-place
        result = subprocess.run(
            [
                sys.executable, "-m", "jupyter", "nbconvert",
                "--to", "notebook",
                "--execute",
                "--inplace",
                "--ExecutePreprocessor.timeout=120",
                "--ExecutePreprocessor.kernel_name=python3",
                nb_path,
            ],
            cwd           = tmpdir,
            capture_output = True,
            text           = True,
            timeout        = 150,
        )

        if result.returncode != 0:
            return {
                "success":     False,
                "error":       result.stderr[-3000:],
                "executed_nb": b"",
                "heatmap_png": b"",
                "scatter_png": b"",
                "residual_png": b"",
                "stdout_text": "",
            }

        # Read executed notebook
        with open(nb_path, "rb") as f:
            executed_nb = f.read()

        # Extract PNGs and stdout from notebook cell outputs
        nb_data     = json.loads(executed_nb)
        stdout_text = ""
        image_names = ["heatmap.png", "scatter.png", "residual.png"]
        image_bytes = {"heatmap.png": b"", "scatter.png": b"", "residual.png": b""}
        image_index = 0

        for cell in nb_data.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            for output in cell.get("outputs", []):
                # Collect stdout
                if output.get("output_type") == "stream" and output.get("name") == "stdout":
                    stdout_text += "".join(output.get("text", []))
                # Extract embedded PNGs
                data = output.get("data", {})
                if "image/png" in data and image_index < len(image_names):
                    png_b64 = data["image/png"]
                    if isinstance(png_b64, list):
                        png_b64 = "".join(png_b64)
                    image_bytes[image_names[image_index]] = base64.b64decode(png_b64)
                    image_index += 1

        return {
            "success":     True,
            "executed_nb": executed_nb,
            "heatmap_png": image_bytes["heatmap.png"],
            "scatter_png": image_bytes["scatter.png"],
            "residual_png": image_bytes["residual.png"],
            "stdout_text": stdout_text,
            "error":       "",
        }
