import pytest
from fastapi.testclient import TestClient

from app.main import MAX_MESSAGE_LENGTH, app

client = TestClient(app)


def test_analyze_returns_structured_findings():
    response = client.post(
        "/analyze",
        json={"message": "URGENT: Share your OTP to keep your account active."},
    )

    assert response.status_code == 200
    body = response.json()
    # No verdict or probability fields: only findings and the notice.
    assert set(body) == {"findings", "notice"}
    assert [finding["category"] for finding in body["findings"]] == [
        "urgency_pressure",
        "credential_request",
    ]
    for finding in body["findings"]:
        assert set(finding) == {"category", "explanation", "evidence"}
    assert "cannot determine whether a message is fraudulent" in body["notice"]


def test_analyze_payment_demand_with_url():
    response = client.post(
        "/analyze",
        json={"message": "Pay Rs 500 customs fee to release your parcel: http://bit.ly/parcel-fee"},
    )

    assert response.status_code == 200
    assert [finding["category"] for finding in response.json()["findings"]] == [
        "link",
        "payment_demand",
    ]


def test_analyze_benign_message_returns_no_findings_but_keeps_notice():
    response = client.post(
        "/analyze",
        json={"message": "Hi, are we still meeting for lunch at 1 pm tomorrow?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["findings"] == []
    assert "may still be a scam" in body["notice"]


@pytest.mark.parametrize("message", ["", "   ", "\n\t  "])
def test_analyze_rejects_blank_message(message):
    response = client.post("/analyze", json={"message": message})

    assert response.status_code == 422


@pytest.mark.parametrize("payload", [{}, {"message": None}, {"message": 123}])
def test_analyze_rejects_missing_or_non_string_message(payload):
    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_accepts_message_at_maximum_length():
    response = client.post("/analyze", json={"message": "a" * MAX_MESSAGE_LENGTH})

    assert response.status_code == 200


def test_analyze_rejects_message_over_maximum_length():
    response = client.post("/analyze", json={"message": "a" * (MAX_MESSAGE_LENGTH + 1)})

    assert response.status_code == 422
