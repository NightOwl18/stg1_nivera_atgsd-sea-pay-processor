import pdfplumber
import re
from datetime import datetime
from app.config import NAME_PREFIX, SIGNATURE_MARKER, SKIP_KEYWORD


def parse_date(date_str):
    """Parse M/D/YYYY or M/D/YY."""
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def clean_event_name(raw):
    """
    Cleans a fully merged event string:

    Handles:
    - Multi-line names ("PAUL HAMILTON")
    - Checkmarks (þ)
    - Times (0000 2359)
    - Parentheses (ASW T-1)
    - Extra spacing
    - Asterisks
    """

    raw = raw.replace("þ", " ")

    # Remove parentheses like (ASW C-1)
    raw = re.sub(r"\(.*?\)", " ", raw)

    # Remove times like 0000 2359
    raw = re.sub(r"\b\d{3,4}\b", " ", raw)

    # Remove asterisks
    raw = raw.replace("*", " ")

    # Collapse whitespace
    raw = re.sub(r"\s+", " ", raw)

    return raw.strip().upper()


def group_events_by_ship(events):
    """
    events: list[(date, merged_raw_event)]
    Combine all entries for each ship into (ship, first_date, last_date)
    """
    grouped = {}

    for dt, raw in events:
        ship = clean_event_name(raw)
        if not ship:
            continue
        grouped.setdefault(ship, []).append(dt)

    final = []
    for ship, ship_dates in grouped.items():
        ship_dates.sort()
        final.append((ship, ship_dates[0], ship_dates[-1]))

    return final


def extract_sailors_and_events(pdf_path):
    """
    Returns:
    [
      {
        "name": "FRANK HATTEN",
        "events": [
            ("PAUL HAMILTON", start, end),
            ("CHOSIN", start, end),
            ("ASHLAND", start, end)
        ]
      }
    ]
    """

    sailors = []

    current_name = None
    current_events = []

    pending_event = ""   # holds merged event text
    pending_date = None  # holds the date of the current event block

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = (page.extract_text() or "").split("\n")

            for raw_line in lines:
                line = raw_line.strip()

                # 1. Detect sailor NAME line
                if line.startswith(NAME_PREFIX):
                    # Extract name before "SSN"
                    after = line[len(NAME_PREFIX):].strip()
                    if "SSN" in after:
                        current_name = after.split("SSN", 1)[0].strip()
                    else:
                        current_name = after.strip()

                    # Save previous sailor
                    if current_events:
                        sailors.append({
                            "name": current_saved_name,
                            "events": group_events_by_ship(current_events)
                        })

                    current_saved_name = current_name
                    current_events = []
                    pending_event = ""
                    pending_date = None
                    continue

                # 2. Detect new EVENT START (starts with a date)
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    date_candidate, rest = parts
                    dt = parse_date(date_candidate)

                    if dt:
                        # Save previous event if one exists
                        if pending_date and pending_event:
                            current_events.append((pending_date, pending_event.strip()))

                        # Begin new event block
                        pending_date = dt
                        pending_event = rest.strip()
                        continue

                # 3. Continuation lines for the same event
                if pending_date:
                    pending_event += " " + line
                    continue

                # 4. Detect SIGNATURE → end of sailor
                if SIGNATURE_MARKER in line and current_saved_name:
                    if pending_date and pending_event:
                        current_events.append((pending_date, pending_event.strip()))

                    sailors.append({
                        "name": current_saved_name,
                        "events": group_events_by_ship(current_events)
                    })

                    current_saved_name = None
                    current_events = []
                    pending_event = ""
                    pending_date = None

    return sailors
