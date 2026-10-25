# Instructions for AI agents working on Second Look

Second Look helps people in India take a second look at a suspicious SMS, WhatsApp message or email. Its users are often frightened, rushed or older, and a wrong answer can cost them money. These rules apply to every agent and flow in this project, including GitLab Duo flows, code review and pipeline fixes.

## The rules that must never be broken

1. **No verdicts.** Nothing Second Look shows may say or imply that a message is, or is not, a scam, safe, genuine or fraudulent, and nothing may give a score, percentage or likelihood. "No warning signs were found" must never become "the message is safe". Treat any change that adds such wording, or weakens the checks that block it, as blocking.
2. **The agent's checks live in code.** `check_summary` and `check_final_text` in `backend/app/agent.py`, the action allowlist (`build_tools`), and the step limits are safety controls. Changes that remove a pattern, widen the allowlist, let the model supply the message, question or answer, or raise the limits need a clear reason and new tests.
3. **The quality gate may only get better.** Never edit `backend/evaluation/quality_baseline.json` to make a failing gate pass. A lower number is a regression to fix in the code. Rules marked `"fixed": true` are requirements, not measurements, and must not change.
4. **Never weaken a test to make it pass.** Fix the code instead. If a test is wrong, say why in the merge request.
5. **Privacy.** Never log, store or print the text of a submitted message, an API key or a deploy hook. Validation errors must not echo what was submitted. Only the agent sends a message to an outside company (Google or Groq), and the page must say so before the button is pressed.
6. **Official sources only.** Guidance comes from verified passages in `backend/app/data/guidance.json`. Do not invent advice, phone numbers or links. The only helpline is 1930.
7. **Languages.** Hindi text shown to users lives in `frontend/src/content/`; when an English API text changes, its Hindi entry in `apiHindi.ts` and `frontend/src/test/fixtures/api-fixed-text.json` must change with it. Telugu, Urdu and Bengali rules are switched off until native speakers review them; nothing may switch them on.
8. **Licence and authorship.** The project is MIT-licensed. Commits are made in the maintainer's name only.

## Layout

| Path | What it is |
| --- | --- |
| `backend/app/` | FastAPI service: warning-sign rules, guidance retrieval, classifier, language estimate, next steps, report, AI agent |
| `backend/app/agent.py` | The agent loop, its allowlisted tools, the Gemini and Groq calls, and the summary check |
| `backend/evaluation/` | Evaluation sets, the live agent evaluation, and the quality gate (`quality_gate.py`) |
| `backend/tests/`, `ml/tests/` | pytest suites |
| `frontend/src/` | React and TypeScript app; tests in `frontend/src/test/` |
| `ml/` | Dataset ingestion and classifier training |
| `ops/release.py` | Deploy to Render, wait for the new commit, live checks and monitoring |
| `.gitlab-ci.yml` | The pipeline |
| `.gitlab/duo/` | GitLab Duo flow definitions and agent setup |

## Commands

```bash
pip install -r requirements-dev.txt
python -m pytest -q                                   # backend and ML tests
python backend/evaluation/quality_gate.py             # quality gate (add --require-classifier after ml/src/ingest_sms_spam.py)
cd frontend && npm ci && npx vitest run && npm run build
python ops/release.py smoke                           # live checks against the deployed site
```

## How to report

Write for a maintainer reading on a phone: short, plain sentences. Lead with whether anything blocks the merge. Quote file paths and the exact lines you mean. Say what you did not check.
