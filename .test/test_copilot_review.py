"""Exercise the owner and quota boundaries of the Copilot review workflow."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/copilot-review.yml").read_text())
JOB = WORKFLOW["jobs"]["request"]
SCRIPT = next(step["with"]["script"] for step in JOB["steps"] if "with" in step)
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


def scenario(*, ready: bool = False) -> dict:
    """Build valid GitHub metadata; individual cases vary one trust boundary."""

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
        "script": SCRIPT,
        "jobIf": JOB["if"],
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
        "jobs": [{"name": "ci", "status": "completed", "conclusion": "success"}],
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


class CopilotReviewTest(unittest.TestCase):
    """Run the real inline JavaScript without network or user credentials."""

    def execute(self, fixture: dict) -> dict:
        """Supply only synthetic API responses and a minimal Node environment."""

        result = subprocess.run(
            ["node", "-e", HARNESS],
            input=json.dumps(fixture),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            env={"PATH": os.environ.get("PATH", os.defpath)},
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def assert_skipped(self, fixture: dict) -> None:
        """An ineligible PR must not even instantiate the owner-token client."""

        result = self.execute(fixture)
        self.assertEqual([], result["requests"])
        self.assertEqual([], result["failures"])
        self.assertNotIn({"method": "getOctokit"}, result["calls"])

    def test_owner_review_is_requested_once_after_successful_current_ci(self) -> None:
        fixture = scenario()
        fixture["repeats"] = 2

        result = self.execute(fixture)

        self.assertEqual([], result["failures"])
        self.assertEqual(
            [
                {
                    "owner": OWNER,
                    "repo": "repository",
                    "pull_number": 7,
                    "reviewers": ["copilot-pull-request-reviewer[bot]"],
                }
            ],
            result["requests"],
        )
        # The reusable workflow executes after ci, before its caller completes.
        self.assertFalse(
            any(call["method"] == "listWorkflowRuns" for call in result["calls"])
        )

    def test_rejects_foreign_actors_and_untested_or_stale_heads(self) -> None:
        for case in (
            "actor",
            "rerunner",
            "event",
            "untested",
            "event_head",
            "validated_head",
        ):
            with self.subTest(case=case):
                fixture = scenario()
                if case == "actor":
                    fixture["context"]["actor"] = "outsider"
                elif case == "rerunner":
                    fixture["env"]["TRIGGERING_ACTOR"] = "outsider"
                elif case == "event":
                    fixture["context"]["eventName"] = "push"
                elif case == "untested":
                    fixture["env"]["VALIDATED_HEAD"] = ""
                elif case == "event_head":
                    fixture["context"]["payload"]["pull_request"]["head"]["sha"] = (
                        "b" * 40
                    )
                else:
                    fixture["env"]["VALIDATED_HEAD"] = "b" * 40
                self.assert_skipped(fixture)

    def test_draft_made_ready_during_ci_uses_current_pull_request_state(self) -> None:
        fixture = scenario()
        fixture["context"]["payload"]["pull_request"]["draft"] = True

        result = self.execute(fixture)

        self.assertEqual(1, len(result["requests"]))
        self.assertEqual([], result["failures"])

    def test_disabled_review_setting_never_requests_a_review(self) -> None:
        fixture = scenario()
        fixture["enabled"] = "false"
        self.assert_skipped(fixture)

    def test_rejects_external_draft_closed_and_fork_pull_requests(self) -> None:
        for key, value in (
            ("draft", True),
            ("state", "closed"),
            ("user", {"login": "outsider"}),
        ):
            with self.subTest(field=key):
                fixture = scenario()
                fixture["pr"][key] = value
                self.assert_skipped(fixture)
        for side, repository in (
            ("head", {"full_name": "outsider/repository", "fork": True}),
            ("head", {**REPOSITORY, "fork": True}),
            ("base", {"full_name": "owner/other"}),
        ):
            with self.subTest(side=side, repository=repository):
                fixture = scenario()
                fixture["pr"][side]["repo"] = repository
                self.assert_skipped(fixture)

    def test_latest_ci_rejects_queue_cancellation_and_foreign_actors(self) -> None:
        for key, value in (
            ("status", "queued"),
            ("conclusion", "failure"),
            ("conclusion", "cancelled"),
            ("actor", {"login": "outsider"}),
            ("triggering_actor", {"login": "outsider"}),
            ("head_repository", {"full_name": "outsider/repository"}),
            ("head_sha", "b" * 40),
        ):
            with self.subTest(field=key, value=value):
                fixture = scenario(ready=True)
                fixture["runs"][0][key] = value
                self.assert_skipped(fixture)
        fixture = scenario(ready=True)
        fixture["runs"] = []
        self.assert_skipped(fixture)

    def test_ready_after_draft_skip_does_not_wait_for_parent_finalization(self) -> None:
        draft = scenario()
        draft["pr"]["draft"] = True
        self.assert_skipped(draft)

        ready = scenario(ready=True)
        ready["runs"][0].update(status="in_progress", conclusion=None)
        result = self.execute(ready)

        self.assertEqual(1, len(result["requests"]))
        self.assertEqual([], result["failures"])

    def test_ready_requires_successful_ci_job_from_latest_attempt(self) -> None:
        for jobs in (
            [],
            [{"name": "ci", "status": "in_progress", "conclusion": None}],
            [{"name": "ci", "status": "queued", "conclusion": None}],
            [{"name": "ci", "status": "completed", "conclusion": "failure"}],
            [{"name": "ci", "status": "completed", "conclusion": "cancelled"}],
            [{"name": "ci", "status": "completed", "conclusion": "skipped"}],
            [{"name": "static-checks", "status": "completed", "conclusion": "success"}],
        ):
            with self.subTest(jobs=jobs):
                fixture = scenario(ready=True)
                fixture["runs"][0].update(status="in_progress", conclusion=None)
                fixture["oldJobs"] = fixture["jobs"]
                fixture["jobs"] = jobs
                self.assert_skipped(fixture)

    def test_existing_or_pending_copilot_id_prevents_another_request(self) -> None:
        for field, value in (("pending", [BOT]), ("reviews", [{"user": BOT}])):
            with self.subTest(field=field):
                fixture = scenario()
                fixture[field] = value
                self.assert_skipped(fixture)

    def test_ready_for_review_uses_existing_ci_and_rejects_other_actors(self) -> None:
        fixture = scenario(ready=True)
        result = self.execute(fixture)
        self.assertEqual(1, len(result["requests"]))
        self.assertEqual([], result["failures"])
        query = next(
            call["options"]
            for call in result["calls"]
            if call["method"] == "listWorkflowRuns"
        )
        self.assertEqual("ansible.yml", query["workflow_id"])
        self.assertEqual("pull_request", query["event"])
        self.assertEqual(fixture["pr"]["head"]["sha"], query["head_sha"])
        jobs_query = next(
            call["options"]
            for call in result["calls"]
            if call["method"] == "listJobsForWorkflowRun"
        )
        self.assertEqual(fixture["runs"][0]["id"], jobs_query["run_id"])
        self.assertEqual("latest", jobs_query["filter"])
        for field in ("actor", "triggering_actor", "action"):
            with self.subTest(field=field):
                fixture = scenario(ready=True)
                if field == "actor":
                    fixture["context"]["actor"] = "outsider"
                elif field == "triggering_actor":
                    fixture["env"]["TRIGGERING_ACTOR"] = "outsider"
                else:
                    fixture["context"]["payload"]["action"] = "opened"
                self.assert_skipped(fixture)

    def test_missing_token_or_wrong_identity_fails_without_requesting(self) -> None:
        for case in ("missing", "other_user", "bot"):
            with self.subTest(case=case):
                fixture = scenario()
                if case == "missing":
                    del fixture["env"]["COPILOT_REVIEW_TOKEN"]
                elif case == "other_user":
                    fixture["identity"]["login"] = "outsider"
                else:
                    fixture["identity"]["type"] = "Bot"
                result = self.execute(fixture)
                self.assertEqual([], result["requests"])
                self.assertEqual(1, len(result["failures"]))

    def test_rechecks_live_pull_request_before_spending(self) -> None:
        for key, value in (
            ("draft", True),
            ("state", "closed"),
            ("head", {"repo": REPOSITORY, "sha": "b" * 40}),
        ):
            with self.subTest(field=key):
                fixture = scenario()
                fixture["current"] = copy.deepcopy(fixture["pr"])
                fixture["current"][key] = value
                result = self.execute(fixture)
                self.assertEqual([], result["requests"])
                self.assertEqual([], result["failures"])

    def test_workflow_keeps_execution_metadata_only_and_bounded(
        self,
    ) -> None:
        # PyYAML's YAML 1.1 loader treats GitHub's unquoted "on" key as True.
        events = WORKFLOW[True]
        self.assertEqual({"workflow_call", "pull_request"}, set(events))
        self.assertEqual(["ready_for_review"], events["pull_request"]["types"])
        self.assertIs(
            True, events["workflow_call"]["inputs"]["validated-head"]["required"]
        )
        self.assertEqual({}, WORKFLOW["permissions"])
        self.assertEqual(
            {"actions": "read", "pull-requests": "read"}, JOB["permissions"]
        )
        self.assertGreater(JOB["timeout-minutes"], 0)
        self.assertLessEqual(JOB["timeout-minutes"], 5)
        self.assertIs(False, WORKFLOW["concurrency"]["cancel-in-progress"])
        self.assertIn("pull_request.number", WORKFLOW["concurrency"]["group"])
        self.assertNotIn("event_name", WORKFLOW["concurrency"]["group"])
        self.assertNotIn("run_id", WORKFLOW["concurrency"]["group"])
        self.assertIn("vars.COPILOT_REVIEW_ENABLED == 'true'", JOB["if"])
        self.assertEqual(1, len(JOB["steps"]))
        step = JOB["steps"][0]
        self.assertTrue(step["uses"].startswith("actions/github-script@"))
        self.assertNotIn("run", step)
        self.assertEqual(0, step["with"]["retries"])
        caller = yaml.safe_load((ROOT / ".github/workflows/ansible.yml").read_text())[
            "jobs"
        ]["copilot_review"]
        self.assertEqual("ci", caller["needs"])
        self.assertIn("needs.ci.result == 'success'", caller["if"])
        self.assertEqual("./.github/workflows/copilot-review.yml", caller["uses"])
        self.assertEqual(
            "${{ github.event.pull_request.head.sha }}",
            caller["with"]["validated-head"],
        )


if __name__ == "__main__":
    unittest.main()
