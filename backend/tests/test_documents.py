import io
from unittest.mock import patch


def _fake_pdf_bytes() -> bytes:
    """Minimal valid PDF file for upload tests."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer<</Root 1 0 R/Size 4>>\n"
        b"startxref\n0\n%%EOF"
    )


def test_upload_requires_authentication(client):
    response = client.post(
        "/documents/",
        files={"file": ("test.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf")},
    )
    assert response.status_code == 401


def test_upload_rejects_non_pdf(client, auth_headers):
    response = client.post(
        "/documents/",
        headers=auth_headers,
        files={"file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")},
    )
    assert response.status_code == 400


def test_upload_accepts_pdf_and_enqueues(client, auth_headers):
    # Patch the queue so no real background job runs during the test.
    with patch("app.api.documents.task_queue") as mock_queue:
        response = client.post(
            "/documents/",
            headers=auth_headers,
            files={"file": ("test.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf")},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["status"] == "pending"
    mock_queue.enqueue.assert_called_once()


def test_list_documents_scoped_to_user(client, auth_headers):
    response = client.get("/documents/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []  # new user has no documents


def test_get_nonexistent_document_returns_404(client, auth_headers):
    response = client.get(
        "/documents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404