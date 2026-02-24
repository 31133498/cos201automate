# ============================================================
# pipeline/__init__.py
#
# Master pipeline function. This is the single entry point
# that app.py calls when a student submits the form.
#
# It chains all 8 steps in order:
#   1. Validate and consume the token
#   2. Create isolated temp folder
#   3. Generate personalized dataset
#   4. Build personalized notebook
#   5. Execute the notebook (renders plots inline)
#   6. Generate defense guide from real metrics
#   7. Zip everything + upload to Cloudinary
#   8. Send email + delete temp folder
# ============================================================

import os
import shutil
import tempfile

from pipeline.dataset_engine  import generate_dataset
from pipeline.notebook_builder import build_notebook
from pipeline.notebook_runner  import run_notebook
from pipeline.defense_guide    import generate_defense_guide
from pipeline.packager         import create_zip
from pipeline.uploader         import upload_all
from pipeline.mailer           import send_email


def run_pipeline(token: str, matric_no: str, student_name: str, student_email: str) -> dict:
    """
    Full pipeline for one student submission.

    Parameters
    ----------
    token         : str — one-time token the student submitted
    matric_no     : str — student's matric number e.g. '190401001'
    student_name  : str — student's full name
    student_email : str — email to deliver the ZIP link to

    Returns
    -------
    dict: {
        success : bool,
        message : str,
        zip_url : str (only present on success)
    }
    """
    print(f"\n{'='*60}")
    print(f"PIPELINE START — {student_name} ({matric_no})")
    print(f"{'='*60}")

    # ------------------------------------------------------------------
    # STEP 1: Token validation
    # Token is marked as used the instant it is validated.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # STEP 2: Create isolated temp folder
    # /tmp/cos201_190401001/ — unique per student, cleaned up at the end
    # ------------------------------------------------------------------
    save_dir = os.path.join(tempfile.gettempdir(), f"cos201_{matric_no}")
    os.makedirs(save_dir, exist_ok=True)
    print(f"→ Working directory: {save_dir}")

    try:
        # ------------------------------------------------------------------
        # STEP 3: Generate dataset
        # ------------------------------------------------------------------
        print("\n[3] Generating dataset...")
        dataset_info = generate_dataset(matric_no, save_dir)

        # ------------------------------------------------------------------
        # STEP 4: Build notebook
        # ------------------------------------------------------------------
        print("\n[4] Building notebook...")
        notebook_path, notebook_name = build_notebook(
            matric_no, student_name, dataset_info, save_dir
        )

        # ------------------------------------------------------------------
        # STEP 5: Execute notebook
        # ------------------------------------------------------------------
        print("\n[5] Executing notebook...")
        metrics = run_notebook(notebook_path, save_dir)
        if metrics is None:
            _cleanup(save_dir)
            return {"success": False, "message": "Notebook execution failed. Please try again or contact support."}

        # ------------------------------------------------------------------
        # STEP 6: Generate defense guide
        # ------------------------------------------------------------------
        print("\n[6] Generating defense guide...")
        generate_defense_guide(save_dir, student_name, matric_no, dataset_info, metrics)

        # ------------------------------------------------------------------
        # STEP 7: Zip + upload
        # ------------------------------------------------------------------
        print("\n[7] Packaging files...")
        zip_path, zip_filename = create_zip(matric_no, save_dir, dataset_info, notebook_name)

        print("\n[7b] Uploading to Cloudinary...")
        urls = upload_all(matric_no, save_dir, zip_filename, dataset_info, notebook_name)

        if zip_filename not in urls:
            _cleanup(save_dir)
            return {"success": False, "message": "File upload failed. Please try again."}

        zip_url = urls[zip_filename]

        # ------------------------------------------------------------------
        # STEP 8: Send email + cleanup
        # ------------------------------------------------------------------
        print("\n[8] Sending email...")
        sent = send_email(student_name, student_email, zip_url, dataset_info, metrics)

        _cleanup(save_dir)

        if not sent:
            # Files are on Cloudinary even if email failed
            return {
                "success": True,
                "message": "Files generated but email delivery failed. Use the link below to download.",
                "zip_url": zip_url
            }

        print(f"\n🎉 Pipeline complete for {student_name}")
        return {
            "success": True,
            "message": f"Assignment delivered successfully to {student_email}. Check your inbox.",
            "zip_url": zip_url
        }

    except Exception as e:
        _cleanup(save_dir)
        print(f"❌ Unexpected error: {e}")
        print(e)
        return {"success": False, "message": f"An unexpected error occurred: {str(e)}"}


def _cleanup(save_dir: str):
    """Delete the temp folder silently."""
    try:
        shutil.rmtree(save_dir)
        print(f"✅ Temp folder deleted.")
    except Exception:
        pass
