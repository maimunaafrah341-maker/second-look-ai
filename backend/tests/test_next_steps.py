"""Tests for the fixed "what happened next?" steps."""

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.guidance import CorpusError, GuidanceIndex, load_corpus
from app.main import app
from app.next_steps import ACTIONS, SITUATIONS, resolve

client = TestClient(app)


def body() -> dict:
    response = client.get("/next-steps")
    assert response.status_code == 200
    return response.json()


def test_situations_are_fixed_and_in_order():
    situations = body()["situations"]

    assert [situation["id"] for situation in situations] == [
        "not_responded",
        "clicked_link",
        "shared_details",
        "lost_money",
    ]
    assert len({situation["label"] for situation in situations}) == len(situations)


def test_response_has_exactly_the_documented_fields():
    data = body()

    assert set(data) == {"situations", "notice"}
    for situation in data["situations"]:
        assert set(situation) == {"id", "label", "steps"}
        assert situation["steps"]
        for step in situation["steps"]:
            assert set(step) == {"topic", "summary", "summary_note", "source", "action"}
            assert set(step["source"]) == {"title", "publisher", "url", "published", "retrieved", "section"}


def test_every_step_is_a_verified_passage_with_its_real_source():
    sources, passages = load_corpus()
    verified = {passage.topic: passage for passage in passages if passage.verification_status == "verified"}

    for situation in body()["situations"]:
        for step in situation["steps"]:
            passage = verified[step["topic"]]
            source = sources[passage.source_id]
            assert step["summary"] == passage.summary
            assert step["summary_note"] == main_module.SUMMARY_NOTE
            assert step["source"]["url"] == source.url
            assert step["source"]["publisher"] == source.publisher
            assert step["source"]["section"] == passage.section


def test_steps_match_what_analyze_serves_for_the_same_passage():
    # The reporting step is the same text and source a reporting question retrieves.
    match = client.post("/analyze", json={"message": "I lost money in an online fraud, where do I report it?"}).json()[
        "guidance"
    ]["matches"][0]
    reporting = next(
        step for situation in body()["situations"] for step in situation["steps"] if step["topic"] == match["topic"]
    )

    for key in ("topic", "summary", "summary_note", "source"):
        assert reporting[key] == match[key]


def test_lost_money_puts_reporting_first_with_the_helpline_action():
    lost_money = next(situation for situation in body()["situations"] if situation["id"] == "lost_money")
    first = lost_money["steps"][0]

    assert first["topic"] == "Reporting cybercrime"
    assert first["action"] == {"label": "Call 1930", "href": "tel:1930"}
    assert "1930" in first["summary"]


def test_actions_exist_only_where_the_passage_supports_them():
    for situation in body()["situations"]:
        for step in situation["steps"]:
            if step["action"] is not None:
                # The only action is dialling the helpline named in the passage itself.
                assert step["action"]["href"] == "tel:1930"
                assert "1930" in step["summary"]
    assert set(ACTIONS) == {"report-helpline-1930"}


def test_not_responded_does_not_send_people_to_the_helpline():
    not_responded = next(situation for situation in body()["situations"] if situation["id"] == "not_responded")

    assert all(step["action"] is None for step in not_responded["steps"])


def test_notice_makes_no_promise_and_no_safety_claim():
    notice = body()["notice"]

    assert "official sources" in notice
    assert "does not contact anyone or file a report for you" in notice
    assert "safe" not in notice.lower()


def test_response_is_the_same_every_time_and_takes_no_input():
    assert body() == body()
    assert client.get("/next-steps", params={"message": "share your OTP"}).json() == body()
    assert client.post("/next-steps", json={"message": "x"}).status_code == 405


def test_passages_awaiting_review_are_never_used():
    index = GuidanceIndex.from_file()
    used = {passage_id for situation in SITUATIONS for passage_id in situation.passage_ids}

    assert not any(passage_id.startswith("digital-arrest") for passage_id in used)
    with pytest.raises(CorpusError):
        index.verified_passage("digital-arrest-precautions")
    with pytest.raises(CorpusError):
        index.verified_passage("no-such-passage")
    assert len(resolve(index)) == len(SITUATIONS)


def test_analyze_response_is_unchanged_by_this_route():
    response = client.post("/analyze", json={"message": "URGENT: Share your OTP to keep your account active."})

    assert set(response.json()) == {"findings", "notice", "guidance", "classifier", "language"}
