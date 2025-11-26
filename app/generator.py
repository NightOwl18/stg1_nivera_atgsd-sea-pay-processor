import os
import zipfile
from datetime import datetime

from PyPDF2 import PdfReader, PdfWriter
from app.config import PG13_TEMPLATE_PATH


def format_mmddyy(date_obj):
    return date_obj.strftime("%m/%d/%y")


def generate_pg13_zip(sailor, output_dir):
    last = sailor["name"].split()[0].upper()
    zip_path = os.path.join(output_dir, f"{last}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for ship, start, end in sailor["events"]:
            pdf_path = make_pg13_pdf(
                sailor["name"], ship, start, end, output_dir
            )
            zf.write(pdf_path, os.path.basename(pdf_path))

    return zip_path


def make_pg13_pdf(name, ship, start, end, root_dir):
    """
    SAFELY fill the PG-13 PDF even if the template has broken AcroForm entries.
    """

    output_path = os.path.join(root_dir, f"{ship}.pdf")

    reader = PdfReader(PG13_TEMPLATE_PATH)
    writer = PdfWriter()

    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)

    # --- CLEAN & REBUILD ACROFORM SAFELY ---
    fields = reader.get_fields() or {}
    writer._root_object.update({
        "/AcroForm": {
            "/Fields": []
        }
    })

    # Re-add only GOOD fields
    for field_key, field_obj in fields.items():
        try:
            writer._root_object["/AcroForm"]["/Fields"].append(
                field_obj.indirect_reference
            )
        except Exception:
            pass  # skip corrupted fields

    # --- BUILD FIELD VALUES ---
    date_str = f"{format_mmddyy(start)} TO {format_mmddyy(end)}. REPORT CAREER SEA PAY FROM"
    ship_str = f"Member performed eight continuous hours per day on-board: {ship} Category A vessel"
    name_str = name

    field_updates = {
        "NAME": name_str,
        "Date": date_str,
        "SHIP": ship_str,
    }

    writer.update_page_form_field_values(writer.pages[0], field_updates)

    # Final write
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
