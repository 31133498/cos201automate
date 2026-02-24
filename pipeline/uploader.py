# ============================================================
# pipeline/uploader.py
#
# Uploads all student files to Cloudinary.
#
# Free tier: 25 GB storage, 25 GB bandwidth/month.
# More than sufficient for 50 students.
#
# Upload rules:
#   - PNG files  → resource_type="image"
#   - All others → resource_type="raw"
#     (this includes .zip, .ipynb, .csv, .txt)
#
# All files go into folder: cos201/{matric_no}/
# This keeps the Cloudinary dashboard organised.
# ============================================================

import cloudinary
import cloudinary.uploader
import os
from config import (
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
)

# Configure Cloudinary once at import time
cloudinary.config(
    cloud_name = CLOUDINARY_CLOUD_NAME,
    api_key    = CLOUDINARY_API_KEY,
    api_secret = CLOUDINARY_API_SECRET,
    secure     = True
)


def upload_all(matric_no: str, save_dir: str, zip_filename: str, dataset_info: dict, notebook_name: str) -> dict:
    """
    Upload all deliverable files to Cloudinary.

    Parameters
    ----------
    matric_no    : str  — used as the Cloudinary subfolder name
    save_dir     : str  — temp folder containing all files
    zip_filename : str  — name of the ZIP file
    dataset_info : dict — from dataset_engine.generate_dataset()
    notebook_name: str  — filename of the .ipynb

    Returns
    -------
    dict mapping filename → public Cloudinary URL
    """
    folder = f"cos201/{matric_no}"

    # Define all files to upload and their resource type
    upload_plan = {
        "heatmap.png":              "image",
        "scatter.png":              "image",
        "residual.png":             "image",
        dataset_info["filename"]:   "raw",   # CSV
        notebook_name:              "raw",   # .ipynb
        "defense_guide.txt":        "raw",
        zip_filename:               "raw",
    }

    urls = {}
    for filename, resource_type in upload_plan.items():
        filepath = os.path.join(save_dir, filename)
        if not os.path.exists(filepath):
            print(f"  ⚠️  Skipping upload (not found): {filename}")
            continue

        # Cloudinary public_id cannot have dots — replace with underscore
        public_id = filename.replace(".", "_")

        result = cloudinary.uploader.upload(
            filepath,
            folder        = folder,
            resource_type = resource_type,
            public_id     = public_id,
            overwrite     = True,
            use_filename  = False,
        )

        urls[filename] = result["secure_url"]
        print(f"  ↑ {filename} → uploaded ({resource_type})")

    print(f"✅ All files uploaded to Cloudinary: {folder}/")
    return urls
