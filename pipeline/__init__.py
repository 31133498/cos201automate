# ============================================================
# pipeline/__init__.py
#
# Two-phase pipeline to support non-blocking Modal execution.
#
# Phase 1 — run_pipeline_phase1():
#   Steps 0-2: dataset, AI narrative, build notebook
#   Step  3:   spawn Modal job (non-blocking, returns call_id)
#   Returns call_id + serialised state for phase 2.
#   Worker saves call_id and exits immediately.
#
# Phase 2 — run_pipeline_phase2():
#   Called by modal_poller when Modal result is ready.
#   Steps 4-6: defense guide, package, upload, email.
# ============================================================

import os
import json
import shutil
import tempfile

from pipeline.dataset_engine    import generate_dataset
from pipeline.ai_narrator       import generate_markdown_narrative
from pipeline.notebook_builder  import build_notebook
from pipeline.notebook_runner   import spawn_notebook_execution, collect_notebook_result
from pipeline.defense_guide     import generate_defense_guide
from pipeline.packager          import create_zip
from pipeline.uploader          import upload_all
from pipeline.mailer            import send_email


def log(msg):
    print(msg, flush=True)


# ─── PHASE 1 ─────────────────────────────────────────────────
def run_pipeline_phase1(
    token:        str,
    matric_no:    str,
    student_name: str,
    student_email:str,
    progress_cb=None,
) -> dict:
    """
    Phase 1: local steps + spawn Modal.
    Returns immediately after spawning Modal.

    Returns dict with:
        success       : bool
        call_id       : str  — Modal call ID for phase 2
        pipeline_data : str  — JSON blob for phase 2
        message       : str  — error message if failed
    """

    def step(n, label):
        log(f"\n[STEP {n}] {label}")
        if progress_cb:
            try: progress_cb(n)
            except Exception as e: log(f"  ⚠️  progress_cb: {e}")

    log(f"\n{'='*60}")
    log(f"PIPELINE PHASE 1 — {student_name} ({matric_no})")
    log(f"{'='*60}")

    save_dir = os.path.join(tempfile.gettempdir(), f"cos201_{matric_no}")
    os.makedirs(save_dir, exist_ok=True)

    try:
        # Step 0: Dataset
        step(0, "Generating dataset")
        dataset_info = generate_dataset(matric_no, save_dir)
        log(f"  Theme    : {dataset_info['display_name']}")
        log(f"  Rows     : {dataset_info['n_rows']}")
        log(f"  Target   : {dataset_info['target']}")

        # Step 1: AI narrative
        step(1, "Generating AI narrative (OpenAI)")
        narrative = generate_markdown_narrative(student_name, matric_no, dataset_info)
        preview   = narrative.get("intro", "")[:120].replace("\n", " ")
        log(f"  Preview  : {preview}...")
        log(f"  Keys     : {list(narrative.keys())}")

        # Step 2: Build notebook
        step(2, "Building notebook")
        notebook_path, notebook_name = build_notebook(
            matric_no    = matric_no,
            student_name = student_name,
            dataset_info = dataset_info,
            save_dir     = save_dir,
            narrative    = narrative,
        )
        log(f"  File     : {notebook_name}")

        # Step 3: Spawn Modal (non-blocking)
        step(3, "Spawning Modal execution (non-blocking)")
        csv_path = os.path.join(save_dir, dataset_info["filename"])
        call_id  = spawn_notebook_execution(notebook_path, save_dir, csv_path)
        log(f"  call_id  : {call_id}")
        log("  Worker is free — Modal running in background.")

        # Serialise everything phase 2 needs
        pipeline_data = json.dumps({
            "save_dir":      save_dir,
            "notebook_path": notebook_path,
            "notebook_name": notebook_name,
            "dataset_info":  dataset_info,
            "student_email": student_email,
            "student_name":  student_name,
            "matric_no":     matric_no,
        })

        return {
            "success":       True,
            "call_id":       call_id,
            "pipeline_data": pipeline_data,
        }

    except Exception as e:
        _cleanup(save_dir)
        log(f"❌ Phase 1 error: {e}")
        import traceback; traceback.print_exc()
        return {"success": False, "message": str(e)}


# ─── PHASE 2 ─────────────────────────────────────────────────
def run_pipeline_phase2(
    call_id:       str,
    pipeline_data: str,
    progress_cb=None,
) -> dict:
    """
    Phase 2: called when Modal result is ready.
    Collects result, then runs steps 4-6.

    Returns dict with: success, message, zip_url
    Returns "pending" string if Modal still running.
    """

    def step(n, label):
        log(f"\n[STEP {n}] {label}")
        if progress_cb:
            try: progress_cb(n)
            except Exception as e: log(f"  ⚠️  progress_cb: {e}")

    data          = json.loads(pipeline_data)
    save_dir      = data["save_dir"]
    notebook_path = data["notebook_path"]
    notebook_name = data["notebook_name"]
    dataset_info  = data["dataset_info"]
    student_name  = data["student_name"]
    student_email = data["student_email"]
    matric_no     = data["matric_no"]

    log(f"\n[PHASE 2] Collecting Modal result — call_id: {call_id}")

    # Check Modal — returns "pending" / None / metrics dict
    metrics = collect_notebook_result(call_id, notebook_path, save_dir)

    if metrics == "pending":
        log("  Modal still running — will check again.")
        return "pending"

    if metrics is None:
        _cleanup(save_dir)
        return {"success": False, "message": "Notebook execution failed on Modal."}

    log(f"  R²={metrics['r2']:.4f}  MAE={metrics['mae']:.2f}")

    try:
        # Step 4: Defense guide
        step(4, "Generating defense guide")
        generate_defense_guide(save_dir, student_name, matric_no, dataset_info, metrics)

        # Step 5: Package + upload
        step(5, "Packaging and uploading to Cloudinary")
        zip_path, zip_filename = create_zip(matric_no, save_dir, dataset_info, notebook_name)
        urls = upload_all(matric_no, save_dir, zip_filename, dataset_info, notebook_name)

        if zip_filename not in urls:
            _cleanup(save_dir)
            return {"success": False, "message": "File upload failed."}

        zip_url = urls[zip_filename]
        log(f"  ZIP URL  : {zip_url}")

        # Step 6: Email
        step(6, "Sending email")
        sent = send_email(student_name, student_email, zip_url, dataset_info, metrics)
        _cleanup(save_dir)

        if not sent:
            return {
                "success": True,
                "message": "Files ready but email failed. Use the download button.",
                "zip_url": zip_url,
            }

        log(f"\n🎉 PIPELINE COMPLETE — {student_name}")
        return {
            "success": True,
            "message": f"Assignment delivered to {student_email}. Check your inbox.",
            "zip_url": zip_url,
        }

    except Exception as e:
        _cleanup(save_dir)
        log(f"❌ Phase 2 error: {e}")
        import traceback; traceback.print_exc()
        return {"success": False, "message": str(e)}


def _cleanup(save_dir: str):
    try:
        shutil.rmtree(save_dir)
        log("✅ Temp folder deleted.")
    except Exception:
        pass
