import re
from datetime import datetime
from typing import Tuple, Optional


def clean_string(val: Optional[str]) -> Optional[str]:
    """Trim leading/trailing whitespace and strip control chars."""
    if val is None:
        return None
    cleaned = str(val).strip()
    return cleaned if cleaned != "" else None


def clean_amount(val: any) -> Tuple[Optional[float], bool]:
    """
    Parses currency string or numeric into positive float and indicates if original was negative.
    Examples:
        "-1500.00" -> (1500.0, True)
        "₹50,000" -> (50000.0, False)
        "100.5" -> (100.5, False)
    """
    if val is None:
        return None, False

    s = str(val).strip()
    if not s:
        return None, False

    is_negative = False
    if s.startswith("-") or "(" in s:
        is_negative = True

    # Strip commas first, then strip out non-digits and non-dots
    s_no_commas = s.replace(",", "")
    cleaned_s = re.sub(r"[^\d.]", "", s_no_commas)
    if not cleaned_s:
        return None, False

    try:
        amount = float(cleaned_s)
        return amount, is_negative
    except ValueError:
        return None, False


def clean_date(val: Optional[str]) -> Optional[str]:
    """
    Standardizes heterogeneous date formats into 'YYYY-MM-DD HH:MM:SS' string.
    Supports formats:
      - 2026-08-15 14:30:00 / 2026-08-15
      - 15/08/2026 14:30:00 / 15/08/2026
      - 15-08-2026 / 15-Aug-2026 / 15 Aug 2026
      - ISO format strings (e.g. 2026-08-15T14:30:00Z)
    """
    if not val:
        return None

    s = str(val).strip()
    if not s:
        return None

    # Replace T in ISO dates
    s_clean = s.replace("T", " ").replace("Z", "")

    date_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
        "%d %b %Y",
        "%d-%b-%Y",
        "%d %B %Y",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(s_clean, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    # Try generic ISO parse if available
    try:
        dt = datetime.fromisoformat(s_clean)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    return None
