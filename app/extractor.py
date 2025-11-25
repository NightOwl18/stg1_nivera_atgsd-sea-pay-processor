import pdfplumber
import re
from datetime import datetime
from app.config import NAME_PREFIX, SIGNATURE_MARKER, SKIP_KEYWORD


# ---------------------- Helpers ---------------------- #

def parse_date(date_str):
    """Parse M/D/YYYY or M/D/YY."""
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def clean_ship_name(raw):
    """
    Clean the ship name extracted from table columns.
    
    Removes:
    - ASW parentheses
    - times (0000, 2359, 0800, etc.)
    - checkmark 'þ'
    - extra spaces
    """
    if not raw:
        return ""

    raw = raw.replace("þ", " ")

    # Remove parentheses blocks: (ASW C-1), (ASW T-1)
    raw = re.sub(r"\(.*?\)", " ", raw)

    # Remove times
    raw = re.sub(r"\b\d{3,4}\b", " ", raw)

    # Remove asterisks
    raw = raw.replace("*", " ")

    # Collapse multiple spaces
    raw = re.sub(r"\s+", " ", raw)

    return raw.strip().upper()


def group_by_ship(events):
    """
    events: list[(date, ship_name)]
    
    Returns: list[(ship, start_date, end_date)]
    """
    grouped = {}
    for dt, ship in events:
        grouped.setdefault(ship, []).append(dt)

    final = []
    for ship, dates in grouped.items():
        sorted_dates = sorted(dates)
        final.append((ship, sorted_dates[0], sorted_dates[-1]))

    return final


# ---------------------- Core Parser ---------------------- #

def extract_sailors_and_events(pdf_path):
    sailors = []

    current_name = None
    current_events = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:

            text = page.extract_text() or ""
            lines = text.split("\n")

            # 1. Find sailor name
            for line in lines:
                if line.startswith(NAME_PREFIX):
                    extracted = line[len(NAME_PREFIX):].strip()
                    if "SSN" in extracted:
                        extracted = extracted.split("SSN")[0].strip()

                    # Save previous sailor if any
                    if current_name and current_events:
                        sailors.append({
                            "name": current_name,
                            "events": group_by_ship(current_events)
                        })

                    current_name = extracted
                    current_events = []
                    break  # only one name per page

            # 2. Read the table rows (REAL EVENT DATA)
            table = page.extract_table()

            if not table:
                continue

            for row in table:
                if not row:
                    continue

                # table columns often look like:
                # [ DATE , SHIP1 , SHIP2? , STARTTIME , ENDTIME ]
                date_col = row[0]

                # Skip header rows or blank date cells
                if not date_col or not isinstance(date_col, str):
                    continue

                dt = parse_date(date_col.strip())
                if not dt:
                    continue  # not an event row

                # Combine all ship-name fields (Event Column)
                ship_parts = row[1:3]  # usually 2 columns for ship name
                ship_raw = " ".join([p for p in ship_parts if p])

                # Skip empties
                if not ship_raw:
                    continue

                # Skip MITE entirely
                if SKIP_KEYWORD in ship_raw.upper():
                    continue

                ship_clean = clean_ship_name(ship_raw)
                if ship_clean:
                    current_events.append((dt, ship_clean))

            # 3. Detect signature -> end of sailor
            for line in lines:
                if SIGNATURE_MARKER in line and current_name:
                    sailors.append({
                        "name": current_name,
                        "events": group_by_ship(current_events)
                    })
                    current_name = None
                    current_events = []
                    break

    return sailors
