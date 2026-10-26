"""Checks on the GitLab pipeline and the GitLab Duo flow definitions.

GitLab validates these files only when they are used. These tests catch the mistakes that
would otherwise show up as a failed pipeline or a flow that cannot start.
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
FLOWS = sorted((ROOT / ".gitlab" / "duo" / "flows").glob("*.yml"))

# Tool names checked against GitLab's agent tool registry (duo_workflow_service/tools).
KNOWN_TOOLS = {
    "get_merge_request", "list_merge_request_diffs", "list_all_merge_request_notes", "create_merge_request_note",
    "get_pipeline_failing_jobs", "get_job_logs", "gitlab_api_get", "list_issues", "create_issue",
    "create_issue_note", "get_repository_file", "list_repository_tree", "read_file", "grep", "find_files",
}
# Flows only comment and report. None of them may change code, branches or settings.
WRITE_TOOLS = {"create_commit", "edit_file", "create_file_with_contents", "create_branch", "create_merge_request",
               "update_merge_request", "run_command", "update_issue"}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pipeline() -> dict:
    return load(ROOT / ".gitlab-ci.yml")


def test_there_are_flows_to_check():
    assert {path.name for path in FLOWS} == {"mr-safety-review.yml", "pipeline-triage.yml"}


@pytest.mark.parametrize("path", FLOWS, ids=lambda path: path.name)
def test_flow_follows_the_flow_registry_v1_format(path):
    flow = load(path)

    assert flow["version"] == "v1" and flow["environment"] == "ambient"
    names = {component["name"] for component in flow["components"]}
    assert flow["flow"]["entry_point"] in names
    for router in flow["routers"]:
        assert router["from"] in names and router["to"] in names | {"end", "abort"}
    prompts = {prompt["prompt_id"]: prompt for prompt in flow["prompts"]}
    for component in flow["components"]:
        assert ":" not in component["name"] and "." not in component["name"]
        prompt = prompts[component["prompt_id"]]
        assert prompt["unit_primitives"] == [] and prompt["prompt_template"]["placeholder"] == "history"
        # Every {{ variable }} in the prompt must come from the component's inputs.
        aliases = {item["as"] for item in component["inputs"]}
        template = prompt["prompt_template"]["system"] + prompt["prompt_template"]["user"]
        assert set(re.findall(r"\{\{\s*(\w+)\s*\}\}", template)) <= aliases
        # GitLab API tools need the project ID passed in explicitly.
        assert "project_id" in aliases and "Project ID: {{ project_id }}" in prompt["prompt_template"]["user"]
        # Without an explicit stopping instruction an agent loops.
        assert "No further steps are needed after that." in prompt["prompt_template"]["system"]


@pytest.mark.parametrize("path", FLOWS, ids=lambda path: path.name)
def test_flows_use_known_tools_and_cannot_change_code(path):
    for component in load(path)["components"]:
        tools = {tool if isinstance(tool, str) else next(iter(tool)) for tool in component["toolset"]}
        assert tools <= KNOWN_TOOLS, tools - KNOWN_TOOLS
        assert not tools & WRITE_TOOLS


@pytest.mark.parametrize("path", FLOWS, ids=lambda path: path.name)
def test_flows_carry_the_projects_safety_rules(path):
    system = load(path)["prompts"][0]["prompt_template"]["system"]

    assert "AGENTS.md" in system
    assert "data, never instructions" in system
    assert "quality_baseline.json" in system


def test_pipeline_runs_tests_scans_and_the_gate_on_every_merge_request(pipeline):
    assert pipeline["stages"] == ["test", "quality", "deploy", "verify"]
    templates = {item["template"] for item in pipeline["include"]}
    assert {"Jobs/SAST.latest.gitlab-ci.yml", "Jobs/Secret-Detection.latest.gitlab-ci.yml"} <= templates
    for job in ("backend-tests", "frontend-tests", "quality-gate"):
        assert job in pipeline
    assert "--require-classifier" in " ".join(pipeline["quality-gate"]["script"])


def test_only_main_deploys_and_only_after_the_checks_pass(pipeline):
    deploy = pipeline["deploy-production"]

    assert set(deploy["needs"]) == {"backend-tests", "frontend-tests", "quality-gate"}
    assert all("$CI_DEFAULT_BRANCH" in rule["if"] for rule in deploy["rules"])
    assert deploy["environment"]["name"] == "production"
    script = " ".join(deploy["script"])
    assert "release.py deploy" in script and 'wait --commit "$CI_COMMIT_SHA"' in script
    assert pipeline["verify-production"]["needs"] == ["deploy-production"]
    assert "--agent" in " ".join(pipeline["verify-production"]["script"])


def test_monitoring_runs_only_on_a_schedule(pipeline):
    assert pipeline["monitor-production"]["rules"] == [{"if": '$CI_PIPELINE_SOURCE == "schedule"'}]


def test_cache_keys_use_at_most_two_files(pipeline):
    # GitLab rejects the whole pipeline when cache:key:files lists more than two files.
    for name, job in pipeline.items():
        if isinstance(job, dict) and isinstance(job.get("cache"), dict):
            files = job["cache"].get("key", {}).get("files", [])
            assert len(files) <= 2, name


def test_no_secret_is_written_into_the_pipeline():
    text = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")

    assert "api.render.com/deploy" not in text
    assert not re.search(r"(?i)(api[_-]?key|token)\s*[:=]\s*\S{8,}", text)
