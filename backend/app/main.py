import os
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.classifier import NOT_APPLICABLE, UNAVAILABLE, Classifier
from app.guidance import GuidanceIndex
from app.language import estimate_language
from app.next_steps import resolve as resolve_next_steps
from app.warning_signs import Finding, detect_warning_signs

MAX_MESSAGE_LENGTH = 5000

NOTICE = (
    "These are rule-based indicators only. They cannot determine whether a message "
    "is fraudulent: a message with no indicators may still be a scam, and a message "
    "with indicators may be legitimate. Verify through an official channel before acting."
)
GUIDANCE_NOTICE = (
    "These entries were retrieved by keyword similarity from a small, English-only "
    "collection of official guidance. They are not a judgement about this message, and "
    "the publishers have not reviewed or endorsed this service. Read the linked source."
)
NO_GUIDANCE_NOTICE = (
    "No matching official guidance was found. The collection is small and English-only, "
    "so this does not mean the message is safe."
)
SUMMARY_NOTE = "Summary written by Second Look. It is not a quotation from the source."
CLASSIFIER_NOTICE = (
    "This auxiliary signal compares the message with English SMS spam from a 2011 UK and "
    "Singapore dataset. It was not trained on Indian scams and cannot tell whether this "
    "message is fraudulent. Genuine bank, OTP and delivery messages are often rated "
    "spam-like, and many scams are not. A 'not spam-like' label does not mean the message "
    "is safe. This signal does not change the warning signs or the official guidance."
)
CLASSIFIER_NOT_APPLICABLE_NOTICE = (
    "The auxiliary classifier was not run because this message does not appear to be mainly "
    "in English, and the model was trained only on English SMS. This does not mean the "
    "message is safe."
)
CLASSIFIER_UNAVAILABLE_NOTICE = (
    "The auxiliary classifier is not available. The warning signs and official guidance are "
    "unaffected. This does not mean the message is safe."
)

NEXT_STEPS_NOTICE = (
    "These steps come from the linked official sources and are the same for everyone who "
    "picks the same answer. They are not advice about your particular case, and Second Look "
    "does not contact anyone or file a report for you."
)

app = FastAPI(title="Second Look", version="0.1.0")

# Browser origins allowed to call the API from another site, comma-separated (for example
# "https://second-look.example"). Unset means no cross-origin access; local development
# needs none because the Vite dev server proxies API calls.
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.environ.get("SECOND_LOOK_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

# Loaded once at startup. A missing or invalid corpus stops the service from starting.
guidance_index = GuidanceIndex.from_file()
# Also loaded once at startup, but optional: if the model cannot be loaded safely, the
# classifier section reports "unavailable" and the rest of /analyze keeps working.
classifier = Classifier.load()
# Fixed "what happened next?" steps, looked up once from the same verified passages. A
# missing or unverified passage stops the service from starting.
next_step_situations = resolve_next_steps(guidance_index)


class AnalyzeRequest(BaseModel):
    message: str = Field(max_length=MAX_MESSAGE_LENGTH)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


class GuidanceSource(BaseModel):
    title: str
    publisher: str
    url: str
    published: str | None
    retrieved: str
    section: str


class GuidanceMatch(BaseModel):
    topic: str
    summary: str
    summary_note: str
    source: GuidanceSource
    matched_terms: list[str]


class Guidance(BaseModel):
    matches: list[GuidanceMatch]
    notice: str


class ClassifierModel(BaseModel):
    name: str
    training_data: str
    model_sha256: str


class ClassifierSection(BaseModel):
    status: Literal["ok", "unavailable", "not_applicable"]
    label: Literal["spam_like", "not_spam_like"] | None
    model: ClassifierModel | None
    notice: str


class LanguageSection(BaseModel):
    detected: Literal["en", "hi", "hi-Latn", "te", "ur", "bn", "mixed", "unknown"]
    method: Literal["script_and_keyword_estimate"]
    coverage: Literal["supported", "partial", "unsupported"]
    notice: str


class StepAction(BaseModel):
    label: str
    href: str


class NextStep(BaseModel):
    topic: str
    summary: str
    summary_note: str
    source: GuidanceSource
    action: StepAction | None


class NextStepSituation(BaseModel):
    id: str
    label: str
    steps: list[NextStep]


class NextStepsResponse(BaseModel):
    situations: list[NextStepSituation]
    notice: str


class AnalyzeResponse(BaseModel):
    findings: list[Finding]
    notice: str
    guidance: Guidance
    classifier: ClassifierSection
    language: LanguageSection


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
    # The default response repeats the submitted value. Return the reason only.
    detail = [
        {"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detail})


def retrieve_guidance(message: str) -> Guidance:
    matches = [
        GuidanceMatch(
            topic=match.passage.topic,
            summary=match.passage.summary,
            summary_note=SUMMARY_NOTE,
            source=GuidanceSource(
                title=match.source.title,
                publisher=match.source.publisher,
                url=match.source.url,
                published=match.source.published,
                retrieved=match.source.retrieved,
                section=match.passage.section,
            ),
            matched_terms=list(match.matched_terms),
        )
        for match in guidance_index.search(message)
    ]
    return Guidance(matches=matches, notice=GUIDANCE_NOTICE if matches else NO_GUIDANCE_NOTICE)


def estimate_message_language(message: str) -> LanguageSection:
    # The estimate decides only whether the English-only classifier runs. It does not
    # change the warning-sign rules or the guidance.
    estimate = estimate_language(message)
    return LanguageSection(
        detected=estimate.detected, method=estimate.method, coverage=estimate.coverage, notice=estimate.notice
    )


def run_classifier(message: str, language: str) -> ClassifierSection:
    result = classifier.classify(message, language)
    notice = {
        UNAVAILABLE: CLASSIFIER_UNAVAILABLE_NOTICE,
        NOT_APPLICABLE: CLASSIFIER_NOT_APPLICABLE_NOTICE,
    }.get(result.status, CLASSIFIER_NOTICE)
    return ClassifierSection(status=result.status, label=result.label, model=result.model, notice=notice)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/next-steps")
def next_steps() -> NextStepsResponse:
    # The same for every caller: nothing about a message is sent to or used by this route.
    return NextStepsResponse(
        situations=[
            NextStepSituation(
                id=situation.id,
                label=situation.label,
                steps=[
                    NextStep(
                        topic=step.passage.topic,
                        summary=step.passage.summary,
                        summary_note=SUMMARY_NOTE,
                        source=GuidanceSource(
                            title=step.source.title,
                            publisher=step.source.publisher,
                            url=step.source.url,
                            published=step.source.published,
                            retrieved=step.source.retrieved,
                            section=step.passage.section,
                        ),
                        action=StepAction(label=step.action.label, href=step.action.href) if step.action else None,
                    )
                    for step in steps
                ],
            )
            for situation, steps in next_step_situations
        ],
        notice=NEXT_STEPS_NOTICE,
    )


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    language = estimate_message_language(request.message)
    return AnalyzeResponse(
        findings=detect_warning_signs(request.message),
        notice=NOTICE,
        guidance=retrieve_guidance(request.message),
        classifier=run_classifier(request.message, language.detected),
        language=language,
    )
