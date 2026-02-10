"""Reads/writes the Excel tracker file using openpyxl."""

import os

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

import config

# Expected column headers (1-indexed)
EXPECTED_HEADERS = {
    1: "Job posting link",
    2: "JD Text",
    3: "Match %",
    4: "3 areas of improvement",
    5: "Referal profile 1",
    6: "Contextual intro",
    7: "Referal profile 2",
    8: "Contextual intro2",
    9: "Referal profile 3",
    10: "Contextual intro3",
}

COLUMN_WIDTHS = {
    1: 40,   # A - Job posting link
    2: 60,   # B - JD Text
    3: 10,   # C - Match %
    4: 50,   # D - 3 areas of improvement
    5: 40,   # E - Referal profile 1
    6: 50,   # F - Contextual intro
    7: 40,   # G - Referal profile 2
    8: 50,   # H - Contextual intro2
    9: 40,   # I - Referal profile 3
    10: 50,  # J - Contextual intro3
}

# Color fills for match percentage
GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
RED_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")


def _ensure_tracker_exists(tracker_path: str) -> None:
    """Create the tracker file with headers if it doesn't exist."""
    if os.path.exists(tracker_path):
        return

    os.makedirs(os.path.dirname(tracker_path), exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Job Tracker"

    # Write headers
    header_font = Font(bold=True)
    for col, header in EXPECTED_HEADERS.items():
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.alignment = Alignment(wrap_text=True)

    # Set column widths
    for col, width in COLUMN_WIDTHS.items():
        col_letter = ws.cell(row=1, column=col).column_letter
        ws.column_dimensions[col_letter].width = width

    wb.save(tracker_path)
    print(f"Created new tracker file: {tracker_path}")


def _migrate_columns_if_needed(ws) -> bool:
    """
    Check if Column B is 'JD Text'. If not, insert it and shift data right.
    Returns True if migration was performed.
    """
    header_b = ws.cell(row=1, column=2).value
    if header_b and str(header_b).strip().lower() == "jd text":
        return False

    # Check if the current Column B header matches one of the old headers
    # (i.e., the file has the old format without JD Text column)
    old_headers_at_b = ["Match %", "match %", "match%"]
    if header_b and str(header_b).strip().lower() not in [h.lower() for h in old_headers_at_b]:
        # Column B exists but isn't "Match %" either — might be something custom
        # Check if it's empty or something unexpected; still insert JD Text
        pass

    print("  Migrating Excel: inserting 'JD Text' column at B and shifting data right...")

    # Insert column at position 2 (shifts everything right)
    ws.insert_cols(2)

    # Set the header for the new column
    ws.cell(row=1, column=2, value="JD Text")
    ws.cell(row=1, column=2).font = Font(bold=True)
    ws.cell(row=1, column=2).alignment = Alignment(wrap_text=True)

    return True


def _apply_formatting(ws) -> None:
    """Apply column widths and text wrapping."""
    for col, width in COLUMN_WIDTHS.items():
        col_letter = ws.cell(row=1, column=col).column_letter
        ws.column_dimensions[col_letter].width = width

    # Wrap text in all cells
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=10):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def read_unprocessed_rows(tracker_path: str = None) -> list[tuple[int, str, str]]:
    """
    Read the Excel tracker and find rows that need processing.

    A row needs processing when:
    - Column A (job link) is non-empty
    - Column B (JD text) is non-empty
    - Column C (Match %) is empty

    Returns list of (row_number, job_link, jd_text) tuples.
    """
    if tracker_path is None:
        tracker_path = config.TRACKER_PATH

    _ensure_tracker_exists(tracker_path)

    try:
        wb = load_workbook(tracker_path)
    except PermissionError:
        raise PermissionError(
            f"Cannot open {tracker_path} — the file may be open in another application.\n"
            "Please close it and try again."
        )

    ws = wb.active

    # Migrate columns if needed
    migrated = _migrate_columns_if_needed(ws)
    if migrated:
        _apply_formatting(ws)
        wb.save(tracker_path)
        print(f"  Column migration complete. Saved to {tracker_path}")
        print("  Please paste job description text into the new 'JD Text' column (B).")

    unprocessed = []
    for row in range(2, ws.max_row + 1):  # Skip header row
        job_link = ws.cell(row=row, column=1).value
        jd_text = ws.cell(row=row, column=2).value
        match_pct = ws.cell(row=row, column=3).value

        # Row needs processing if link + JD text present but no match %
        if job_link and str(job_link).strip():
            if jd_text and str(jd_text).strip():
                if not match_pct or not str(match_pct).strip():
                    unprocessed.append((row, str(job_link).strip(), str(jd_text).strip()))
            else:
                print(f"  Row {row}: JD text is empty, skipping. Paste the job description in Column B.")

    wb.close()
    return unprocessed


def write_results(row_number: int, results: dict, tracker_path: str = None) -> None:
    """
    Write processing results to the Excel tracker for a specific row.

    Args:
        row_number: The Excel row number to write to.
        results: dict with keys:
            - match_percentage (int)
            - improvements (str)
            - referrals (list of 3 dicts with name, title, url)
            - messages (list of 3 strings)
        tracker_path: Path to the Excel file.
    """
    if tracker_path is None:
        tracker_path = config.TRACKER_PATH

    try:
        wb = load_workbook(tracker_path)
    except PermissionError:
        raise PermissionError(
            f"Cannot open {tracker_path} — the file may be open in another application.\n"
            "Please close it and try again."
        )

    ws = wb.active

    # Column C: Match %
    match_pct = results.get("match_percentage", 0)
    cell_c = ws.cell(row=row_number, column=3, value=f"{match_pct}%")
    if match_pct >= 70:
        cell_c.fill = GREEN_FILL
    elif match_pct >= 50:
        cell_c.fill = YELLOW_FILL
    else:
        cell_c.fill = RED_FILL

    # Column D: 3 areas of improvement
    improvements = results.get("improvements", [])
    improvements_text = "\n".join(improvements) if isinstance(improvements, list) else str(improvements)
    ws.cell(row=row_number, column=4, value=improvements_text)

    # Columns E-J: Referrals and messages
    referrals = results.get("referrals", [])
    messages = results.get("messages", [])

    for i in range(3):
        ref_col = 5 + (i * 2)   # E=5, G=7, I=9
        msg_col = 6 + (i * 2)   # F=6, H=8, J=10

        if i < len(referrals):
            ref = referrals[i]
            ref_text = f"{ref['name']} | {ref['title']}\n{ref['url']}"
            ws.cell(row=row_number, column=ref_col, value=ref_text)
        else:
            ws.cell(row=row_number, column=ref_col, value="No profile found")

        if i < len(messages):
            ws.cell(row=row_number, column=msg_col, value=messages[i])
        else:
            ws.cell(row=row_number, column=msg_col, value="N/A")

    # Apply formatting
    for col in range(1, 11):
        ws.cell(row=row_number, column=col).alignment = Alignment(wrap_text=True, vertical="top")

    # Save after each row
    wb.save(tracker_path)
    wb.close()
