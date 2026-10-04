from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

from app.warning_signs import Finding, detect_warning_signs

MAX_MESSAGE_LENGTH = 5000

NOTICE = (
    "These are rule-based indicators only. They cannot determine whether a message "
    "is fraudulent: a message with no indicators may still be a scam, and a message "
    "with indicators may be legitimate. Verify through an official channel before acting."
)

app = FastAPI(title="Second Look", version="0.1.0")


class AnalyzeRequest(BaseModel):
    message: str = Field(max_length=MAX_MESSAGE_LENGTH)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


class AnalyzeResponse(BaseModel):
    findings: list[Finding]
    notice: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return AnalyzeResponse(findings=detect_warning_signs(request.message), notice=NOTICE)
