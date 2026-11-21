"""
Package Clean Project Submission Zip Archive.
Excludes .git, .venv, venv, __pycache__, .pytest_cache, and temporary files.
Preserves .gitignore and all source, config, data, docs, reports, and models.
"""

import os
import zipfile
from pathlib import Path

OUTPUT_ZIP = "electricity_demand_forecasting_clean.zip"

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".vscode", ".idea", "node_modules"
}
EXCLUDE_EXTS = {
    ".pyc", ".pyo", ".pyd", ".log", ".tmp"
}
EXCLUDE_FILES = {
    OUTPUT_ZIP, "temp_clean_workbook.twb"
}


def build_clean_zip(root_dir=".", output_zip=OUTPUT_ZIP):
    root_path = Path(root_dir).resolve()
    print(f"Creating clean deliverable zip: {output_zip}...")
    
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(root_path):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for f in files:
                if f in EXCLUDE_FILES:
                    continue
                if any(f.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue
                
                file_path = Path(root) / f
                arcname = file_path.relative_to(root_path)
                zf.write(file_path, arcname=str(arcname))
                
    zip_size = os.path.getsize(output_zip)
    print(f"[OK] Clean deliverable created: {output_zip} ({zip_size:,} bytes).")
    print("     Excludes .git, .venv, .pytest_cache, and temporary files.")
    return output_zip


if __name__ == "__main__":
    build_clean_zip()
