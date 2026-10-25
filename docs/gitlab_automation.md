# Second Look on GitLab: automation after the code

Second Look is a live service that people in India use while a scam message is in front of them. A broken release, a leaked key, or a change that lets the AI agent call a scam "safe" would hurt real people. This document describes how GitLab CI/CD and GitLab Duo Agent Platform take every change from merge request to a checked, live release, and how to set it up.

## Before and after

| Step | Before (GitHub and Render, by hand) | After (GitLab) |
| --- | --- | --- |
| Tests | Run on a laptop when remembered | 698 backend, 35 ML and 123 frontend tests on every merge request, with results shown in the merge request |
| Code review | None | A Duo flow reviews every merge request against the project's safety rules in `AGENTS.md` and posts one comment |
| Security | None | SAST and secret detection on every merge request; Python and npm dependency audits |
| Quality of the AI and ML parts | A one-off evaluation, recorded in the README | A quality gate re-measures the agent's guardrail, guidance retrieval, warning signs and the classifier on every merge request, and blocks the merge if any number gets worse |
| Deploy | "Deploy latest commit" pressed by hand on two Render services | Merging to `main` deploys both services, then waits until the backend reports the new commit |
| Release check | Opening the site and trying a message | Six live checks, including a full AI agent run and a check that no verdict reached the user |
| Monitoring | None | The same live checks on a schedule |
| When something fails | Noticed by chance | A Duo flow reads the failed job logs, finds the cause, and reports it on the merge request or in a `production-health` issue with a proposed fix |

## The pipeline (`.gitlab-ci.yml`)

```
merge request ─► test ──────────────────────────► quality
                 backend-tests (pytest)            quality-gate
                 frontend-tests (Vitest + build)     agent guardrail, retrieval,
                 SAST, secret detection              warning signs, classifier
                 dependency audits
                        │ pipeline fails ─► Duo: pipeline triage flow
                        │ merge request opened ─► Duo: safety review flow
merge to main ─► same checks ─► deploy ─────────────► verify
                                deploy-production      verify-production
                                  Render deploy hooks    live checks + one agent run
                                  wait for new commit
schedule ──────────────────────────────────────────► monitor-production ─► Duo triage on failure
```

### The quality gate (`backend/evaluation/quality_gate.py`)

It compares each number with `backend/evaluation/quality_baseline.json`. A number may only get better.

| Area | What is measured |
| --- | --- |
| Agent guardrail | On a fixed set of 38 verdicts and attack outcomes, none may get past the check (a fixed rule that updating the baseline cannot relax). On 22 real summaries written by Gemini and Groq in live runs, the share allowed through may not fall, so the check cannot be "fixed" by blocking everything. |
| Guidance retrieval | Precision and recall on the hand-written retrieval set, for both splits |
| Unsupported languages | The service must still find no false warning signs in Telugu, Urdu and Bengali, which it does not read |
| Classifier | Precision, recall, F1 and false-positive rate on the held-out UCI test split, rebuilt exactly as in training |

On its first run the gate found a real gap: the summary "Paying is the correct and safe thing to do." got past the agent's check. That is what a digital-arrest scam in the attack set asks the model to say. The check was fixed in the same change.

### Live checks and monitoring (`ops/release.py`)

`deploy` calls the Render deploy hooks; `wait` polls the backend's `/version` until it reports the pipeline's commit; `smoke` runs six checks against the live site: backend health, warning signs on a known scam, no false alarm on an ordinary message, the official next steps with Call 1930 first, the frontend offering the agent, and one full agent run with a check that no verdict reached the user.

## The GitLab Duo flows (`.gitlab/duo/flows/`)

| Flow | Trigger | What it does |
| --- | --- | --- |
| Second Look safety review (`mr-safety-review.yml`) | Merge request created; also when its service account is assigned as reviewer | Reads the change, `AGENTS.md` and the pipeline result, then posts one comment: Blocking, Should fix, Pipeline, Not checked. It checks the things specific to this project: verdict wording, weakened guardrails, baseline edits, weakened tests, logging of message text, invented advice, and Hindi text kept in step with English. |
| Second Look pipeline triage (`pipeline-triage.yml`) | Pipeline failed | Reads the failed job logs and diagnoses the cause by job. On a merge request it comments there; on `main` or in monitoring it opens or updates a `production-health` issue with the cause, the impact on users, and a proposed fix. |

Both flows can only read and comment. Neither can edit code, push, merge, deploy or change settings, and both are told never to lower the quality baseline or weaken a test. `AGENTS.md` gives every agent, including GitLab's own foundational flows, the same rules.

## Setting it up

You need the project provisioned by the hackathon (GitLab Duo Agent Platform turned on) and Maintainer access.

### 1. Import the repository

1. In the provisioned project, **Settings > Repository > Mirroring repositories** is one option; the simpler one is to push the code: on your computer, in the project folder, run
   `git remote add gitlab <the project's HTTPS clone URL>` and then `git push gitlab main`.
2. Check that **Settings > General > Visibility** is **Public**, and that the MIT licence shows on the project page.

### 2. Connect Render

Render must build the same code GitLab tests. Choose one:

- **Connect Render to GitLab (recommended).** In each Render service: **Settings > Build & Deploy > Repository**, connect your GitLab account and pick the GitLab project, branch `main`. Keep **Auto-Deploy** off; the pipeline deploys.
- **Keep Render on GitHub.** In GitLab, add a push mirror to the GitHub repository (**Settings > Repository > Mirroring repositories**), and set the CI/CD variable `GITHUB_MIRROR_REPO` to `maimunaafrah341-maker/second-look-ai`. The deploy job then waits for the mirror before deploying.

### 3. CI/CD variables

In GitLab, **Settings > CI/CD > Variables**, add (type Variable, **Masked**, **Protected**):

| Key | Value |
| --- | --- |
| `RENDER_BACKEND_DEPLOY_HOOK` | Render backend service: **Settings > Deploy Hook** URL |
| `RENDER_FRONTEND_DEPLOY_HOOK` | Render frontend service: **Settings > Deploy Hook** URL |

The Gemini and Groq keys stay in Render; the pipeline does not need them.

### 4. Monitoring schedule

**Build > Pipeline schedules > New schedule**: description "Monitor production", interval every 6 hours (`0 */6 * * *`), target branch `main`.

### 5. Duo flows and triggers

1. **AI > Flows > New flow**: paste `.gitlab/duo/flows/mr-safety-review.yml`, save, then enable it for the project.
2. **AI > Triggers > New flow trigger**: event **Merge request**, action **Created**, flow "Second Look safety review". Add a second condition, **Assign reviewer**, to re-run it on demand.
3. Repeat for `.gitlab/duo/flows/pipeline-triage.yml` with event **Pipeline events**, action **Failed**.
4. Flows run on GitLab-hosted runners; if a flow stays queued, check **Settings > CI/CD > Runners**.

### 6. See it work

1. Open a merge request with a small change. Watch the pipeline, the test report and the safety review comment.
2. Open a merge request that adds the word "safe" to a summary pattern test, or lowers a number in `quality_baseline.json`. The gate or the review should block it, and the triage flow should explain why.
3. Merge a change to `main`. Watch `deploy-production` wait for the new commit and `verify-production` run the live checks.
4. Review agent activity under **AI > Sessions**.

## Limits

- The evaluation sets are small and written by this project. The gate catches regressions; it does not prove accuracy on real messages.
- The live agent check uses Gemini and Groq free tiers, so a rate limit can fail a run; the triage flow says so when that is the cause.
- The flow definitions follow GitLab's Flow Registry v1 format, which GitLab labels beta.
