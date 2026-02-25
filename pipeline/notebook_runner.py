# ============================================================
# pipeline/notebook_runner.py
# Compatible with all Modal versions.
# ============================================================

import os
import re
import sys

# Ensure project root on path so modal_runner imports cleanly
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import modal


def _get_fn():
    """
    Get the deployed Modal function.
    Compatible with all Modal versions.
    """

    # New API
    if hasattr(modal.Function, "from_name"):
        return modal.Function.from_name(
            "cos201-notebook-runner",
            "execute_notebook_remote"
        )

    # Mid API
    if hasattr(modal.Function, "lookup"):
        return modal.Function.lookup(
            "cos201-notebook-runner",
            "execute_notebook_remote"
        )

    # Old API
    try:
        functions_mod = getattr(modal, "functions", None)
        if functions_mod and hasattr(functions_mod, "FunctionHandle"):
            return functions_mod.FunctionHandle.lookup(
                "cos201-notebook-runner",
                "execute_notebook_remote"
            )
    except Exception:
        pass

    raise RuntimeError(
        f"Cannot find Modal function lookup API. Modal version: {modal.__version__}"
    )


def spawn_notebook_execution(notebook_path: str, save_dir: str, csv_path: str) -> str:
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook_text = f.read()
    import json
    json.loads(notebook_text)

    notebook_json = notebook_text.encode("utf-8")
    csv_filename = os.path.basename(csv_path)
    with open(csv_path, "rb") as f:
        csv_bytes = f.read()

    print(f"→ Spawning Modal (modal version: {modal.__version__})...", flush=True)

    fn   = _get_fn()
    call = fn.spawn(notebook_json=notebook_json, csv_bytes=csv_bytes, csv_filename=csv_filename)
    call_id = call.object_id
    print(f"  Modal call_id: {call_id}", flush=True)
    return call_id


def collect_notebook_result(call_id: str, notebook_path: str, save_dir: str):
    try:
        call   = modal.functions.FunctionCall.from_id(call_id)
        result = call.get(timeout=0)
    except TimeoutError:
        return "pending"
    except Exception as e:
        print(f"❌ Modal collect error: {e}", flush=True)
        return None

    if not result["success"]:
        print(f"❌ Notebook failed:\n{result['error'][-800:]}", flush=True)
        return None

    with open(notebook_path, "w", encoding="utf-8") as f:
        f.write(result["executed_nb"])
    print("✅ Executed notebook received.", flush=True)

    for fname, key in [("heatmap.png","heatmap_png"),("scatter.png","scatter_png"),("residual.png","residual_png")]:
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

    print(f"✅ Metrics: R²={metrics['r2']:.4f}  MAE={metrics['mae']:.2f}", flush=True)
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
