import os
import zipfile
import tempfile
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.extractor import extract_last_name


# --------------------------------------------------------
#   REGISTER FONTS
# --------------------------------------------------------

FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "times.ttf")

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont("TimesNR", FONT_PATH))
else:
    # fallback if font is missing (never recommended)
    pdfmetrics.registerFont(TTFont("TimesNR", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))


# --------------------------------------------------------
#   PG-13 PDF GENERATOR (AcroForm-like manual layout)
# --------------------------------------------------------

def generate_single_pg13(output_path, sailor_name, ship_name, start_date, end_date):
    """
    Create a single PG-13 PDF for one ship & date range.
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setFont("TimesNR", 10)

    # --------------------------------------------------------
    #  HEADER
    # --------------------------------------------------------
    c.drawString(72, 740, "ADMINISTRATIVE REMARKS")
    c.drawString(72, 725, "NAVPERS 1070/613")

    # --------------------------------------------------------
    #  NAME BLOCK
    # --------------------------------------------------------
    c.setFont("TimesNR", 10)
    c.drawString(72, 700, f"NAME (LAST, FIRST, MIDDLE): {sailor_name}")

    # --------------------------------------------------------
    #  SUBJECT LINE
    # --------------------------------------------------------
    c.setFont("TimesNR", 10)
    c.drawString(72, 675, "SUBJECT: SEA PAY CERTIFICATION")

    # --------------------------------------------------------
    #  BODY TEXT
    # --------------------------------------------------------
    c.setFont("TimesNR", 10)
    line_y = 645

    body = (
        f"1. The following member is certified for SEA PAY while assigned to the ship named below.\n"
        f"2. SHIP/STATION: {ship_name}\n"
        f"   PERIOD: {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}\n"
        f"3. This certification is submitted in accordance with DOD 7000.14-R and OPNAVINST 7200.14."
    )

    for line in body.split("\n"):
        c.drawString(72, line_y, line)
        line_y -= 18

    # --------------------------------------------------------
    #  SIGNATURE BLOCK
    # --------------------------------------------------------
    c.drawString(72, line_y - 20, "_______________________________")
    c.drawString(72, line_y - 35, "SIGNATURE OF VERIFYING OFFICIAL & DATE")

    c.showPage()
    c.save()


# --------------------------------------------------------
#   ZIP BUILDER
# --------------------------------------------------------

def generate_pg13_zip(sailor, output_dir=None):
    """
    Takes parsed sailor data:

    sailor = {
        "name": "BRANDON ANDERSEN",
        "events": [
            ("CHOSIN", date(2025,8,11), date(2025,8,13)),
            ...
        ]
    }

    And generates a ZIP containing one PG-13 per ship & date range.
    """

    sailor_name = sailor["name"]
    last_name = extract_last_name(sailor_name)

    # Make temp directory for PDFs
    if output_dir is None:
        output_dir = tempfile.mkdtemp()

    pdf_folder = os.path.join(output_dir, "pg13_output")
    os.makedirs(pdf_folder, exist_ok=True)

    # --------------------------------------------------------
    #  GENERATE ONE PG-13 PER SHIP GROUP
    # --------------------------------------------------------
    for ship, start_date, end_date in sailor["events"]:
        filename = f"{last_name}_{ship}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(pdf_folder, filename)
        generate_single_pg13(filepath, sailor_name, ship, start_date, end_date)

    # --------------------------------------------------------
    #  CREATE ZIP
    # --------------------------------------------------------
    zip_path = os.path.join(output_dir, f"{last_name}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in os.listdir(pdf_folder):
            zf.write(os.path.join(pdf_folder, f), f)

    return zip_path
