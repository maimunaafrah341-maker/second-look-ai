"""Fixed next steps for what happened after a suspicious message.

The person picks what happened. Each choice maps to verified passages of the guidance
corpus, in a fixed order. Nothing is generated or inferred from the message, and no
model is involved: the steps are the same summaries and sources that /analyze serves.

The choices and their wording are written by Second Look. What to do comes only from
the passages, so a step can be traced to its official source.
"""

from dataclasses import dataclass

from app.guidance import GuidanceIndex, Passage, Source


@dataclass(frozen=True)
class Action:
    """Something the person can do directly from the page, such as dialling a number."""

    label: str
    href: str


@dataclass(frozen=True)
class Situation:
    id: str
    label: str
    passage_ids: tuple[str, ...]


@dataclass(frozen=True)
class Step:
    passage: Passage
    source: Source
    action: Action | None


# The I4C website tells people to report cybercrime by calling 1930.
ACTIONS = {"report-helpline-1930": Action(label="Call 1930", href="tel:1930")}

# Ordered from least to most serious. Where money has been lost, reporting comes first.
SITUATIONS = (
    Situation("not_responded", "I haven't replied, clicked or paid", ("phishing-donts",)),
    Situation("clicked_link", "I clicked a link in the message", ("phishing-if-you-responded",)),
    Situation(
        "shared_details",
        "I shared an OTP, PIN, password, or card or bank details",
        ("phishing-if-you-responded", "report-helpline-1930"),
    ),
    Situation(
        "lost_money",
        "I paid, or money has left my account",
        ("report-helpline-1930", "phishing-if-you-responded"),
    ),
)


def resolve(index: GuidanceIndex) -> list[tuple[Situation, list[Step]]]:
    """Look up every situation's passages. Raises CorpusError if one is missing or unverified."""
    return [
        (
            situation,
            [
                Step(*index.verified_passage(passage_id), ACTIONS.get(passage_id))
                for passage_id in situation.passage_ids
            ],
        )
        for situation in SITUATIONS
    ]
