# browser_policies

Manage Linux browser and VS Code enterprise policies as code.

This role writes root-owned files under `/etc/...` because enterprise
policies are system configuration, not user profile state. It intentionally
does not manage runtime browser profiles such as
`~/.config/BraveSoftware/`, `~/.config/chromium/`, or
`~/.mozilla/firefox/`, and it does not manage VS Code user or workspace
state under `~/.config/Code*`.

System policy paths should stay root-owned and should not be symlinked back
into `$HOME`. This keeps the install explicit, auditable, and aligned with
how browsers load enterprise policy on Linux.

Firefox note: this role owns the complete generated
`/etc/firefox/policies/policies.json` file for each enabled Firefox target.
If a file already exists there, running this role will replace it with the
rendered policy document.

VS Code note: this role owns the complete generated
`/etc/vscode/policy.json` file for each enabled VS Code target.

## Usage

Apply:

```bash
go-task browser-policies -- -K
```

Dry run:

```bash
go-task browser-policies:check -- -K
```

## Verification

- `brave://policy`
- `brave://management`
- `about:policies`
- VS Code Settings should show managed values with a lock icon
- VS Code Command Palette: `Show Window Log`

## Variables

Edit variables in inventory, for example
`inventory/host_vars/this_host.yml`, to override role defaults.

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

## Adding Chromium-Based Browsers

Add another item to `browser_policies_chromium_targets`. Each target writes
one generated JSON file into its own managed policy directory.

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

This target list approach also works for `google-chrome`,
`microsoft-edge`, `vivaldi`, and other Chromium-based browsers with their
own managed policy directories.

## Adding Firefox-Based Browsers

Add another item to `browser_policies_firefox_targets`. Each target writes a
complete `policies.json` file at the declared system path.

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

This target list approach also works for other Firefox-based browsers such
as `zen-browser` when they support the same enterprise policy file format.

## Managing VS Code

VS Code Linux policy is written as `/etc/vscode/policy.json`. The role
stores policy values by enterprise policy name, for example `UpdateMode`,
`TelemetryLevel`, and `EnableFeedback`.

```yaml
browser_policies_vscode_targets:
  - name: vscode
    enabled: true
    policy_path: /etc/vscode/policy.json
    policies:
      UpdateMode: manual
```

The role renders `AllowedExtensions` for you from a normal mapping variable,
because VS Code expects this specific policy value as a JSON string inside the
outer `policy.json` document.

```yaml
browser_policies_vscode_allowed_extensions:
  "*": false
  vscodevim.vim: stable
  golang.go: true
  rust-lang.rust-analyzer:
    - "5.0.0@linux-x64"
```

If you do not want to restrict extensions, leave
`browser_policies_vscode_allowed_extensions: {}`.

## Managing Extensions

Extension policy is controlled through dedicated variables. With
`browser_policies_extension_lockdown_enabled: true`, the role merges a
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

To switch an extension from `normal_installed` to `force_installed`, change
only its `installation_mode` value in the matching extension settings
mapping.

## Warnings

- Extension lockdown can block or remove extensions that are not listed in
  code.
- Disabling password managers through enterprise policy does not necessarily
  delete passwords already saved in existing browser profiles.
- This role intentionally does not manage cookies, history, sessions, cache,
  local storage, VS Code user settings, VS Code workspace settings, or any
  other runtime profile state.
