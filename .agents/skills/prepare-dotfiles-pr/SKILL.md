---
name: prepare-dotfiles-pr
description: >-
  Prepare coherent Conventional Commits and a factual pull request for this
  dotfiles repository. Use when organizing changes for commit, committing an
  authorized scope, or preparing or publishing a PR. Publication follows the
  current session's authorization.
---

# Prepare Dotfiles Commits And Pull Requests

## Scope

Run from the repository root; paths below remain repository-relative when
this skill is loaded through a provider symlink. Read `AGENTS.md` and the
applicable nested instructions. `CONTRIBUTING.md` owns branch, commit, squash,
release, and handoff policy; `.commitlintrc.yaml` owns accepted message syntax.

Distinguish authorization to commit, push, create or update a PR, and merge.
Use the current session's scope, including an explicit later change to an
earlier restriction; do not request the same permission again. Preparation
alone produces local artifacts. Finish authorized local work before reporting
an uncovered publication step; invoking this skill grants no extra permission.

## Prepare The Change

1. Inspect the current branch, working tree, index, recent history, upstream,
   and chosen base. Read staged and unstaged diffs and untracked files. When
   remote access is available, inspect an existing PR for this branch before
   proposing another one; retain the user's selected branch and base.
2. Review the entire intended PR against its base, including existing commits.
   Group changes by coherent behavior and keep dependent code, locks, tests,
   and documentation together. One commit is reasonable for one coupled change;
   do not split by file type merely to increase commit count. Include existing
   dirty work when the user explicitly requests all current changes; otherwise
   preserve changes outside the requested scope. Do not rewrite published
   history or replace the index to manufacture clean groups.
3. Select validation through the root matrix and reuse results while the
   tested files and dependencies remain unchanged. Run the existing
   `detect-secrets` and `detect-private-key` pre-commit hooks against candidate
   files, and `go-task lint:english`. Check new files, symlink targets, lockfile
   contents, and generated or machine-local state before staging. Do not add
   suppressions merely to make publication pass.
4. Stage only the chosen paths or hunks, then inspect the actual
   `git diff --cached` and `git diff --cached --check`. Confirm the staged
   content matches the proposed message and excludes unintended files. A clean
   worktree diff does not substitute for reviewing the index.

## Commit And Describe

Use the locked local commitlint tool, without an implicit latest-version fetch:

```bash
npm ci --prefix .github/tools/commitlint --ignore-scripts --no-audit --no-fund
```

Write each exact proposed message to a temporary file and set
`commit_message_file` to its path. Validate it from the repository root:

```bash
NODE_PATH="$PWD/.github/tools/commitlint/node_modules" \
  .github/tools/commitlint/node_modules/.bin/commitlint \
  --config .commitlintrc.yaml --strict --edit "$commit_message_file"
```

When commits are authorized, commit the reviewed index with that message file.
If a hook changes files, review and stage those changes before retrying; do not
bypass a failed hook. Verify the resulting commit and remaining working tree.

Preserve configured commit signing. If a signing key is unavailable or locked,
keep the reviewed index and message file intact and report the required local
key unlock or signing-agent access. Do not silently disable signing or change
the signing identity to bypass the failure.

Build the PR description from `.github/pull_request_template.md` and the final
base-to-head diff. Explain the problem and resulting behavior, actual checks
and their limits, and meaningful migration or rollback needs. Record required
GitHub settings or App setup separately from local configuration changes.
Follow `CONTRIBUTING.md` for breaking-change titles and squash behavior; run
the same commitlint validator on the PR title through stdin.

## Publish Within Scope

Preserve title and body literally: use structured API arguments or write the
body to a temporary file and use `gh pr create` or `gh pr edit` with
`--body-file`. Supply the intended head and base explicitly when creating a
PR. Push or create/update the PR only when authorized; a local PR draft is a
complete preparation result when publication is outside scope.

On an authentication or policy failure, stop the blocked publication action
and report the exact blocker with the prepared artifacts. Do not retry with
different identities or repeatedly request an already granted permission.
Report actual commit IDs, the PR URL or local draft location, validation
results, remaining dirty files, and any unperformed publication or settings
step. Do not claim a local draft was published or a check passed if it skipped.
