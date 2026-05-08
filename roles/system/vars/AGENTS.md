# Scope

Applies to `roles/system/vars/`.

- `archlinux.yml` contains Arch-specific role variables.
- `archlinux-packages.yml` is the Arch Linux package manifest used by the
  `pkg` tagged package install task.

## Package Rules

- Verify package names against current Arch Linux repositories before
  finalizing package changes.
- Prefer official repository packages.
- Do not add AUR-only packages unless AUR support is explicitly implemented.
- Keep commented AUR notes as comments only.
- Preserve existing package categories unless a regrouping is explicitly
  requested.
- Preserve custom fold markers and keep them balanced.
- Keep Kubernetes-related packages in the `kubernetes` fold category.
- Keep comments and category names in English.
- Do not store secrets in vars files.

## Validation

- Run `go-task lint`.
- Run `uv run yamllint .` or `go-task yamllint`.
- Remember that `go-task test:system` runs with `--skip-tags pkg`; it does not
  prove package availability.

## Done Criteria

- Vars stay deterministic, syntax-clean, and consistent with package manifest
  conventions.
- Package changes are explicit and reviewable.
