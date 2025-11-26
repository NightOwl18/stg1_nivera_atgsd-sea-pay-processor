# app/generator.py

import os
import zipfile
from datetime import date

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

from app.config import PG13_TEMPLATE_PATH


def _fmt_mmddyy(d: date) -> str:
    """Return date in MM/DD/YY format."""
    return d.strftime("%m/%d/%y")


def generate_pg13_zip(sailor, output_dir):
    """
    Create a ZIP with one PG-13 PDF per ship for this sailor.

    sailor = {
        "name": "BRANDON ANDERSEN",
        "events": [
            ("PAUL HAMILTON", date_start, date_end),
            ...
        ]
    }
    """
    # Use last name for the zip filename
    last_name = sailor["name"].split()[-1].upper()
    zip_path = os.path.join(output_dir, f"{last_name}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for ship, start, end in sailor["events"]:
            pdf_path = make_pg13_pdf(sailor["name"], ship, start, end, output_dir)
            zf.write(pdf_path, os.path.basename(pdf_path))

    return zip_path


def make_pg13_pdf(name: str, ship: str, start: date, end: date, root_dir: str) -> str:
    """
    Fill the NAVPERS 1070/613 PG-13 template using form fields.

    Fields in the template (from get_fields()):
      - Subject
      - Date
      - SHIP
      - NAME
    """
    # Read the PG-13 template
    reader = PdfReader(PG13_TEMPLATE_PATH)

    # ------------------------------------------------------------------
    # Build the text values we actually want to see on the finished form
    # ------------------------------------------------------------------
    subject_text = f"{_fmt_mmddyy(start)} TO {_fmt_mmddyy(end)}"

    # This line prints exactly after "____.REPORT CAREER SEA PAY FROM"
    date_text = (
        f"____.REPORT CAREER SEA PAY FROM "
        f"{_fmt_mmddyy(start)} TO {_fmt_mmddyy(end)}"
    )

    # Only the ship name – the surrounding sentence is already printed
    # on the form: "Member performed eight continuous hours per day
    # on-board: [SHIP] Category A vessel."
    ship_text = ship

    # Upper-case sailor name for consistency with your example
    name_text = name.upper()

    # ------------------------------------------------------------------
    # Update AcroForm fields directly on the reader
    # ------------------------------------------------------------------
    root = reader.trailer["/Root"]
    acroform = root.get("/AcroForm")

    if acroform is not None:
        fields = acroform.get("/Fields", [])
        for field in fields:
            field_obj = field.get_object()
            fname = field_obj.get("/T")

            if fname == "Subject":
                field_obj.update(
                    {NameObject("/V"): TextStringObject(subject_text)}
                )
            elif fname == "Date":
                field_obj.update(
                    {NameObject("/V"): TextStringObject(date_text)}
                )
            elif fname == "SHIP":
                field_obj.update(
                    {NameObject("/V"): TextStringObject(ship_text)}
                )
            elif fname == "NAME":
                field_obj.update(
                    {NameObject("/V"): TextStringObject(name_text)}
                )

    # ------------------------------------------------------------------
    # Write out a new PDF, preserving the (now-updated) AcroForm
    # ------------------------------------------------------------------
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    if acroform is not None:
        # Re-attach the same AcroForm to the writer
        writer._root_object.update({NameObject("/AcroForm"): acroform})

    output_path = os.path.join(root_dir, f"{ship}.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
