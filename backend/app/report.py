"""A written record of a suspicious message, for the person to use when they report it.

The text is assembled here from a fixed template: the person's own message, the
rule-based warning signs, their answer about what happened, and the verified reporting
passage from the guidance corpus. No model writes any of it, and it makes no statement
about whether the message is fraudulent. Second Look does not send it anywhere.
"""

from datetime import date

from app.guidance import Passage, Source
from app.warning_signs import Finding

TITLE = "Record of a suspicious message"

CATEGORY_LABELS = {
    "urgency_pressure": "Urgency, a threat or a deadline",
    "credential_request": "Asks for an OTP, PIN, password or banking details",
    "link": "Contains a link",
    "payment_demand": "Asks for a payment, transfer or fee",
}

NOT_ANSWERED = "Not stated"
NO_FINDINGS = "None of the patterns Second Look checks for were found. It checks only a few patterns and can miss others."


def build_report(
    message: str, findings: list[Finding], answer: str | None, reporting: tuple[Passage, Source], today: date
) -> dict:
    """Return {"kind", "title", "text"}: plain text the person can copy."""
    passage, source = reporting
    signs = [
        f'- {CATEGORY_LABELS.get(finding.category, finding.category)}: "{finding.evidence}"' for finding in findings
    ] or [NO_FINDINGS]
    lines = [
        TITLE,
        f"Prepared with Second Look on {today.isoformat()}.",
        "This is a record of a message I received. It is not a finding that the message is fraudulent.",
        "",
        "The message, exactly as I received it:",
        message,
        "",
        f"What I have done so far: {answer or NOT_ANSWERED}",
        "",
        "Warning signs noticed by Second Look's rule-based checks:",
        *signs,
        "",
        "Where to report:",
        f"{passage.summary} (Source: {source.publisher}, {source.url})",
    ]
    return {"kind": "report", "title": TITLE, "text": "\n".join(lines)}
