import os
import zipfile
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from app.config import PG13_TEMPLATE_PATH


def format_mmddyy(date_obj):
    """Convert date object to MM/DD/YY format."""
    return date_obj.strftime("%m/%d/%y")


def generate_pg13_zip(sailor, output_dir):
    # Use LAST name for zip filename
    last = sailor["name"].split()[0].upper()
    zip_path = os.path.join(output_dir, f"{last}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for ship, start, end in sailor["events"]:
            pdf_path = make_pg13_pdf(sailor["name"], ship, start, end, output_dir)
            zf.write(pdf_path, os.path.basename(pdf_path))

    return zip_path


def make_pg13_pdf(name, ship, start, end, root_dir):
    output_path = os.path.join(root_dir, f"{ship}.pdf")

    # Load template
    reader = PdfReader(PG13_TEMPLATE_PATH)
    writer = PdfWriter()

    # Copy pages first
    for page in reader.pages:
        writer.add_page(page)

    # COPY ACROFORM EXACTLY or fields will NOT exist
    if "/AcroForm" in reader.trailer["/Root"]:
        writer._root_object.update({
            "/AcroForm": reader.trailer["/Root"]["/AcroForm"]
        })

    # Get form fields from READER (NOT writer)
    fields = reader.get_fields()

    # --- Required PG-13 formatting ---
    date_from_to = f"{format_mmddyy(start)} TO {format_mmddyy(end)}"
    ship_text = f"Member performed eight continuous hours per day on-board: {ship} Category A vessel"
    name_text = name

    # Set field values
    writer.update_page_form_field_values(
        writer.pages[0],
        {
            "NAME": name_text,
            "Date": date_from_to,
            "SHIP": ship_text
        }
    )

    # Must set NeedAppearances for fields to display properly
    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"].update({"/NeedAppearances": True})

    # Save output
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
