# Privacy Policy Surfaces

This repository manages a personal Arch Linux workstation baseline. Privacy
settings here are personal defaults, not a generic security benchmark.

## Managed Surfaces

| Tool or area | Surface | Managed path |
| ------------ | ------- | ------------ |
| Gemini CLI | User settings and environment variables | `~/.gemini/settings.json`, `.bashrc`, `environment.d` |
| Chromium/Brave | Enterprise policy | `/etc/brave/policies/managed/10-dotfiles-managed.json` |
| Firefox | Enterprise policy | `/etc/firefox/policies/policies.json` |
| Thunderbird | Enterprise policy | `/etc/thunderbird/policies/policies.json` |
| VS Code | Enterprise policy | `/etc/vscode/policy.json` |
| K9s | User dotfile | `~/.config/k9s/config.yaml` |
| Git Delta | Git config | `~/.gitconfig` |
| Terraform CLI | User CLI config | `~/.terraformrc` |
| bat | User dotfile | `~/.config/bat/config` |
| ripgrep | User dotfile plus shell export | `~/.config/ripgrep/ripgreprc` |
| btop | User dotfile | `~/.config/btop/btop.conf` |
| direnv | User dotfile plus Bash hook | `~/.config/direnv/direnv.toml`, `.bashrc` |
| npm | User dotfile | `~/.npmrc` |
| Yarn | User dotfile and environment variable | `~/.yarnrc`, `environment.d` |
| pip | User dotfile | `~/.config/pip/pip.conf` |

The managed values prefer opt-outs for telemetry, usage statistics, prompts,
surveys, feedback, in-app messages, update notifiers, and prompt logging where
the tool exposes a documented setting.

## AI Client Notes

Gemini CLI has an official user settings file at `~/.gemini/settings.json`.
The managed file disables automatic updates, update notifications, usage
statistics, telemetry, detailed telemetry traces, prompt logging, and external
collector use. The shell environment also sets documented Gemini telemetry
variables to disabled values. The committed key names were checked against the
installed `@google/gemini-cli 0.41.2` bundled reference docs; the online Gemini
CLI docs also document the user settings file, usage statistics opt-out, and
telemetry environment variables.

This repository does not manage Gemini API keys, OAuth state, Google Cloud
credentials, local conversation history, MCP server credentials, extension
state, or project `.gemini` directories. Those files are account, project, or
runtime state and must stay out of git.

K9s is intentionally read-only by default through `readOnly: true`. This is an
operational guard, not just a privacy setting, and it does not manage
kubeconfig, cluster context history, namespace history, cluster names, or
tokens.

Git Delta is configured as the Git pager and interactive diff filter. That
assumes `delta` is installed; `go-task doctor` reports its availability.

npm sets `audit=false` as a privacy-first trade-off to avoid registry audit
submission by default. Run `npm audit` explicitly inside project workflows when
you want that signal.

Yarn Classic is managed through `~/.yarnrc`. `YARN_ENABLE_TELEMETRY=false`
applies only to Yarn versions that honor the modern telemetry environment
variable; this repository does not manage Yarn Berry `.yarnrc.yml` files.

Terraform checkpoint calls are disabled in the managed CLI config for privacy.
That also disables HashiCorp upgrade and security bulletin checks from the CLI;
run explicit provider and Terraform update review when you want that signal.

Thunderbird policy keys are checked against the official Thunderbird policy
templates. The managed in-app notification keys are version-specific and require
Thunderbird 139 or newer.

No managed Cursor, Windsurf, or other AI-client config was added because those
clients are not currently represented in the package manifest or existing
dotfile mappings. Add only documented, non-secret config surfaces if those
tools are introduced later.

## Deliberately Not Managed

- Kubeconfigs, cluster tokens, K9s cluster context history, and namespace
  history.
- Browser, Thunderbird, and VS Code runtime profiles.
- Mail accounts, local mail cache, address books, calendars, cookies, and
  sessions.
- Terraform Cloud tokens, provider credentials, private registry mirrors, and
  internal hostnames.
- npm, Yarn, and pip registry credentials or private indexes.
- Yarn Berry `.yarnrc.yml` files. The managed package is Yarn Classic, so this
  repository manages Classic `.yarnrc` and the documented modern telemetry
  environment variable only.
- TFLint, SQLFluff, and ShellCheck global rule configs. Project-level config is
  less surprising for linters that can change build or review outcomes.

## Verification

- Dotfiles dry run: `go-task dotfiles:check`
- Policy dry run: `go-task browser-policies:check`
- Local reports: `go-task doctor`, `go-task dotfiles:plan`,
  `go-task system:report`, `go-task browser-policies:report`
- Browser policies: `brave://policy`, `about:policies`, Thunderbird
  Troubleshooting Information, and VS Code managed-setting indicators

Official references used for these surfaces include:

- Gemini CLI configuration and telemetry:
  <https://google-gemini.github.io/gemini-cli/docs/get-started/configuration.html>
  and <https://google-gemini.github.io/gemini-cli/docs/cli/telemetry.html>
- Thunderbird policy templates:
  <https://thunderbird.github.io/policy-templates/templates/esr140/>
- Terraform CLI configuration:
  <https://developer.hashicorp.com/terraform/cli/config/config-file>
- Git Delta configuration:
  <https://dandavison.github.io/delta/configuration.html>
- K9s configuration:
  <https://github.com/derailed/k9s/blob/master/README.md>
- bat configuration:
  <https://github.com/sharkdp/bat>
- btop configuration:
  <https://github.com/aristocratos/btop>
- ripgrep configuration:
  <https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md>
- direnv shell hook:
  <https://direnv.net/docs/hook.html>
- npm configuration:
  <https://docs.npmjs.com/cli/v9/using-npm/config/>
- Yarn Classic configuration:
  <https://classic.yarnpkg.com/lang/en/docs/yarnrc/>
- Yarn Berry telemetry:
  <https://yarnpkg.com/advanced/telemetry>
- pip configuration:
  <https://pip.pypa.io/en/stable/topics/configuration/>
