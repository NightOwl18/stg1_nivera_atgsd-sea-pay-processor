import os
import zipfile
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from app.config import PG13_TEMPLATE_PATH


def format_mmddyy(date_obj):
    """Convert date object to MM/DD/YY format."""
    return date_obj.strftime("%m/%d/%y")


def generate_pg13_zip(sailor, output_dir):
    last = sailor["name"].split()[0].upper()
    zip_path = os.path.join(output_dir, f"{last}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for ship, start, end in sailor["events"]:
            pdf_path = make_pg13_pdf(sailor["name"], ship, start, end, output_dir)
            zf.write(pdf_path, os.path.basename(pdf_path))

    return zip_path


def make_pg13_pdf(name, ship, start, end, root_dir):
    output_path = os.path.join(root_dir, f"{ship}.pdf")

    # Load the PG13 PDF template
    reader = PdfReader(PG13_TEMPLATE_PATH)
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)

    # Format fields
    date_value = format_mmddyy(start)  # ONLY ONE DATE AS YOU INSTRUCTED
    ship_value = f"Member performed eight continuous hours per day on-board: {ship} Category A vessel"
    name_value = name

    # Ensure these fields exist before writing
    if writer.get_fields() is None:
        writer._root_object.update({
            "/AcroForm": reader.trailer["/Root"]["/AcroForm"]
        })

    field_updates = {
        "NAME": name_value,
        "Date": date_value,
        "SHIP": ship_value
    }

    writer.update_page_form_field_values(writer.pages[0], field_updates)

    # Save PDF
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
