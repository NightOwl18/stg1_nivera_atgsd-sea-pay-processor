import os

# Flask Secret Key - required for sessions, flash messages, etc.
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")

# Prefix used when detecting Sailor names in PDFs
NAME_PREFIX = "Name:"

# Marker used to detect the end of each Sailor block
SIGNATURE_MARKER = "SIGNATURE OF CERTIFYING OFFICER"

# Skip all MITE rows (ASW MITE)
SKIP_KEYWORD = "MITE"

PG13_TEMPLATE_PATH = "app/templates_pdf/NAVPERS_1070_613_TEMPLATE.pdf"

# Field names inside the PG-13 form (if you use AcroForm mode)
NAME_FIELD = "NAME"   # Name (LAST, FIRST, MIDDLE)
DATE_FIELD = "Date"   # First remarks line
SHIP_FIELD = "SHIP"   # Second remarks line
