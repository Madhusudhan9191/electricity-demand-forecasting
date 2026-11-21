"""
Package Tableau Workbook (.twb) and exported CSV data extracts into a standalone .twbx archive.
Removes all absolute file paths so the workbook is 100% portable across any machine.
"""

import os
import re
import zipfile
import shutil

TWB_FILE = "Book1.twb"
OUTPUT_TWBX = "electricity_demand_forecasting.twbx"
EXPORTS_DIR = "data/exports"

if not os.path.exists(TWB_FILE):
    print(f"Warning: {TWB_FILE} not found.")
    exit(0)

with open(TWB_FILE, "r", encoding="utf-8", errors="ignore") as f:
    xml_content = f.read()

# Replace any local absolute drive paths with relative references
# e.g. [Drive]:/.../data/exports/tableau_hourly_forecasts.csv -> Data/tableau_hourly_forecasts.csv
clean_xml = re.sub(r'[A-Za-z]:/[^<"\']*/data/exports/([^<"\']+)', r'Data/\1', xml_content)
clean_xml = re.sub(r'[A-Za-z]:\\[^<"\']*\\[dD]ata\\[eE]xports\\([^<"\']+)', r'Data/\1', clean_xml)

temp_twb = "temp_clean_workbook.twb"
with open(temp_twb, "w", encoding="utf-8") as f:
    f.write(clean_xml)

# Create .twbx zip archive
with zipfile.ZipFile(OUTPUT_TWBX, "w", zipfile.ZIP_DEFLATED) as zf:
    # 1. Add workbook XML as base .twb inside archive
    zf.write(temp_twb, arcname="electricity_demand_forecasting.twb")
    
    # 2. Add data extracts under Data/
    for root, dirs, files in os.walk(EXPORTS_DIR):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(root, file)
                archive_name = f"Data/{file}"
                zf.write(file_path, arcname=archive_name)
                print(f"  Bundled {file} -> {archive_name}")

if os.path.exists(temp_twb):
    os.remove(temp_twb)

print(f"\nSuccessfully generated standalone packaged Tableau workbook: {OUTPUT_TWBX} ({os.path.getsize(OUTPUT_TWBX):,} bytes).")
