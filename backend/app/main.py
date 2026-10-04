from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.guidance import GuidanceIndex
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

app = FastAPI(title="Second Look", version="0.1.0")

# Loaded once at startup. A missing or invalid corpus stops the service from starting.
guidance_index = GuidanceIndex.from_file()


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


class AnalyzeResponse(BaseModel):
    findings: list[Finding]
    notice: str
    guidance: Guidance


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return AnalyzeResponse(
        findings=detect_warning_signs(request.message),
        notice=NOTICE,
        guidance=retrieve_guidance(request.message),
    )
