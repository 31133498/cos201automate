# ============================================================
# modal_runner.py  (project root — NOT inside pipeline/)
#
# The @app.function is deployed to Modal separately via:
#   modal deploy modal_runner.py
#
# From your Render app (notebook_runner.py), functions are
# called via modal.Function.lookup() — no app.run() needed.
# app.run() is only for the CLI / local testing.
# ============================================================

import os
import modal

app = modal.App("cos201-notebook-runner")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "nbformat==5.9.2",
        "nbconvert==7.16.4",
        "jupyter_client==8.6.2",
        "ipykernel==6.29.4",
        "pandas==2.2.2",
        "numpy==1.26.4",
        "scipy==1.13.1",
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
    # ALL imports inside the function — nothing from pipeline/
    import subprocess, sys, tempfile, os, json, base64

    print(f"Container started. csv={csv_filename} nb={len(notebook_json)}b", flush=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        nb_path  = os.path.join(tmpdir, "notebook.ipynb")
        csv_path = os.path.join(tmpdir, csv_filename)
        with open(nb_path,  "wb") as f: f.write(notebook_json)
        with open(csv_path, "wb") as f: f.write(csv_bytes)

        result = subprocess.run(
            [
                sys.executable, "-m", "jupyter", "nbconvert",
                "--to", "notebook", "--execute", "--inplace",
                "--ExecutePreprocessor.timeout=120",
                "--ExecutePreprocessor.kernel_name=python3",
                "--ExecutePreprocessor.startup_timeout=60",
                nb_path,
            ],
            cwd=tmpdir, capture_output=True, text=True, timeout=150,
            env={**os.environ, "MPLBACKEND": "Agg"},
        )

        print(f"nbconvert exit={result.returncode}", flush=True)
        if result.returncode != 0:
            print("STDERR:", result.stderr[-2000:], flush=True)
            return {"success": False, "error": result.stderr[-3000:],
                    "executed_nb": b"", "heatmap_png": b"",
                    "scatter_png": b"", "residual_png": b"", "stdout_text": result.stdout}


        with open(nb_path, "r", encoding="utf-8") as f:
            executed_nb = f.read()

        nb_data = json.loads(executed_nb)
        stdout_text = ""
        images_dict = {}
        image_names = ["heatmap.png", "scatter.png", "residual.png"]
        image_bytes = {k: b"" for k in image_names}
        image_index = 0

        for cell in nb_data.get("cells", []):
            if cell.get("cell_type") != "code": continue
            for output in cell.get("outputs", []):
                if output.get("output_type") == "stream" and output.get("name") == "stdout":
                    stdout_text += "".join(output.get("text", []))
                data = output.get("data", {})
                if "image/png" in data and image_index < len(image_names):
                    png_b64 = data["image/png"]
                    if isinstance(png_b64, list): png_b64 = "".join(png_b64)
                    image_bytes[image_names[image_index]] = base64.b64decode(png_b64)
                    image_index += 1
        
        for img_name in image_names:
            img_path = os.path.join(tmpdir, img_name)
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    images_dict[img_name] = f.read()
            else:
                images_dict[img_name] = b""

        print(f"Done. images={image_index} stdout={len(stdout_text)}chars", flush=True)
        return {"success": True, "executed_nb": executed_nb,
                "heatmap_png": images_dict["heatmap.png"],
                "scatter_png": images_dict["scatter.png"],
                "residual_png": images_dict["residual.png"],
                "stdout_text": stdout_text, "error": ""}
