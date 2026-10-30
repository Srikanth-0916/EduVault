"""Upload type, size, row-limit and encoding guards."""

from __future__ import annotations

from app.services.csv_import import ALL_HEADERS
from tests.factories import auth_headers
from tests.helpers import create_batch, upload


def _batch(client):
    operator = auth_headers(client, "operator@demo-ait.edu")
    return operator, create_batch(client, operator)


def test_rejects_non_csv_extension(client, seeded) -> None:
    operator, batch = _batch(client)
    response = upload(client, operator, batch["id"], b"a,b\n1,2\n", name="students.txt")
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_rejects_non_csv_media_type(client, seeded) -> None:
    operator, batch = _batch(client)
    response = client.post(
        f"/api/v1/submission-batches/{batch['id']}/file",
        files={"file": ("students.csv", b"a,b\n1,2\n", "application/json")},
        headers=operator,
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_rejects_file_over_five_megabytes(client, seeded) -> None:
    operator, batch = _batch(client)
    oversize = b"x" * (5 * 1024 * 1024 + 1)
    response = upload(client, operator, batch["id"], oversize)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_rejects_more_than_ten_thousand_rows(client, seeded) -> None:
    operator, batch = _batch(client)
    header = ",".join(ALL_HEADERS).encode() + b"\n"
    rows = b"x,123456789012\n" * 10_001
    response = upload(client, operator, batch["id"], header + rows)
    assert response.status_code == 413
    codes = {item["code"] for item in response.json()["error"]["details"]["errors"]}
    assert "TOO_MANY_ROWS" in codes


def test_rejects_invalid_utf8(client, seeded) -> None:
    operator, batch = _batch(client)
    response = upload(client, operator, batch["id"], b"\xff\xfe\x00\x00")
    assert response.status_code == 422
    codes = {item["code"] for item in response.json()["error"]["details"]["errors"]}
    assert "INVALID_ENCODING" in codes


def test_rejects_duplicate_headers(client, seeded) -> None:
    operator, batch = _batch(client)
    header = ",".join(ALL_HEADERS) + ",institution_student_id\n"
    response = upload(client, operator, batch["id"], header.encode())
    assert response.status_code == 422
    codes = {item["code"] for item in response.json()["error"]["details"]["errors"]}
    assert "DUPLICATE_HEADERS" in codes


def test_accepts_utf8_bom_and_text_plain(client, seeded, sample_csv) -> None:
    operator, batch = _batch(client)
    content = b"\xef\xbb\xbf" + sample_csv("batch_valid.csv")
    response = client.post(
        f"/api/v1/submission-batches/{batch['id']}/file",
        files={"file": ("students.csv", content, "text/plain")},
        headers=operator,
    )
    assert response.status_code == 200, response.text
    assert response.json()["rowCount"] == 4
