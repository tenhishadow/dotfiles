# AGENTS.md

## Scope

- This file applies to `roles/system/vars/`.
- `archlinux.yml` contains Arch-specific role variables.
- `archlinux-packages.yml` is the Arch Linux package manifest used by the
  `pkg` tagged package install task.

## Current Migration Rule

- Do not add, remove, rename, reorder, or regroup packages for the
  `AGENTS.md` migration.

## Package Rules For Future Work

- Verify package names against current Arch Linux repositories before
  finalizing changes.
- Prefer official repository packages.
- Do not add AUR-only packages unless AUR support is explicitly implemented.
- Keep commented AUR notes as comments only.
- Preserve existing package categories.
- Preserve the custom fold markers and keep them balanced.
- Keep Kubernetes-related packages in the `kubernetes` fold category.
- Do not store secrets in vars files.

## Validate

- Run `go-task lint`.
- If `yamllint` is already available, run `yamllint .`.
- Remember that `go-task test:system` runs with `--skip-tags pkg`, so it does
  not prove package availability.

## Done Means

- Vars stay deterministic, syntax-clean, and consistent with the current
  package manifest conventions.
