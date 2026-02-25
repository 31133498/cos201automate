# ============================================================
# pipeline/modal_runner.py
#
# IMPORTANT: The @app.function decorated function is uploaded
# to Modal's container and executed there. Modal serialises
# the function and its imports. This means anything imported
# at MODULE LEVEL in this file will also be imported inside
# the container — and must be available in the container image.
#
# The previous crash: Modal was importing pipeline/__init__.py
# which imported ai_narrator.py which imported openai —
# a package that wasn't installed in the container image.
#
# FIX: This file is now fully self-contained. The function
# body imports only standard library + packages installed
# in the image below. No imports from pipeline/ anywhere.
# ============================================================

import os
import modal

app = modal.App("cos201-notebook-runner")

# Everything the container needs — including openai in case
# Modal ever serialises any surrounding context
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "nbformat==5.9.2",
        "nbconvert==7.16.4",
        "jupyter_client==8.6.2",
        "ipykernel==6.29.4",
        "pandas==2.2.2",
        "numpy==1.26.4",
        "statsmodels==0.14.2",
        "scikit-learn==1.5.0",
        "matplotlib==3.9.0",
        "seaborn==0.13.2",
    )
    .run_commands(
        "python -m ipykernel install --user --name python3 --display-name 'Python 3'",
    )
    .env({"MPLBACKEND": "Agg"})
)


@app.function(
    image   = image,
    timeout = 180,
    memory  = 1024,
    retries = modal.Retries(max_retries=1, backoff_coefficient=1.0, initial_delay=5.0),
)
def execute_notebook_remote(notebook_json: bytes, csv_bytes: bytes, csv_filename: str) -> dict:
    """
    Executes a Jupyter notebook inside a Modal container.
    ALL imports are inside the function body — nothing from
    pipeline/ is imported here. Fully self-contained.
    """
    # ── Standard library only — always available ──────────────
    import subprocess
    import sys
    import tempfile
    import os
    import json
    import base64
    # ── Packages installed in image above ─────────────────────
    # (imported lazily inside function, not at module level)

    print(f"Container started. csv={csv_filename} nb={len(notebook_json)}b", flush=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        nb_path  = os.path.join(tmpdir, "notebook.ipynb")
        csv_path = os.path.join(tmpdir, csv_filename)

        with open(nb_path,  "wb") as f: f.write(notebook_json)
        with open(csv_path, "wb") as f: f.write(csv_bytes)

        # Confirm kernel is registered
        ks = subprocess.run(["jupyter", "kernelspec", "list"],
                            capture_output=True, text=True)
        print("Kernelspecs:", ks.stdout.strip(), flush=True)

        result = subprocess.run(
            [
                sys.executable, "-m", "jupyter", "nbconvert",
                "--to", "notebook",
                "--execute", "--inplace",
                "--ExecutePreprocessor.timeout=120",
                "--ExecutePreprocessor.kernel_name=python3",
                "--ExecutePreprocessor.startup_timeout=60",
                nb_path,
            ],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=150,
            env={**os.environ, "MPLBACKEND": "Agg"},
        )

        print(f"nbconvert exit={result.returncode}", flush=True)
        if result.returncode != 0:
            print("STDERR:", result.stderr[-2000:], flush=True)
            return {
                "success":      False,
                "error":        result.stderr[-3000:],
                "executed_nb":  b"",
                "heatmap_png":  b"",
                "scatter_png":  b"",
                "residual_png": b"",
                "stdout_text":  result.stdout,
            }

        with open(nb_path, "rb") as f:
            executed_nb = f.read()

        nb_data     = json.loads(executed_nb)
        stdout_text = ""
        image_names = ["heatmap.png", "scatter.png", "residual.png"]
        image_bytes = {k: b"" for k in image_names}
        image_index = 0

        for cell in nb_data.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            for output in cell.get("outputs", []):
                if output.get("output_type") == "stream" and output.get("name") == "stdout":
                    stdout_text += "".join(output.get("text", []))
                data = output.get("data", {})
                if "image/png" in data and image_index < len(image_names):
                    png_b64 = data["image/png"]
                    if isinstance(png_b64, list):
                        png_b64 = "".join(png_b64)
                    image_bytes[image_names[image_index]] = base64.b64decode(png_b64)
                    image_index += 1

        print(f"Done. {image_index} images, {len(stdout_text)} stdout chars", flush=True)

        return {
            "success":      True,
            "executed_nb":  executed_nb,
            "heatmap_png":  image_bytes["heatmap.png"],
            "scatter_png":  image_bytes["scatter.png"],
            "residual_png": image_bytes["residual.png"],
            "stdout_text":  stdout_text,
            "error":        "",
        }


def get_modal_client():
    """Explicit auth client — required when running from Render (no CLI config)."""
    token_id     = os.environ.get("MODAL_TOKEN_ID", "")
    token_secret = os.environ.get("MODAL_TOKEN_SECRET", "")
    if not token_id or not token_secret:
        raise RuntimeError("MODAL_TOKEN_ID or MODAL_TOKEN_SECRET not set in environment")
    return modal.Client.from_credentials(token_id, token_secret)
