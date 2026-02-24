# ============================================================
# pipeline/packager.py
#
# Zips all student deliverables into one archive.
# The ZIP is named after the dataset theme, not the student.
#
# Contents every ZIP always includes:
#   - {theme}.csv           — their unique dataset
#   - {theme}_regression.ipynb — pre-executed notebook
#   - heatmap.png           — correlation heatmap
#   - scatter.png           — actual vs predicted plot
#   - residual.png          — residual analysis plot
#   - defense_guide.txt     — viva preparation guide
# ============================================================

import zipfile
import os


def create_zip(matric_no: str, save_dir: str, dataset_info: dict, notebook_name: str) -> tuple:
    """
    Zip all deliverable files for the student.

    Parameters
    ----------
    matric_no     : str  — student matric number
    save_dir      : str  — temp folder containing all generated files
    dataset_info  : dict — from dataset_engine.generate_dataset()
    notebook_name : str  — filename of the .ipynb e.g. 'housing_market_regression.ipynb'

    Returns
    -------
    (zip_path, zip_filename) tuple
    """
    theme_base   = dataset_info["filename"].replace(".csv", "")
    zip_filename = f"{theme_base}_regression_assignment.zip"
    zip_path     = os.path.join(save_dir, zip_filename)

    # Every ZIP always contains these files
    files_to_zip = [
        dataset_info["filename"],   # CSV
        notebook_name,              # .ipynb
        "heatmap.png",              # Graph 1
        "scatter.png",              # Graph 2
        "residual.png",             # Graph 3
        "defense_guide.txt",        # Defense guide
    ]

    missing = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_zip:
            fpath = os.path.join(save_dir, fname)
            if os.path.exists(fpath):
                zf.write(fpath, arcname=fname)
                print(f"  + {fname}")
            else:
                missing.append(fname)
                print(f"  ⚠️  Skipped (not found): {fname}")

    if missing:
        print(f"⚠️  ZIP created but missing: {missing}")
    else:
        size_kb = os.path.getsize(zip_path) // 1024
        print(f"✅ ZIP created: {zip_filename} ({size_kb} KB)")

    return zip_path, zip_filename
