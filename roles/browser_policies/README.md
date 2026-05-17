# browser_policies

Opt-in role for managing Linux browser, Thunderbird, and VS Code enterprise
policies as root-owned system configuration.

This role writes policy files under `/etc`. It does not manage runtime browser
or mail profiles, cookies, history, cache, session state, local storage, mail
accounts, address books, calendars, VS Code user settings, or VS Code workspace
settings.

## Usage

Dry-run policy changes:

```bash
go-task browser-policies:check
```

Apply policy changes:

```bash
go-task browser-policies
```

The playbook uses sudo because policy files are system configuration.

## Managed Policy Targets

| Target family | Managed path behavior |
| ------------- | --------------------- |
| Chromium-based browsers | Writes one generated JSON file under each target managed policy directory. |
| Firefox-based browsers | Owns the complete `policies.json` file for each enabled target. |
| Thunderbird | Owns the complete `policies.json` file for each enabled target. |
| VS Code | Owns the complete `/etc/vscode/policy.json` file for each enabled target. |

System policy files should stay root-owned and should not be symlinked back
into `$HOME`. Policy file writes create Ansible backups before replacing
role-owned files.

## Variables

Set host-specific overrides in
`inventory/host_vars/this_host/browser_policies.yml`.

Key defaults:

```yaml
browser_policies_enabled: true
browser_policies_state: present

browser_policies_chromium_enabled: true
browser_policies_firefox_enabled: true
browser_policies_thunderbird_enabled: true
browser_policies_vscode_enabled: true

browser_policies_extension_lockdown_enabled: true
browser_policies_extension_block_message: "Extensions are managed by dotfiles."
browser_policies_chromium_policy_filename: "10-dotfiles-managed.json"
browser_policies_chromium_extension_settings: {}
browser_policies_firefox_extension_settings: {}
browser_policies_thunderbird_extension_settings: {}
browser_policies_vscode_allowed_extensions: {}
```

Public role variables use the `browser_policies_` prefix. Target entries use
short, stable keys:

| Target family | Path key |
| ------------- | -------- |
| Chromium-based browsers | `policy_dir` |
| Firefox-based browsers | `policy_path` |
| Thunderbird | `policy_path` |
| VS Code | `policy_path` |

The task files normalize enabled targets into generated policy file specs
internally before shared file tasks write or remove policy files.

## Chromium-Based Browsers

Add targets to `browser_policies_chromium_targets`. Each item writes one JSON
file into that browser's managed policy directory.

```yaml
browser_policies_chromium_targets:
  - name: brave
    enabled: true
    policy_dir: /etc/brave/policies/managed
    policy_filename: "10-dotfiles-managed.json"
    policies:
      BraveRewardsDisabled: true
  - name: chromium
    enabled: true
    policy_dir: /etc/chromium/policies/managed
    policy_filename: "10-dotfiles-managed.json"
    policies: {}
```

The same target pattern works for `google-chrome`, `microsoft-edge`,
`vivaldi`, and other Chromium-based browsers with a Linux managed policy
directory.

## Firefox-Based Browsers

Add targets to `browser_policies_firefox_targets`. Each item owns the complete
policy file at `policy_path`.

```yaml
browser_policies_firefox_targets:
  - name: firefox
    enabled: true
    policy_path: /etc/firefox/policies/policies.json
  - name: librewolf
    enabled: true
    policy_path: /etc/librewolf/policies/policies.json
    policies: {}
```

The same target pattern works for other Firefox-based browsers when they
support the Firefox enterprise policy file format.

## Thunderbird

Thunderbird policy support uses the official `policies.json` surface and owns
the complete file at `policy_path`. The default target is
`/etc/thunderbird/policies/policies.json`.

```yaml
browser_policies_thunderbird_targets:
  - name: thunderbird
    enabled: true
    policy_path: /etc/thunderbird/policies/policies.json
```

The default Thunderbird policy keys are verified against the official
Thunderbird policy templates. They disable telemetry, DNS prefetching,
login-save prompts, password-manager access, and in-app donation, survey, and
message notifications where supported by the installed Thunderbird version. The
`InAppNotification_*` keys require Thunderbird 139 or newer.

This role does not manage mail accounts, profile data, saved passwords, local
mail cache, extensions installed inside a runtime profile, address books,
calendars, cookies, or sessions.

## VS Code

VS Code policy is stored as `/etc/vscode/policy.json`. Policy keys use the
enterprise policy names, for example `UpdateMode`, `TelemetryLevel`, and
`EnableFeedback`.

```yaml
browser_policies_vscode_targets:
  - name: vscode
    enabled: true
    policy_path: /etc/vscode/policy.json
    policies:
      UpdateMode: manual
```

`AllowedExtensions` is rendered from a normal mapping because VS Code expects
that policy value as a JSON string inside the outer `policy.json` document.

```yaml
browser_policies_vscode_allowed_extensions:
  "*": false
  vscodevim.vim: stable
  golang.go: true
  rust-lang.rust-analyzer:
    - "5.0.0@linux-x64"
```

Use an empty mapping to avoid restricting extensions:

```yaml
browser_policies_vscode_allowed_extensions: {}
```

## Extension Policy

When `browser_policies_extension_lockdown_enabled: true`, the role merges a
default wildcard block entry:

```yaml
"*":
  installation_mode: blocked
  blocked_install_message: "Extensions are managed by dotfiles."
```

Chromium example with uBlock Origin allowed but not force-installed:

```yaml
browser_policies_chromium_extension_settings:
  "*":
    installation_mode: blocked
    blocked_install_message: "Extensions are managed by dotfiles."
  cjpalhdlnbpafiamejdnhcphjbkeiagm:
    installation_mode: normal_installed
    update_url: "https://clients2.google.com/service/update2/crx"
```

Firefox example with uBlock Origin force-installed:

```yaml
browser_policies_firefox_extension_settings:
  "*":
    installation_mode: blocked
    blocked_install_message: "Extensions are managed by dotfiles."
  uBlock0@raymondhill.net:
    installation_mode: force_installed
    install_url: "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
```

Thunderbird uses the same extension policy merge model:

```yaml
browser_policies_thunderbird_extension_settings:
  "*":
    installation_mode: blocked
    blocked_install_message: "Extensions are managed by dotfiles."
```

## Validation

After applying, verify policies in the relevant applications:

- Brave or Chromium: `brave://policy` and `brave://management`
- Firefox-compatible browsers: `about:policies`
- Thunderbird: Troubleshooting Information, then Enterprise Policies
- VS Code: Settings UI managed-value lock icons
- VS Code logs: Command Palette, `Show Window Log`

For repository validation, run:

```bash
go-task lint
go-task browser-policies:check
go-task verify
git diff --check
```

The role validates common variables, target shapes, target names, absolute
policy paths, and generated policy file specs before writing system files.

## Rollback

Set `browser_policies_state: absent` for managed policy removal, inspect
Ansible backups for replaced policy files, or revert the role and inventory
changes in git and reapply:

```bash
go-task browser-policies
```

Removing policy files does not remove data already stored in browser,
Thunderbird, or VS Code profiles.

## Risks

- Extension lockdown can block or remove extensions that are not declared in
  code.
- Password-manager policy changes do not necessarily delete passwords already
  saved in existing browser or Thunderbird profiles.
- Existing policy files at role-owned paths are backed up and replaced by
  rendered output.
