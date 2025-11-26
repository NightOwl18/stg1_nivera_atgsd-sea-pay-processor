import os
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from app.config import PG13_TEMPLATE_PATH


def format_mmddyy(date_obj):
    return date_obj.strftime("%m/%d/%y")


def generate_pg13_zip(sailor, output_dir):
    last = sailor["name"].split()[0].upper()
    zip_path = os.path.join(output_dir, f"{last}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for ship, start, end in sailor["events"]:
            pdf_path = make_pg13_pdf(sailor["name"], ship, start, end, output_dir)
            zf.write(pdf_path, os.path.basename(pdf_path))

    return zip_path


def make_overlay(name, ship, date_str, overlay_path):
    """
    Create a transparent overlay PDF with text placed EXACTLY where it needs to go
    on the PG-13 form.
    """

    c = canvas.Canvas(overlay_path, pagesize=letter)

    # -------------------------------
    # TEXT POSITIONS ON PG-13 FORM
    # (Measured from your uploaded PG13 TEMPLATE)
    # -------------------------------

    # 1. Date goes after "____.REPORT CAREER SEA PAY FROM"
    c.drawString(1.65 * inch, 8.05 * inch, date_str)

    # 2. Ship name goes in the middle paragraph
    c.drawString(2.15 * inch, 7.40 * inch, ship)

    # 3. Sailor Name goes in NAME (LAST, FIRST, MIDDLE)
    c.drawString(2.80 * inch, 5.70 * inch, name)

    c.save()


def make_pg13_pdf(name, ship, start, end, output_dir):
    date_str = format_mmddyy(start)

    overlay_path = os.path.join(output_dir, "overlay.pdf")
    output_path = os.path.join(output_dir, f"{ship}.pdf")

    # Create overlay PDF
    make_overlay(name, ship, date_str, overlay_path)

    # Read template + overlay
    template_reader = PdfReader(PG13_TEMPLATE_PATH)
    overlay_reader = PdfReader(overlay_path)

    template_page = template_reader.pages[0]
    overlay_page = overlay_reader.pages[0]

    # Merge overlay onto template
    template_page.merge_page(overlay_page)

    # Write final PDF
    writer = PdfWriter()
    writer.add_page(template_page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
