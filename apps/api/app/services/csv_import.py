"""Strict, size-limited CSV parsing for submission batches.

Parsing never persists or logs raw APAAR values. The caller is responsible for
sanitising row data before storing it.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Any

from app.security import encrypt_apaar, mask_apaar, normalize_apaar
from app.services.apaar import validate_apaar_format
from app.services.storage import MAX_ROWS, MAX_UPLOAD_BYTES

REQUIRED_HEADERS = (
    "institution_student_id",
    "apaar_id",
    "student_name",
    "programme_code",
    "campus_code",
    "academic_year",
    "admission_date",
    "exit_date",
    "enrollment_status",
    "seat_classification",
    "admission_category",
    "nri_status",
    "oci_status",
    "foreign_national_status",
    "approval_reference",
)
OPTIONAL_HEADERS = ("date_of_birth", "gender")
ALL_HEADERS = (*REQUIRED_HEADERS, *OPTIONAL_HEADERS)


@dataclass
class ParsedCsv:
    headers: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)


def parse_csv(content: bytes) -> ParsedCsv:
    """Parse a UTF-8 CSV with required headers and at most 10,000 data rows."""
    result = ParsedCsv()
    if not content:
        result.errors.append({"code": "EMPTY_FILE", "message": "The uploaded file is empty"})
        return result
    if len(content) > MAX_UPLOAD_BYTES:
        result.errors.append(
            {
                "code": "FILE_TOO_LARGE",
                "message": "CSV uploads are limited to 5 MB",
                "sizeBytes": len(content),
            }
        )
        return result
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        result.errors.append(
            {
                "code": "INVALID_ENCODING",
                "message": "The CSV must be UTF-8 encoded",
            }
        )
        return result

    reader = csv.reader(io.StringIO(text))
    try:
        raw_headers = next(reader)
    except StopIteration:
        result.errors.append({"code": "EMPTY_FILE", "message": "The uploaded file is empty"})
        return result

    headers = [header.strip().lower() for header in raw_headers]
    result.headers = headers
    missing = [header for header in REQUIRED_HEADERS if header not in headers]
    if missing:
        result.errors.append(
            {
                "code": "MISSING_HEADERS",
                "message": "The CSV is missing required columns",
                "missing": missing,
            }
        )
        return result
    duplicates = sorted({header for header in headers if headers.count(header) > 1})
    if duplicates:
        result.errors.append(
            {
                "code": "DUPLICATE_HEADERS",
                "message": "The CSV has duplicate columns",
                "duplicates": duplicates,
            }
        )
        return result

    index = {header: position for position, header in enumerate(headers)}
    for row_number, values in enumerate(reader, start=2):
        if not values or not any(value.strip() for value in values):
            continue
        if len(result.rows) >= MAX_ROWS:
            result.errors.append(
                {
                    "code": "TOO_MANY_ROWS",
                    "message": "Batches are limited to 10,000 data rows",
                    "rowNumber": row_number,
                }
            )
            break
        if len(values) > len(headers):
            result.errors.append(
                {
                    "code": "TOO_MANY_COLUMNS",
                    "message": "A data row has more columns than the header",
                    "rowNumber": row_number,
                }
            )
            continue
        data = {
            header: (values[position].strip() if position < len(values) else "")
            for header, position in index.items()
        }
        result.rows.append({"row_number": row_number, "data": data})

    if not result.rows and not result.errors:
        result.errors.append({"code": "NO_DATA_ROWS", "message": "The CSV contains no data rows"})
    return result


def prepare_row(values: dict[str, str]) -> dict[str, Any]:
    """Return a persistable row with raw APAAR replaced by encrypted evidence.

    The plaintext is used only inside this function (format check and
    encryption). Only the ciphertext, masked fragment and last four digits are
    stored in the JSON column.
    """
    safe: dict[str, Any] = {header: values.get(header, "") for header in ALL_HEADERS}
    raw = normalize_apaar(values.get("apaar_id"))
    state = validate_apaar_format(raw)
    safe.pop("apaar_id", None)
    safe["apaarStatus"] = state["status"]
    safe["apaarMasked"] = mask_apaar(raw)
    safe["apaarLast4"] = (
        raw[-4:] if raw and len(raw) >= 4 and state["status"] == "FORMAT_VALID" else ""
    )
    if state["status"] == "FORMAT_VALID" and raw is not None:
        safe["apaarIdCiphertext"] = encrypt_apaar(raw)
    return safe
