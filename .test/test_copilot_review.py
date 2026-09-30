"""Exercise the owner and quota boundaries of the Copilot review workflow."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest
import yaml

OWNER = "owner"
REPOSITORY = {"full_name": "owner/repository", "fork": False}
BOT = {"id": 175728472, "login": "Copilot", "type": "Bot"}
HARNESS = r"""
const fixture = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
const result = {requests: [], failures: [], calls: []};
const pending = fixture.pending;
let reads = 0;
const github = {
  paginate: async (method, options) => {
    const {data} = await method(options);
    return Array.isArray(data) ? data : data.jobs;
  },
  rest: {
    pulls: {
      get: async () => ({
        data: fixture.current && reads++ > 0 ? fixture.current : fixture.pr
      }),
      listRequestedReviewers: async () => ({data: {users: pending}}),
      listReviews: async () => ({data: fixture.reviews})
    },
    actions: {
      listWorkflowRuns: async options => {
        result.calls.push({method: 'listWorkflowRuns', options});
        return {data: {workflow_runs: fixture.runs}};
      },
      listJobsForWorkflowRun: async options => {
        result.calls.push({method: 'listJobsForWorkflowRun', options});
        const jobs = options.filter === 'latest'
          ? fixture.jobs : [...fixture.oldJobs, ...fixture.jobs];
        return {data: {jobs}};
      }
    },
    users: {getByUsername: async () => ({data: fixture.bot})}
  }
};
const getOctokit = token => {
  if (token !== 'fixture-owner-token') throw new Error('Unexpected token');
  result.calls.push({method: 'getOctokit'});
  return {rest: {
    users: {getAuthenticated: async () => ({data: fixture.identity})},
    pulls: {requestReviewers: async options => {
      result.requests.push(options);
      pending.push(fixture.bot);
      return {data: {}};
    }}
  }};
};
const core = {info: () => {}, setFailed: message => result.failures.push(message)};
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const execute = new AsyncFunction(
  'github', 'context', 'core', 'getOctokit', 'process', fixture.script
);
// This workflow's condition uses plain boolean syntax shared with JavaScript.
const enabled = new Function('github', 'vars', `return (${fixture.jobIf});`)(
  {
    repository_owner: fixture.context.repo.owner,
    repository: `${fixture.context.repo.owner}/${fixture.context.repo.repo}`,
    actor: fixture.context.actor,
    triggering_actor: fixture.env.TRIGGERING_ACTOR,
    event_name: fixture.context.eventName,
    event: fixture.context.payload
  },
  {COPILOT_REVIEW_ENABLED: fixture.enabled}
);
(async () => {
  for (let i = 0; enabled && i < fixture.repeats; i++) {
    await execute(github, fixture.context, core, getOctokit, {env: fixture.env});
  }
  console.log(JSON.stringify(result));
})().catch(error => {console.error(error); process.exitCode = 1;});
"""


@pytest.fixture(name="workflow", scope="module")
def fixture_workflow(repo_root: Path):
    """Read the production workflow without credentials or network access."""
    return yaml.safe_load(
        (repo_root / ".github/workflows/copilot-review.yml").read_text()
    )


def scenario(workflow: dict, *, ready: bool = False) -> dict:
    """Build valid GitHub metadata; individual cases vary one trust boundary."""
    job = workflow["jobs"]["request"]

    pull_request = {
        "number": 7,
        "state": "open",
        "draft": False,
        "user": {"login": OWNER},
        "base": {"repo": copy.deepcopy(REPOSITORY)},
        "head": {"repo": copy.deepcopy(REPOSITORY), "sha": "a" * 40},
    }
    run = {
        "id": 31,
        "event": "pull_request",
        "status": "completed",
        "conclusion": "success",
        "actor": {"login": OWNER},
        "triggering_actor": {"login": OWNER},
        "head_repository": copy.deepcopy(REPOSITORY),
        "head_branch": "feature",
        "head_sha": pull_request["head"]["sha"],
    }
    return {
        "script": next(
            step["with"]["script"] for step in job["steps"] if "with" in step
        ),
        "jobIf": job["if"],
        "enabled": "true",
        "context": {
            "repo": {"owner": OWNER, "repo": "repository"},
            "eventName": "pull_request",
            "actor": OWNER,
            "payload": {
                "action": "ready_for_review" if ready else "synchronize",
                "pull_request": copy.deepcopy(pull_request),
            },
        },
        "pr": pull_request,
        "runs": [run],
        "jobs": [
            {"name": "ci", "status": "completed", "conclusion": "success"}
        ],
        "oldJobs": [],
        "pending": [],
        "reviews": [],
        "bot": BOT,
        "identity": {"login": OWNER, "type": "User"},
        "env": {
            "COPILOT_REVIEW_TOKEN": "fixture-owner-token",
            "TRIGGERING_ACTOR": OWNER,
            "VALIDATED_HEAD": "" if ready else pull_request["head"]["sha"],
        },
        "repeats": 1,
    }


def execute(run_command, fixture: dict) -> dict:
    """Supply only synthetic API responses and a minimal Node environment."""
    result = run_command(
        ["node", "-e", HARNESS],
        input=json.dumps(fixture),
        env={"PATH": os.environ.get("PATH", os.defpath)},
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def assert_skipped(run_command, fixture: dict) -> None:
    """An ineligible PR must not even instantiate the owner-token client."""
    result = execute(run_command, fixture)
    assert result["requests"] == []
    assert result["failures"] == []
    assert {"method": "getOctokit"} not in result["calls"]


def test_owner_review_is_requested_once_after_successful_current_ci(
    run_command, workflow
):
    fixture = scenario(workflow)
    fixture["repeats"] = 2
    result = execute(run_command, fixture)
    assert result["failures"] == []
    assert result["requests"] == [
        {
            "owner": OWNER,
            "repo": "repository",
            "pull_number": 7,
            "reviewers": ["copilot-pull-request-reviewer[bot]"],
        }
    ]
    # The reusable workflow executes after ci, before its caller completes.
    assert not any(
        call["method"] == "listWorkflowRuns" for call in result["calls"]
    )


@pytest.mark.parametrize(
    "case",
    ["actor", "rerunner", "event", "untested", "event_head", "validated_head"],
)
def test_rejects_foreign_actors_and_untested_or_stale_heads(
    run_command, workflow, case
):
    fixture = scenario(workflow)
    if case == "actor":
        fixture["context"]["actor"] = "outsider"
    elif case == "rerunner":
        fixture["env"]["TRIGGERING_ACTOR"] = "outsider"
    elif case == "event":
        fixture["context"]["eventName"] = "push"
    elif case == "untested":
        fixture["env"]["VALIDATED_HEAD"] = ""
    elif case == "event_head":
        fixture["context"]["payload"]["pull_request"]["head"]["sha"] = "b" * 40
    else:
        fixture["env"]["VALIDATED_HEAD"] = "b" * 40
    assert_skipped(run_command, fixture)


def test_draft_made_ready_during_ci_uses_current_pull_request_state(
    run_command, workflow
):
    fixture = scenario(workflow)
    fixture["context"]["payload"]["pull_request"]["draft"] = True
    result = execute(run_command, fixture)
    assert len(result["requests"]) == 1
    assert result["failures"] == []


def test_disabled_review_setting_never_requests_a_review(run_command, workflow):
    fixture = scenario(workflow)
    fixture["enabled"] = "false"
    assert_skipped(run_command, fixture)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("draft", True),
        ("state", "closed"),
        ("user", {"login": "outsider"}),
    ],
)
def test_rejects_external_draft_and_closed_pull_requests(
    run_command, workflow, key, value
):
    fixture = scenario(workflow)
    fixture["pr"][key] = value
    assert_skipped(run_command, fixture)


@pytest.mark.parametrize(
    ("side", "repository"),
    [
        ("head", {"full_name": "outsider/repository", "fork": True}),
        ("head", {**REPOSITORY, "fork": True}),
        ("base", {"full_name": "owner/other"}),
    ],
)
def test_rejects_fork_or_foreign_repositories(
    run_command, workflow, side, repository
):
    fixture = scenario(workflow)
    fixture["pr"][side]["repo"] = repository
    assert_skipped(run_command, fixture)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("status", "queued"),
        ("conclusion", "failure"),
        ("conclusion", "cancelled"),
        ("actor", {"login": "outsider"}),
        ("triggering_actor", {"login": "outsider"}),
        ("head_repository", {"full_name": "outsider/repository"}),
        ("head_sha", "b" * 40),
        (None, None),
    ],
)
def test_latest_ci_rejects_missing_runs_failures_and_foreign_actors(
    run_command, workflow, key, value
):
    fixture = scenario(workflow, ready=True)
    if key is None:
        fixture["runs"] = []
    else:
        fixture["runs"][0][key] = value
    assert_skipped(run_command, fixture)


def test_ready_after_draft_skip_does_not_wait_for_parent_finalization(
    run_command, workflow
):
    draft = scenario(workflow)
    draft["pr"]["draft"] = True
    assert_skipped(run_command, draft)
    ready = scenario(workflow, ready=True)
    ready["runs"][0].update(status="in_progress", conclusion=None)
    result = execute(run_command, ready)
    assert len(result["requests"]) == 1
    assert result["failures"] == []


@pytest.mark.parametrize(
    "jobs",
    [
        [],
        [{"name": "ci", "status": "in_progress", "conclusion": None}],
        [{"name": "ci", "status": "queued", "conclusion": None}],
        [{"name": "ci", "status": "completed", "conclusion": "failure"}],
        [{"name": "ci", "status": "completed", "conclusion": "cancelled"}],
        [{"name": "ci", "status": "completed", "conclusion": "skipped"}],
        [
            {
                "name": "static-checks",
                "status": "completed",
                "conclusion": "success",
            }
        ],
    ],
    ids=[
        "missing",
        "running",
        "queued",
        "failed",
        "cancelled",
        "skipped",
        "wrong-job",
    ],
)
def test_ready_requires_successful_ci_job_from_latest_attempt(
    run_command, workflow, jobs
):
    fixture = scenario(workflow, ready=True)
    fixture["runs"][0].update(status="in_progress", conclusion=None)
    fixture["oldJobs"] = fixture["jobs"]
    fixture["jobs"] = jobs
    assert_skipped(run_command, fixture)


@pytest.mark.parametrize(
    ("field", "value"), [("pending", [BOT]), ("reviews", [{"user": BOT}])]
)
def test_existing_or_pending_copilot_id_prevents_another_request(
    run_command, workflow, field, value
):
    fixture = scenario(workflow)
    fixture[field] = value
    assert_skipped(run_command, fixture)


def test_ready_for_review_uses_existing_ci_from_latest_attempt(
    run_command, workflow
):
    fixture = scenario(workflow, ready=True)
    result = execute(run_command, fixture)
    assert len(result["requests"]) == 1
    assert result["failures"] == []
    query = next(
        call["options"]
        for call in result["calls"]
        if call["method"] == "listWorkflowRuns"
    )
    assert query["workflow_id"] == "ansible.yml"
    assert query["event"] == "pull_request"
    assert query["head_sha"] == fixture["pr"]["head"]["sha"]
    jobs_query = next(
        call["options"]
        for call in result["calls"]
        if call["method"] == "listJobsForWorkflowRun"
    )
    assert jobs_query["run_id"] == fixture["runs"][0]["id"]
    assert jobs_query["filter"] == "latest"


@pytest.mark.parametrize("field", ["actor", "triggering_actor", "action"])
def test_ready_for_review_rejects_other_actors_and_events(
    run_command, workflow, field
):
    fixture = scenario(workflow, ready=True)
    if field == "actor":
        fixture["context"]["actor"] = "outsider"
    elif field == "triggering_actor":
        fixture["env"]["TRIGGERING_ACTOR"] = "outsider"
    else:
        fixture["context"]["payload"]["action"] = "opened"
    assert_skipped(run_command, fixture)


@pytest.mark.parametrize("case", ["missing", "other_user", "bot"])
def test_missing_token_or_wrong_identity_fails_without_requesting(
    run_command, workflow, case
):
    fixture = scenario(workflow)
    if case == "missing":
        del fixture["env"]["COPILOT_REVIEW_TOKEN"]
    elif case == "other_user":
        fixture["identity"]["login"] = "outsider"
    else:
        fixture["identity"]["type"] = "Bot"
    result = execute(run_command, fixture)
    assert result["requests"] == []
    assert len(result["failures"]) == 1


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("draft", True),
        ("state", "closed"),
        ("head", {"repo": REPOSITORY, "sha": "b" * 40}),
    ],
)
def test_rechecks_live_pull_request_before_spending(
    run_command, workflow, key, value
):
    fixture = scenario(workflow)
    fixture["current"] = copy.deepcopy(fixture["pr"])
    fixture["current"][key] = value
    result = execute(run_command, fixture)
    assert result["requests"] == []
    assert result["failures"] == []


def test_workflow_keeps_execution_metadata_only_and_bounded(
    workflow, repo_root
):
    # PyYAML's YAML 1.1 loader treats GitHub's unquoted "on" key as True.
    events = workflow[True]
    job = workflow["jobs"]["request"]
    assert set(events) == {"workflow_call", "pull_request"}
    assert events["pull_request"]["types"] == ["ready_for_review"]
    assert (
        events["workflow_call"]["inputs"]["validated-head"]["required"] is True
    )
    assert workflow["permissions"] == {}
    assert job["permissions"] == {"actions": "read", "pull-requests": "read"}
    assert 0 < job["timeout-minutes"] <= 5
    assert workflow["concurrency"]["cancel-in-progress"] is False
    group = workflow["concurrency"]["group"]
    assert "pull_request.number" in group
    assert "event_name" not in group
    assert "run_id" not in group
    # A checkout or arbitrary shell step would expose the owner credential.
    for step in job["steps"]:
        assert step["uses"].startswith("actions/github-script@")
        assert "run" not in step
        assert step["with"]["retries"] == 0
    caller = yaml.safe_load(
        (repo_root / ".github/workflows/ansible.yml").read_text()
    )["jobs"]["copilot_review"]
    assert caller["needs"] == "ci"
    assert "needs.ci.result == 'success'" in caller["if"]
    assert caller["uses"] == "./.github/workflows/copilot-review.yml"
    assert (
        caller["with"]["validated-head"]
        == "${{ github.event.pull_request.head.sha }}"
    )
