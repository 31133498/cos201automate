# ============================================================
# pipeline/notebook_runner.py
#
# Uses get_modal_client() for explicit token auth.
# This is what makes it work from Render (no CLI config).
# ============================================================

import os
import re
import modal
from pipeline.modal_runner import app, execute_notebook_remote, get_modal_client


def spawn_notebook_execution(notebook_path: str, save_dir: str, csv_path: str) -> str:
    """Spawn Modal job, return call_id immediately (non-blocking)."""
    with open(notebook_path, "rb") as f:
        notebook_json = f.read()
    csv_filename = os.path.basename(csv_path)
    with open(csv_path, "rb") as f:
        csv_bytes = f.read()

    print("→ Spawning Modal (non-blocking)...", flush=True)

    # Use explicit client — required on Render
    client = get_modal_client()
    with app.run(client=client):
        call = execute_notebook_remote.spawn(
            notebook_json=notebook_json,
            csv_bytes=csv_bytes,
            csv_filename=csv_filename,
        )

    call_id = call.object_id
    print(f"  Modal call_id: {call_id}", flush=True)
    return call_id


def collect_notebook_result(call_id: str, notebook_path: str, save_dir: str):
    """
    Non-blocking check — returns:
      "pending" if Modal still running
      None      if failed
      dict      of metrics if successful
    """
    try:
        client = get_modal_client()
        with app.run(client=client):
            call   = modal.functions.FunctionCall.from_id(call_id)
            result = call.get(timeout=0)   # raises TimeoutError if still running

    except TimeoutError:
        return "pending"
    except Exception as e:
        print(f"❌ Modal collect error: {e}", flush=True)
        return None

    if not result["success"]:
        print(f"❌ Notebook execution failed in Modal:\n{result['error'][-800:]}", flush=True)
        return None

    # Write executed notebook
    with open(notebook_path, "wb") as f:
        f.write(result["executed_nb"])
    print("✅ Executed notebook received.", flush=True)

    # Write PNGs
    for fname, key in [("heatmap.png","heatmap_png"), ("scatter.png","scatter_png"), ("residual.png","residual_png")]:
        data = result.get(key, b"")
        if data:
            with open(os.path.join(save_dir, fname), "wb") as f:
                f.write(data)
            print(f"  ✅ {fname}", flush=True)
        else:
            print(f"  ⚠️  {fname} missing", flush=True)

    metrics = _parse_metrics(result.get("stdout_text", ""))
    if metrics is None:
        print("❌ Metrics not found in stdout.", flush=True)
        print("Stdout tail:", result.get("stdout_text","")[-500:], flush=True)
        return None

    print(f"✅ Metrics: R²={metrics['r2']:.4f} MAE={metrics['mae']:.2f}", flush=True)
    return metrics


def _parse_metrics(stdout: str) -> dict:
    if "DONE" not in stdout:
        return None

    def ef(key):
        m = re.search(rf"{key}=([\d\.\-]+)", stdout)
        return float(m.group(1)) if m else 0.0

    def es(key):
        m = re.search(rf"{key}=([^\n]+)", stdout)
        return m.group(1).strip() if m else "N/A"

    return {
        "r2":          ef("SKLEARN_R2"),
        "mse":         ef("SKLEARN_MSE"),
        "mae":         ef("SKLEARN_MAE"),
        "ridge_r2":    ef("RIDGE_R2"),
        "top_feature": es("TOP_FEATURE"),
        "top_coef":    es("TOP_COEF"),
    }
