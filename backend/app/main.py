import os
import threading
import time
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.agent import build_tools, run_agent
from app.classifier import NOT_APPLICABLE, UNAVAILABLE, Classifier
from app.env import load_env_file
from app.guidance import GuidanceIndex
from app.language import estimate_language
from app.next_steps import resolve as resolve_next_steps
from app.report import build_report
from app.warning_signs import Finding, detect_warning_signs

# For local development only: a hosting provider sets its own variables and has no .env file.
load_env_file()

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

AGENT_NOTICE = (
    "This used a language model, so your message was sent to Google or Groq. The model "
    "only chose which checks to run and wrote the summary; the warning signs, guidance and "
    "steps come from the same code and official sources as the rest of Second Look. It "
    "cannot determine whether a message is fraudulent. Verify through an official channel "
    "before acting."
)
# The agent calls free-tier model APIs, so requests to it are limited: per caller and in
# total, per minute. The counts are held in memory only and hold no message text.
AGENT_REQUESTS_PER_MINUTE = int(os.environ.get("SECOND_LOOK_AGENT_REQUESTS_PER_MINUTE", "10"))
AGENT_TOTAL_PER_MINUTE = int(os.environ.get("SECOND_LOOK_AGENT_TOTAL_PER_MINUTE", "60"))

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


class AgentRequest(AnalyzeRequest):
    # The person's answer to the agent's one question: the id of a fixed situation.
    situation: str | None = None

    @field_validator("situation")
    @classmethod
    def situation_must_be_known(cls, value: str | None) -> str | None:
        if value is not None and value not in SITUATION_LABELS:
            raise ValueError("situation is not one of the fixed choices")
        return value


class AgentOption(BaseModel):
    id: str
    label: str


class AgentStep(BaseModel):
    step: int
    provider: str | None
    action: str
    args: dict
    outcome: Literal["ok", "refused", "rejected"]
    detail: str
    # The model's own one-line reason for the step, or None when it gave none or it failed the check.
    reason: str | None
    result: dict | None


class AgentResponse(BaseModel):
    status: Literal["finished", "needs_input", "step_limit", "rejected", "unavailable"]
    text: str | None
    question: str | None
    options: list[AgentOption]
    trace: list[AgentStep]
    notice: str


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


# Render sets RENDER_GIT_COMMIT to the commit it built. The pipeline reads this after a
# deploy to confirm the new commit is the one serving requests before it runs smoke tests.
COMMIT_ENV_VARS = ("SECOND_LOOK_COMMIT", "RENDER_GIT_COMMIT")


@app.get("/version")
def version() -> dict[str, str]:
    commit = next((os.environ[name] for name in COMMIT_ENV_VARS if os.environ.get(name)), "unknown")
    return {"commit": commit}


def next_steps_response() -> NextStepsResponse:
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


def analyze_message(message: str) -> AnalyzeResponse:
    language = estimate_message_language(message)
    return AnalyzeResponse(
        findings=detect_warning_signs(message),
        notice=NOTICE,
        guidance=retrieve_guidance(message),
        classifier=run_classifier(message, language.detected),
        language=language,
    )


SITUATION_LABELS = {situation.id: situation.label for situation, _ in next_step_situations}


def situation_steps(situation_id: str) -> dict:
    situation = next(item for item in next_steps_response().situations if item.id == situation_id)
    return situation.model_dump()


# The report always points to the same verified passage that /next-steps uses for reporting.
REPORTING_PASSAGE_ID = "report-helpline-1930"
reporting_passage = guidance_index.verified_passage(REPORTING_PASSAGE_ID)


def prepare_report(message: str, situation_id: str | None) -> dict:
    answer = SITUATION_LABELS.get(situation_id) if situation_id else None
    return build_report(message, detect_warning_signs(message), situation_id, answer, reporting_passage, date.today())


# The only things the agent can do: the parts of /analyze as separate checks, the fixed next
# steps, a templated report, one fixed question, and finishing.
agent_tools = build_tools(
    warning_signs=lambda message: {
        "findings": [finding.model_dump() for finding in detect_warning_signs(message)],
        "notice": NOTICE,
    },
    guidance=lambda query: retrieve_guidance(query).model_dump(),
    language=lambda message: estimate_message_language(message).model_dump(),
    spam_signal=lambda message: run_classifier(message, estimate_message_language(message).detected).model_dump(),
    next_steps=situation_steps,
    report=prepare_report,
)


class RateLimiter:
    """Counts requests per caller and in total within a fixed window, in memory."""

    def __init__(self, per_caller: int, total: int, window_seconds: float = 60.0):
        self.per_caller = per_caller
        self.total = total
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        self._started = time.monotonic()
        self._counts: dict[str, int] = {}
        self._total = 0

    def allow(self, caller: str) -> bool:
        with self._lock:
            if time.monotonic() - self._started >= self.window_seconds:
                self.reset()
            if self._total >= self.total or self._counts.get(caller, 0) >= self.per_caller:
                return False
            self._total += 1
            self._counts[caller] = self._counts.get(caller, 0) + 1
            return True


agent_limiter = RateLimiter(AGENT_REQUESTS_PER_MINUTE, AGENT_TOTAL_PER_MINUTE)


@app.get("/next-steps")
def next_steps() -> NextStepsResponse:
    # The same for every caller: nothing about a message is sent to or used by this route.
    return next_steps_response()


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return analyze_message(request.message)


@app.post("/agent")
def agent(request: AgentRequest, http_request: Request) -> AgentResponse:
    # Opt-in: unlike /analyze, this sends the message to a language model provider. Nothing
    # is kept between requests; the answer to the agent's question arrives as `situation`.
    caller = http_request.client.host if http_request.client else "unknown"
    if not agent_limiter.allow(caller):
        raise HTTPException(status_code=429, detail="Too many agent requests. Try again in a minute.")
    result = run_agent(
        request.message,
        request.situation,
        SITUATION_LABELS.get(request.situation) if request.situation else None,
        agent_tools,
    )
    options = [AgentOption(id=key, label=label) for key, label in SITUATION_LABELS.items()]
    return AgentResponse(
        status=result.status,
        text=result.text,
        question=result.question,
        options=options if result.status == "needs_input" else [],
        trace=result.trace,
        notice=AGENT_NOTICE,
    )
