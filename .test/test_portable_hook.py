"""Black-box tests for the portable Codex hook contract."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "dotfiles/.codex/hooks/portable.py"
HOOKS_CONFIG = ROOT / "dotfiles/.codex/hooks.json"


def _event(command: str, *, tool_name: str = "Bash") -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_use_id": "tool-use-test",
            "tool_input": {"command": command},
        }
    )


def _run_hook(
    payload: str, *, optimized: bool = False
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", str(HOOK)))
    return subprocess.run(
        command,
        cwd=ROOT,
        input=payload,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


class PortableHookTest(unittest.TestCase):
    """Exercise policy decisions through the hook's JSON interface."""

    def test_manifest_uses_current_pre_tool_use_contract(self) -> None:
        config = json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))
        event = config["hooks"]["PreToolUse"]
        self.assertEqual(1, len(event))
        self.assertEqual("Bash", event[0]["matcher"])
        handlers = event[0]["hooks"]
        self.assertEqual(1, len(handlers))
        self.assertEqual("command", handlers[0]["type"])
        self.assertEqual("python3 ~/.codex/hooks/portable.py", handlers[0]["command"])

    def test_sensitive_and_destructive_commands_are_denied(self) -> None:
        token = "literal-" + "credential"
        deep_command = "rm -rf /"
        for _index in range(33):
            deep_command = f"echo $({deep_command})"
        commands = (
            "rm -rf /",
            "command rm -rf /",
            "env SAFE=yes /bin/rm --recursive --force /",
            "nice -n 5 /usr/bin/rm -fr /",
            "sudo -n rm -rf /",
            "sudo -- rm -rf /",
            "env --unset SAFE sudo --non-interactive /bin/rm --force --recursive /",
            "env -S 'rm -rf /'",
            "env --spl 'rm -rf /'",
            "env --spl='rm -rf /'",
            "env --split-string='rm -rf /'",
            "env -vS 'rm -rf /'",
            r"env -S 'rm\_-rf\_/'",
            "env -S '${DANGEROUS_COMMAND}'",
            "env -a safe-name rm -rf /",
            "env --argv0 safe-name rm -rf /",
            "exec rm -rf /",
            "exec -a safe-name rm -rf /",
            "time rm -rf /",
            "time -f elapsed rm -rf /",
            "timeout 30 rm -rf /",
            "stdbuf -oL rm -rf /",
            "setsid rm -rf /",
            "ionice rm -rf /",
            "chrt 1 rm -rf /",
            "watch rm -rf /",
            "strace rm -rf /",
            "busybox rm -rf /",
            "pkexec rm -rf /",
            "run0 rm -rf /",
            "doas rm -rf /",
            "doas -u root rm -rf /",
            "unshare rm -rf /",
            "setpriv --no-new-privs rm -rf /",
            "prlimit rm -rf /",
            "chroot /tmp/root rm -rf /",
            "bash -c 'rm -rf /'",
            "bash -O expand_aliases -c 'rm -rf /'",
            "bash -o errexit -c 'rm -rf /'",
            "sh -o errexit -c 'rm -rf /'",
            "bash -lc 'rm -rf /'",
            "bash -c -- 'rm -rf /'",
            "bash -c $'rm -rf /'",
            "bash -c 'rm \"$@\"' _ -rf /",
            "bash <<'EOF'\nrm -rf /\nEOF",
            "bash <<'EOF-X'\nrm -rf /\nEOF-X",
            "bash <<'E'OF\nrm -rf /\nEOF",
            "bash <<E\\OF\nrm -rf /\nEOF",
            "bash <<'EOF'\nrm -rf /",
            "sh <<< 'rm -rf /'",
            "sh <<< $'rm -rf /'",
            "printf 'rm -rf /\\n' | sh",
            "printf $'rm -rf /\\n' | sh",
            "printf 'rm -rf /\\n' | cat | sh",
            "printf %s 'rm -rf /' | sh",
            "printf %b 'rm\\x20-rf\\x20/\\n' | sh",
            "echo -n 'rm -rf /' | sh",
            "printf %s 'rm -rf /' | tee /dev/null | sh",
            "printf %s 'rm -rf /' | sed -n p | sh",
            "cat <<'EOF' | sh\nrm -rf /\nEOF",
            "sudo sh -lc 'rm -rf /'",
            "sudo -Eu root rm -rf /",
            "eval 'rm -rf /'",
            "eval $'rm -rf /'",
            "builtin eval 'rm -rf /'",
            "cmd='rm -rf /'; eval \"$cmd\"",
            "cmd='rm -rf /'; bash -c \"$cmd\"",
            "export cmd=rm; $cmd -rf /",
            "readonly cmd=rm; $cmd -rf /",
            "cmd=; ${cmd:=rm} -rf /",
            "unset cmd; ${cmd=rm} -rf /",
            "cmd=RM; ${cmd,,} -rf /",
            "cmd=rm; ref=cmd; ${!ref} -rf /",
            "echo $(rm -rf /)",
            'echo "$(rm -rf /)"',
            "echo `rm -rf /`",
            r"echo `echo \`rm -rf /\``",
            "echo <(rm -rf /)",
            "cat <<EOF\n$(rm -rf /)\nEOF",
            "printf ignored | xargs rm -rf /",
            "printf done && /bin/rm -rf /./",
            "rm --force --recursive ~/.",
            "printf ok\nrm -rf /",
            "(rm -rf /)",
            "{ rm -rf /; }",
            "> /tmp/safe-output rm -rf /",
            "2>&1 rm -rf /",
            "&>/tmp/safe-output rm -rf /",
            "FOO+=bar rm -rf /",
            "rm -rf ./*",
            "rm -rf ../*",
            "rm -rf /{*,.*}",
            "rm -rf /{tmp,}",
            "rm -rf /tmp/../*",
            "rm -rf ~/tmp/../*",
            "rm -rf /home/tenhi/tmp/../*",
            "rm -rf /etc",
            "rm -rf /usr",
            "rm -rf /var",
            "rm -rf /home",
            "rm -rf /boot",
            "rm -rf /root",
            "rm -rf ~/.config",
            "rm -rf ~/.local",
            "rm -rf $PWD",
            "rm -rf ${PWD}",
            "rm -rf ${HOME:?}",
            "rm -rf ~tenhi",
            "rm -rf //",
            "rm --recurs --forc --no-preserve-root /",
            "f(){ rm -rf /; }; f",
            "case x in x) rm -rf /;; esac",
            "coproc rm -rf /",
            "alias nuke='rm -rf /'; nuke",
            "x=; ${x:-rm} -rf /",
            "x=; r${x}m -rf /",
            "/usr/bin/r[m] -rf /",
            "r\\\nm -rf /",
            "rm -rf /\\\n",
            "find /tmp -exec rm -rf / {} +",
            "find /tmp -exec sh -c 'rm -rf /' {} +",
            "find /tmp -exec printf safe {} + -exec sh -c 'rm -rf /' {} +",
            "systemd-run --user --wait rm -rf /",
            "systemd-run --user --wait sh -c 'rm -rf /'",
            "script -q -c 'rm -rf /' /dev/null",
            "$(printf 'rm -rf /')",
            "$(printf command) $(printf rm) -rf /",
            "`printf rm` -rf /",
            '$"rm" -rf /',
            "r{,}m -rf /",
            'bash -O extglob -c "@(r)m -rf /"',
            "echo $(echo $(echo $(echo $(rm -rf /))))",
            deep_command,
            "git reset --hard HEAD",
            "git reset --har HEAD",
            "git -C 'path with spaces' reset --hard HEAD",
            "git --no-pager reset --hard HEAD",
            "git clean -fdx",
            "git clean -f",
            "git clean --forc -d",
            "git -c clean.requireForce=false clean -dx",
            "git -c clean.requireForce=false clean",
            "git --config-env=clean.requireForce=CLEAN_FORCE clean -dx",
            "git -c alias.nuke='!rm -rf --no-preserve-root /' nuke",
            "git -c alias.nuke='reset --hard' nuke",
            "git -c alias.first=second -c alias.second='reset --hard' first",
            "git -c Alias.NUKE='reset --hard' nuke",
            "git --config-env=alias.nuke=NUKE_COMMAND nuke",
            "git --config-en alias.nuke=NUKE_COMMAND nuke",
            "g\\\nit reset --hard HEAD",
            "kubectl logs pod",
            "kubectl logs pod --tail=-1",
            "kubectl logs --follow=true --tail=10 pod",
            "docker logs container",
            "docker --context prod logs container",
            "docker container logs container",
            "docker compose logs --follow",
            "docker logs --follow=true --tail=10 container",
            "docker logs -f=true --tail=10 container",
            "docker logs container # --tail=10",
            "bash -c 'docker logs container'",
            "find /tmp -exec sh -c 'docker logs container' {} +",
            "docker logs --tail=all container",
            "journalctl -u unit",
            "journalctl --lines=all -u unit",
            "journalctl -f | tail -n 10",
            "journalctl -f | sed -n '1,10p'",
            "journalctl -f | sed -n '/q/p'",
            f"API_TOKEN={token} command",
            f"OPENAI_API_KEY={token} command",
            f"GITHUB_TOKEN={token} command",
            f"AWS_SECRET_ACCESS_KEY={token} command",
            "API_TOKEN=$'literal-credential' command",
            "_".join(("OPENAI", "API", "KEY")) + "='literal-''credential' command",
            "tool --openai-api-key literal-credential",
            "API_TOKEN='literal multiword credential' command",
            "cat ~/.ssh/id_ed25519",
            "cat ~/.s$(printf sh)/id_ed25519",
            f'cat "{Path.home()}/.s$(printf sh)/id_ed25519"',
            "cat ~/.$(printf ssh)/id_ed25519",
            "x=ssh; cat ~/.$x/id_ed25519",
            "cat ~/.s${x:-sh}/id_ed25519",
            "cat ~/.s${EMPTY}sh/id_ed25519",
            "cat ~/.s[s]h/id_ed25519",
            "cat ~/.s'sh'/id_ed25519",
            r"cat ~/.s\sh/id_ed25519",
            "source .test/system/local.env",
            "cat ~/.kube/config",
            "cat ~/.ku?e/config",
            "cat ~/.k$(printf ube)/config",
            f'cat "{Path.home()}/.k$(printf ube)/config"',
            "cat ~/.k`printf ube`/config",
            "x=kube; cat ~/.$x/config",
            "cat ~/.k${x:-ube}/config",
            "cat ~/.ku${EMPTY}be/config",
            'printf "%s" "$KUBECONFIG"',
            "kubectl --kubeconfig=/tmp/cluster.yaml get pods",
            "cat ~/.gnupg/private-keys-v1.d/key",
            "cat ~/.gn[u]pg/private-keys-v1.?/key",
            "cat ~/.gn$(printf upg)/private-keys-v1.d/key",
            f'cat "{Path.home()}/.gn$(printf upg)/private-keys-v1.d/key"',
            "cat ~/.e$(printf nv)",
            "cat ~/${x:-.env}",
            'cat "$GRAFANA_SERVICE_ACCOUNT_TOKEN_FILE"',
        )
        for command in commands:
            with self.subTest(command=command):
                result = _run_hook(_event(command))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)
                output = json.loads(result.stdout)
                decision = output["hookSpecificOutput"]
                self.assertEqual(
                    {"hookEventName", "permissionDecision", "permissionDecisionReason"},
                    set(decision),
                )
                self.assertEqual("PreToolUse", decision["hookEventName"])
                self.assertEqual("deny", decision["permissionDecision"])
                self.assertTrue(decision["permissionDecisionReason"])
                self.assertNotIn(command, result.stdout)

    def test_narrow_and_public_commands_are_allowed(self) -> None:
        commands = (
            "rm -rf /tmp/narrow",
            "rm -rf ~/tmp/narrow",
            "command rm -rf /tmp/narrow",
            r"env -S 'printf\_%s\_safe'",
            "env --spl 'printf %s safe'",
            "env --spl='printf %s safe'",
            "printf '%s\\n' 'rm -rf /'",
            "printf '%s\\n' 'echo $(rm -rf /)'",
            r"echo \$(rm -rf /)",
            "cat <<'EOF'\n$(rm -rf /)\nEOF",
            "cat <<EOF\nrm -rf /\nEOF",
            "# $(rm -rf /)",
            "sudo -u rm printf '%s\\n' safe",
            "doas -u root printf '%s\\n' safe",
            "eval 'printf %s safe'",
            "bash -O expand_aliases -c 'printf %s safe'",
            "bash -o errexit -c 'printf %s safe'",
            'bash -O extglob -c "@(p)rintf %s safe"',
            "sh -o errexit -c 'printf %s safe'",
            "find /tmp -exec sh -c 'printf %s safe' {} +",
            "systemd-run --user --wait printf %s safe",
            "script -q -c 'printf %s safe' /dev/null",
            "export cmd=printf; $cmd %s safe",
            "$(printf printf) %s safe",
            "args=(rm -rf /)",
            "declare -a args=(rm -rf /)",
            "command -v rm -rf /",
            "bash -- -c 'rm -rf /'",
            "git -C 'path with spaces' status --short",
            "git --no-pager status --short",
            "git -c alias.first=second -c alias.second=status first",
            "git -c Alias.NUKE=status nuke",
            "git --config-env=user.name=GIT_AUTHOR status",
            "git -c clean.requireForce=true clean",
            "git reset -- README.md",
            "git clean -- README.md",
            "rm -rf /tmp/narrow/../specific",
            "rm -rf /etc/specific-file",
            "kubectl logs pod --tail=100",
            "docker logs --follow=false --tail=10 container",
            "docker logs -f=false --tail=10 container",
            "docker logs container --tail=10 # ignored comment",
            "bash -c 'docker logs container --tail=10'",
            "printf '%s\\n' 'docker logs container # --tail=10'",
            "journalctl -u unit | head -n 50",
            "journalctl -f | head -n 50",
            "journalctl -f | sed -n '1,10p;10q'",
            "API_TOKEN=$TOKEN command",
            "cat dotfiles/.ssh/config",
            "cat dotfiles/.s$(printf sh)/config",
            "git status --short dotfiles/.ssh",
            "git diff -- dotfiles/.ssh",
            "ls -la dotfiles/.ssh",
            "rg -n PasswordAuthentication dotfiles/.ssh",
            "cat ~/.s[s]h/config",
            "cat ~/.s[h]h/id_ed25519",
            "cat ~/.ssh/config.d/work",
            "cat ~/.ssh/id_ed25519.pub",
            "cat .test/system/local.env.example",
            "cat dotfiles/.gnupg/gpg.conf",
            "cat /tmp/pa$(printf ckage).json",
            "cat /tmp/$package_name.json",
            "ls docs/$file",
            "ls /tmp/$file",
            "ls ./tmp/$file",
            'ls "$HOME/tmp/$file"',
            'cat "~/.s$(printf sh)/id_ed25519"',
            (
                "for f in dotfiles/.local/share/codex-*/**/package.json "
                "dotfiles/.local/share/codex-cli/locked/package.json; do "
                'test -f "$f" && { echo "$f"; sed -n \'1,120p\' "$f"; }; done'
            ),
        )
        for command in commands:
            with self.subTest(command=command):
                result = _run_hook(_event(command))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_non_bash_and_malformed_events_are_ignored(self) -> None:
        cases = (
            _event("rm -rf /", tool_name="Read"),
            json.dumps({"hook_event_name": "PostToolUse", "tool_name": "Bash"}),
            json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"cmd": "rm -rf /"},
                }
            ),
            json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": ["rm", "-rf", "/"]},
                }
            ),
            "{not-json",
            "[]",
            "null",
            '"text"',
            "42",
        )
        for payload in cases:
            with self.subTest(payload=payload):
                result = _run_hook(payload)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_optimized_python_cannot_disable_policy(self) -> None:
        result = _run_hook(_event("rm -rf /"), optimized=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "deny",
            json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"],
        )


if __name__ == "__main__":
    unittest.main()
