# browser_policies

Opt-in role for managing Linux browser and VS Code enterprise policies as
root-owned system configuration.

This role writes policy files under `/etc`. It does not manage runtime browser
profiles, cookies, history, cache, session state, local storage, VS Code user
settings, or VS Code workspace settings.

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
| VS Code | Owns the complete `/etc/vscode/policy.json` file for each enabled target. |

System policy files should stay root-owned and should not be symlinked back
into `$HOME`.

## Variables

Set host-specific overrides in `inventory/host_vars/this_host.yml`.

Key defaults:

```yaml
browser_policies_enabled: true
browser_policies_state: present

browser_policies_chromium_enabled: true
browser_policies_firefox_enabled: true
browser_policies_vscode_enabled: true

browser_policies_extension_lockdown_enabled: true
browser_policies_extension_block_message: "Extensions are managed by dotfiles."
browser_policies_chromium_policy_filename: "10-tenhishadow-managed.json"
browser_policies_chromium_extension_settings: {}
browser_policies_firefox_extension_settings: {}
browser_policies_vscode_allowed_extensions: {}
```

## Chromium-Based Browsers

Add targets to `browser_policies_chromium_targets`. Each item writes one JSON
file into that browser's managed policy directory.

```yaml
browser_policies_chromium_targets:
  - name: brave
    enabled: true
    managed_dir: /etc/brave/policies/managed
    policy_filename: "10-tenhishadow-managed.json"
    policies:
      BraveRewardsDisabled: true
  - name: chromium
    enabled: true
    managed_dir: /etc/chromium/policies/managed
    policy_filename: "10-tenhishadow-managed.json"
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

## Validation

After applying, verify policies in the relevant applications:

- Brave or Chromium: `brave://policy` and `brave://management`
- Firefox-compatible browsers: `about:policies`
- VS Code: Settings UI managed-value lock icons
- VS Code logs: Command Palette, `Show Window Log`

For repository validation, run:

```bash
go-task lint
go-task browser-policies:check
git diff --check
```

## Rollback

Set `browser_policies_state: absent` for managed policy removal, or revert the
role and inventory changes in git and reapply:

```bash
go-task browser-policies
```

Removing policy files does not remove data already stored in browser or VS Code
profiles.

## Risks

- Extension lockdown can block or remove extensions that are not declared in
  code.
- Password-manager policy changes do not necessarily delete passwords already
  saved in existing browser profiles.
- Existing policy files at role-owned paths are replaced by rendered output.
