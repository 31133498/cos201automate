# ============================================================
# pipeline/__init__.py
# Master pipeline — called by the worker for each job.
# All prints use flush=True so they appear immediately in
# Render logs (PYTHONUNBUFFERED=1 must also be set in env).
# ============================================================

import os
import shutil
import tempfile

from pipeline.dataset_engine    import generate_dataset
from pipeline.ai_narrator       import generate_markdown_narrative
from pipeline.notebook_builder  import build_notebook
from pipeline.notebook_runner   import run_notebook
from pipeline.defense_guide     import generate_defense_guide
from pipeline.packager          import create_zip
from pipeline.uploader          import upload_all
from pipeline.mailer            import send_email


def log(msg):
    """Flushed print so Render logs show lines immediately."""
    print(msg, flush=True)


def run_pipeline(
    token:         str,
    matric_no:     str,
    student_name:  str,
    student_email: str,
    progress_cb=None,   # optional callback(step_index) to update Job.current_step
) -> dict:
    """
    Full pipeline for one student job.
    progress_cb(n) is called before each major step so the
    worker can write current_step to the database and the
    frontend can poll it for real sync.
    """

    def step(n, label):
        log(f"\n[STEP {n}] {label}")
        if progress_cb:
            try:
                progress_cb(n)
            except Exception as e:
                log(f"  ⚠️  progress_cb failed: {e}")

    log(f"\n{'='*60}")
    log(f"PIPELINE START — {student_name} ({matric_no})")
    log(f"{'='*60}")

    save_dir = os.path.join(tempfile.gettempdir(), f"cos201_{matric_no}")
    os.makedirs(save_dir, exist_ok=True)
    log(f"→ Temp dir: {save_dir}")

    try:
        # ── Step 0: Dataset ──────────────────────────────────────
        step(0, "Generating dataset")
        dataset_info = generate_dataset(matric_no, save_dir)
        log(f"  Theme    : {dataset_info['display_name']}")
        log(f"  Rows     : {dataset_info['n_rows']}")
        log(f"  Target   : {dataset_info['target']}")
        log(f"  Features : {dataset_info['features']}")

        # ── Step 1: AI Narrative ─────────────────────────────────
        step(1, "Generating AI narrative (OpenAI)")
        narrative = generate_markdown_narrative(student_name, matric_no, dataset_info)
        # Log a snippet so you can confirm AI is working
        intro_preview = narrative.get("intro", "")[:120].replace("\n", " ")
        log(f"  AI intro preview : {intro_preview}...")
        log(f"  Keys returned    : {list(narrative.keys())}")

        # ── Step 2: Build notebook ───────────────────────────────
        step(2, "Building notebook")
        notebook_path, notebook_name = build_notebook(
            matric_no    = matric_no,
            student_name = student_name,
            dataset_info = dataset_info,
            save_dir     = save_dir,
            narrative    = narrative,
        )
        log(f"  Notebook : {notebook_name}")

        # ── Step 3: Execute on Modal ─────────────────────────────
        step(3, "Executing notebook on Modal")
        csv_path = os.path.join(save_dir, dataset_info["filename"])
        metrics  = run_notebook(notebook_path, save_dir, csv_path)

        if metrics is None:
            _cleanup(save_dir)
            return {
                "success": False,
                "message": "Notebook execution failed on Modal. Please contact support."
            }

        log(f"  R²           : {metrics['r2']:.4f}")
        log(f"  MSE          : {metrics['mse']:.2f}")
        log(f"  MAE          : {metrics['mae']:.2f}")
        log(f"  Ridge R²     : {metrics['ridge_r2']:.4f}")
        log(f"  Top feature  : {metrics['top_feature']}")
        log(f"  Top coef     : {metrics['top_coef']}")

        # ── Step 4: Defense guide ────────────────────────────────
        step(4, "Generating defense guide")
        generate_defense_guide(save_dir, student_name, matric_no, dataset_info, metrics)

        # ── Step 5: Package + upload ─────────────────────────────
        step(5, "Packaging and uploading to Cloudinary")
        zip_path, zip_filename = create_zip(matric_no, save_dir, dataset_info, notebook_name)
        urls = upload_all(matric_no, save_dir, zip_filename, dataset_info, notebook_name)

        if zip_filename not in urls:
            _cleanup(save_dir)
            return {"success": False, "message": "File upload failed. Please try again."}

        zip_url = urls[zip_filename]
        log(f"  ZIP URL : {zip_url}")

        # ── Step 6: Email ────────────────────────────────────────
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
        import traceback
        log(f"❌ PIPELINE ERROR: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"Unexpected error: {str(e)}"}


def _cleanup(save_dir: str):
    try:
        shutil.rmtree(save_dir)
        log("✅ Temp folder deleted.")
    except Exception:
        pass
