import os
import zipfile
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from app.config import PG13_TEMPLATE_PATH


# -----------------------------
# Clean ship name for PG-13
# -----------------------------
def clean_ship(ship):
    # Remove ASW codes, stars, parenthesis, weird symbols
    ship = ship.replace("þ", " ")
    ship = ship.upper()
    for bad in ["ASW", "READ", "E", "AS", "C", "*", "-", "  "]:
        ship = ship.replace(bad, " ")
    ship = ship.replace("(", " ").replace(")", " ")
    ship = " ".join(ship.split())
    return ship.strip()


# -----------------------------
# Generate ZIP containing all PG-13s for one sailor
# -----------------------------
def generate_pg13_zip(sailor, output_dir):
    last = sailor["name"].split()[-1].upper()
    zip_path = os.path.join(output_dir, f"{last}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for ship, start, end in sailor["events"]:
            pdf_path = make_pg13_pdf(sailor["name"], ship, start, end, output_dir)
            zf.write(pdf_path, os.path.basename(pdf_path))

    return zip_path


# -----------------------------
# Generate a single PG-13 PDF
# -----------------------------
def make_pg13_pdf(name, ship_raw, start_date, end_date, root_dir):
    ship = clean_ship(ship_raw)
    out_path = os.path.join(root_dir, f"{ship}.pdf")

    # 1. Load template
    template = PdfReader(PG13_TEMPLATE_PATH)
    base_page = template.pages[0]

    # 2. Create overlay PDF (ReportLab draws text)
    overlay_path = os.path.join(root_dir, "overlay.pdf")
    c = canvas.Canvas(overlay_path, pagesize=letter)

    # -----------------------------
    # PG-13 Fields (Coordinates)
    # -----------------------------
    # NAME field (top of form)
    c.drawString(140, 700, name.upper())

    # DATE FROM/TO line
    c.drawString(140, 660, f"{start_date} TO {end_date}")

    # SHIP field
    c.drawString(140, 620, ship)

    # MAIN PG-13 TEXT
    text = f"""_____. REPORT CAREER SEA PAY FROM {start_date} TO {end_date}

Member performed eight continuous hours per day on-board: {ship}
Category A vessel."""

    text_y = 540
    for line in text.split("\n"):
        c.drawString(80, text_y, line)
        text_y -= 18

    c.save()

    # 3. Merge overlay onto template
    overlay_pdf = PdfReader(overlay_path)
    overlay_page = overlay_pdf.pages[0]

    writer = PdfWriter()

    merged = PageObject.create_blank_page(width=letter[0], height=letter[1])
    merged.merge_page(base_page)
    merged.merge_page(overlay_page)

    writer.add_page(merged)

    with open(out_path, "wb") as f:
        writer.write(f)

    return out_path
