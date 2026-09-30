# Scope

Applies to `roles/system/vars/`.

The root and parent `AGENTS.md` files own shared role and validation rules.

- `archlinux.yml` contains Arch-specific role variables.
- `archlinux-packages.yml` is the Arch Linux package manifest used by the
  `pkg` tagged package install task.

## Package Rules

- Verify package names against current Arch Linux repositories before
  finalizing package changes.
- Package availability is an online compatibility check against rolling Arch
  metadata. A passing query does not prove installation or service behavior.
- Prefer official repository packages.
- Do not add AUR-only packages unless AUR support is explicitly implemented.
- Keep AUR helper build dependency variables separate from
  `archlinux-packages.yml`, and ensure related tasks use tag `aur`.
- Keep commented AUR notes as comments only.
- Preserve existing package categories unless a regrouping is explicitly
  requested.
- Preserve custom fold markers and keep them balanced.
- Keep Kubernetes-related packages in the `kubernetes` fold category.

## Validation

Use the root matrix for variable changes. For package manifest changes, run
`go-task test:system` when Docker is available: it validates names against a
fresh Arch container before the smoke and idempotency pass. Documentation-only
edits need documentation checks.

## Done Criteria

- Vars stay deterministic, syntax-clean, and consistent with package manifest
  conventions.
- Package changes are explicit and reviewable.
