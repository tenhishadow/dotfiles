# Contributing

Use the repository's [agent instructions](AGENTS.md) for editing boundaries
and validation selection, and the [README command catalog](README.md#common-tasks)
for supported commands. This guide owns the branch, commit, pull request, and
release workflow.

Agents can use the shared [prepare-dotfiles-pr skill](.agents/skills/prepare-dotfiles-pr/SKILL.md)
to turn the authorized change into reviewed commits and a factual PR draft.

## Branches

`master` is the default integration and release branch. Use a short-lived,
descriptive branch for a coherent change, such as `fix/chrony-resume` or
`chore/agent-workflow`; no permanent `develop` branch is needed. This follows
[GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow).

Start new work from the chosen integration base, normally current `master`.
When the user selects another base or asks to continue an existing branch,
preserve that choice. A stacked PR targets its prerequisite branch until that
work lands; review and validate its diff against that base.

Inspect the current branch and working tree before changing either. Do not
switch, reset, stash, rebase, or clean existing work merely to enforce a branch
name. Use a separate worktree when independent work needs another checkout.
Repository edits do not authorize committing, pushing, opening a PR, merging,
or applying workstation configuration.

## Commits And Pull Requests

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
for requested commits and PR titles. `.commitlintrc.yaml` is the executable
type and formatting policy; do not maintain another accepted-type list.
Choose a scope only when it identifies the changed area:

```text
fix(system): preserve chrony boot synchronization
docs(agents): clarify instruction discovery
chore(deps): refresh locked dependencies
feat(dotfiles)!: change the managed shell layout
```

The PR title describes the final change, including after its scope changes.
Keep unrelated work separate when practical, without discarding an existing
combined change the user explicitly asked to maintain. Use the
[PR template](.github/pull_request_template.md) to explain the problem,
resulting behavior, actual validation, and material rollback or adoption needs.
Remove irrelevant prompts; documentation edits do not need runtime checklists.

Merge by squash once the relevant checks and review are complete and merging
is authorized. GitHub settings verified on 2026-09-30 allow squash only, use
the PR title as the commit title, leave its body blank, and delete merged
branches automatically. Put `!` in a breaking-change PR title and describe
migration in the PR; a `BREAKING CHANGE` footer only in the PR description
will not survive that default squash message. Review the final merge message.
Start subsequent work from the integration branch instead of reusing a
squashed branch. See [GitHub's merge behavior](https://docs.github.com/en/pull-requests/reference/pull-request-merges).

Labels describe affected areas or triage state; they do not select the commit
type or release version. See the [label catalog](docs/github-labels.md).

Scheduled dependency maintenance reuses `chore/weekly-dependencies` while its
single update PR is open; it is the intentional exception to per-change branch
creation. The weekly workflow runs the same local updater across all managed
surfaces. Renovate PR creation stays disabled to avoid a competing update queue;
see [dependency maintenance](docs/dependency-updates.md) for setup, coverage,
and manual execution.

## Required Checks

The validation workflow exposes the stable required check `ci`; the separate
`pr-title` check validates the squash title, including title-only edits. Select
both in branch protection. The `ci` gate requires successful static and
complementary lint checks before integration jobs run; only integration checks
deliberately skipped by path selection may be absent. PR title validation also
runs first in the static job. After correcting a title that stopped CI, rerun
the failed CI run; title-only edits rerun `pr-title`, not the expensive pipeline.

The live `master` ruleset was updated and verified on 2026-09-30 to require
`ci` and `pr-title` from GitHub Actions. It retains strict up-to-date checks,
squash-only merges, and protection against branch deletion and force pushes.
When required check names change, migrate the ruleset as a separately
authorized GitHub settings change; local workflow edits do not update it.

## Copilot Review

`.github/workflows/copilot-review.yml` requests the initial automatic review
for an open, ready PR authored and triggered by the repository owner, with its
head in this repository. It runs after successful CI or when an already
validated draft becomes ready. Forks, external actors, bots, stale commits,
failed CI, and existing or pending Copilot reviews are excluded. The workflow
reads metadata only; it never checks out PR code or imports artifacts.

After the workflow reaches the default branch:

1. Set repository secret `COPILOT_REVIEW_TOKEN` to an owner-created fine-grained
   PAT scoped to this repository with **Pull requests: read and write** only.
   The ordinary Actions token reads CI metadata; the separate owner token
   requests the review. Do not reuse a broad release or local CLI token.
2. In GitHub's [Copilot review settings](https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-code-review),
   select **Lite** effort and enable custom instructions. Leave native
   automatic reviews, draft reviews, and review-on-push disabled; those
   independent triggers would bypass this workflow's author and fork filters.
   Keep approving reviews and MCP tool access disabled for this review-only
   setup. Suggested patches do not require cloud-agent fix sessions.
3. Set repository variable `COPILOT_REVIEW_ENABLED` to `true`. Set it to `false`
   to stop this workflow. Request any later re-review manually after reviewing
   the changes; it consumes additional quota.

Instruction brevity reduces unnecessary context, but it is not a spending
limit. Review usage depends on the subscription and work performed; configure
the account's [additional-usage budget](https://docs.github.com/en/billing/how-tos/set-up-budgets)
to stop paid overages. No token ceiling or review-effort field is exposed by
the [review-request API](https://docs.github.com/en/rest/pulls/review-requests#request-reviewers-for-a-pull-request).
The workflow cannot override personal settings or prevent separately requested
reviews. Copilot feedback supplements the required checks and owner review.

## Releases

`.github/workflows/release.yml` runs Release Please on pushes to `master`.
`release-please-config.json` selects the `simple` strategy and updates the
project version files; `.release-please-manifest.json` records the released
version. Preserve the generated release PR title, body, and lifecycle labels.
Merging that PR causes the next run to create the tag and GitHub release; it
does not deploy dotfiles or configure a workstation.

Release Please derives version changes from merged commit messages. Features,
fixes, and breaking changes carry release meaning; routine `chore(deps)`
updates do not independently request a release with the current strategy.
Use `fix(deps)` when an update actually fixes a user-visible defect. Do not
change a type merely to force a release or edit version state incidentally.
The workflow's `RELEASE_TOKEN` is managed as a GitHub secret so bot-created
PRs can trigger validation. Follow the upstream
[release workflow](https://github.com/googleapis/release-please)
and [token guidance](https://github.com/googleapis/release-please-action#github-credentials).

## Agent Collaboration

Follow the user's current execution scope and preserve unrelated dirty files.
Assign independent tasks explicit file ownership; coordinate shared-file edits
before writing. Worktrees are optional isolation, not permission to replace
the selected branch or discard work.

Before handing work back, inspect the combined affected diff and report changed
contracts, exact checks and results, remaining blockers, and any untested
runtime behavior. Reuse valid prior results and run shared-workspace checks
sequentially where required by `AGENTS.md`. Another agent's report is evidence
to assess, not proof that a check ran on the final files. Do not create commits,
pushes, PRs, comments, labels, or releases unless the user's scope authorizes
those actions.
