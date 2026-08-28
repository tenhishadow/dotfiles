#!/usr/bin/env python3
"""Small, deterministic Codex lifecycle guardrails."""

# This hook stays a single standard-library file so it can run before managed
# runtimes exist and can be copied without importing repository-local modules.
# pylint: disable=too-many-lines

from __future__ import annotations

import codecs
import fnmatch
import json
import os
import posixpath
import re
import shlex
import sys
from collections.abc import Callable
from pathlib import Path

SHELL_LITERAL_VALUE = r"(?:'[^']*'|\"[^\"]*\"|[^\s;&|]+)"
SECRET_BASENAME = (
    r"(?:api[_-]?(?:key|token)|access[_-]?token|auth[_-]?token|"
    r"client[_-]?secret|private[_-]?key|secret[_-]?(?:access[_-]?)?key|"
    r"token|password|passwd|secret)"
)
SECRET_NAME = re.compile(rf"(?i)^(?:[a-z0-9]+[_-])*{SECRET_BASENAME}$")
SECRET_ASSIGNMENT = re.compile(
    rf"(?i)(?<![A-Za-z0-9_-])(?:[a-z0-9]+[_-])*{SECRET_BASENAME}"
    rf"\b\s*(?:=|:)\s*({SHELL_LITERAL_VALUE})"
)
SECRET_FLAG = re.compile(
    rf"(?i)--(?:[a-z0-9]+[_-])*{SECRET_BASENAME}"
    rf"(?:=|\s+)\s*({SHELL_LITERAL_VALUE})"
)
BEARER = re.compile(rf"(?i)\bauthorization\s*:\s*bearer\s+({SHELL_LITERAL_VALUE})")
URL_CREDENTIALS = re.compile(r"(?i)\bhttps?://[^\s/:]+:[^\s/@]+@")
SENSITIVE_PATH_REFERENCE = re.compile(
    r"(?:\$(?:KUBECONFIG\b|\{KUBECONFIG\b|"
    r"GRAFANA_SERVICE_ACCOUNT_TOKEN_FILE\b|"
    r"\{GRAFANA_SERVICE_ACCOUNT_TOKEN_FILE\b)|"
    r"(?<![A-Za-z0-9_])(?:KUBECONFIG|"
    r"GRAFANA_SERVICE_ACCOUNT_TOKEN_FILE)\s*=|--kubeconfig(?:=|\s))"
)
SAFE_VALUE_PREFIXES = (
    "$",
    "${",
    "<",
    "your_",
    "redacted",
    "example",
    "dummy",
    "test",
    "changeme",
)

COMMAND_WRAPPERS = {
    "busybox",
    "chrt",
    "chroot",
    "command",
    "doas",
    "builtin",
    "env",
    "exec",
    "ionice",
    "nice",
    "nohup",
    "pkexec",
    "prlimit",
    "run0",
    "setpriv",
    "setsid",
    "strace",
    "sudo",
    "systemd-run",
    "stdbuf",
    "time",
    "timeout",
    "toybox",
    "unshare",
    "watch",
    "xargs",
}
CONTROL_PREFIXES = {
    "!",
    "(",
    "{",
    "coproc",
    "do",
    "elif",
    "else",
    "if",
    "then",
    "until",
    "while",
}
SUDO_OPTIONS_WITH_VALUES = {
    "-C",
    "-D",
    "-R",
    "-T",
    "-g",
    "-h",
    "-p",
    "-u",
    "--chdir",
    "--chroot",
    "--close-from",
    "--group",
    "--host",
    "--prompt",
    "--role",
    "--type",
    "--user",
}
ENV_OPTIONS_WITH_VALUES = {
    "-C",
    "-S",
    "-a",
    "-u",
    "--argv0",
    "--chdir",
    "--split-string",
    "--unset",
}
XARGS_OPTIONS_WITH_VALUES = {
    "-E",
    "-I",
    "-L",
    "-P",
    "-a",
    "-d",
    "-n",
    "-s",
    "--arg-file",
    "--delimiter",
    "--eof",
    "--max-args",
    "--max-chars",
    "--max-lines",
    "--max-procs",
    "--replace",
}
SYSTEMD_RUN_OPTIONS_WITH_VALUES = {
    "-C",
    "-E",
    "-H",
    "-M",
    "-p",
    "-u",
    "--background",
    "--capsule",
    "--description",
    "--expand-environment",
    "--gid",
    "--host",
    "--job-mode",
    "--json",
    "--machine",
    "--nice",
    "--on-active",
    "--on-boot",
    "--on-calendar",
    "--on-startup",
    "--on-unit-active",
    "--on-unit-inactive",
    "--output",
    "--path-property",
    "--property",
    "--root-directory",
    "--service-type",
    "--setenv",
    "--slice",
    "--socket-property",
    "--timer-property",
    "--uid",
    "--unit",
    "--working-directory",
}
WRAPPER_OPTIONS_WITH_VALUES = {
    "chrt": {"-D", "-P", "-T", "--deadline", "--period", "--runtime"},
    "chroot": {"--groups", "--userspec"},
    "doas": {"-a", "-C", "-u"},
    "env": ENV_OPTIONS_WITH_VALUES,
    "exec": {"-a"},
    "ionice": {
        "-c",
        "-n",
        "-p",
        "-P",
        "-u",
        "--class",
        "--classdata",
        "--pgid",
        "--pid",
        "--uid",
    },
    "nice": {"-n", "--adjustment"},
    "pkexec": {"--user"},
    "prlimit": {
        "--as",
        "--core",
        "--cpu",
        "--data",
        "--fsize",
        "--locks",
        "--memlock",
        "--msgqueue",
        "--nice",
        "--nofile",
        "--nproc",
        "--pid",
        "--rss",
        "--rtprio",
        "--rttime",
        "--sigpending",
        "--stack",
    },
    "run0": {"--chdir", "--group", "--machine", "--nice", "--user"},
    "setpriv": {
        "--bounding-set",
        "--euid",
        "--egid",
        "--groups",
        "--inh-caps",
        "--pdeathsig",
        "--reuid",
        "--regid",
        "--ruid",
        "--securebits",
    },
    "strace": {
        "-D",
        "-E",
        "-I",
        "-O",
        "-P",
        "-S",
        "-U",
        "-b",
        "-e",
        "-o",
        "-p",
        "-s",
        "-u",
        "--columns",
        "--decode-fds",
        "--detach-on",
        "--env",
        "--fault",
        "--inject",
        "--interruptible",
        "--output",
        "--status",
        "--string-limit",
        "--trace",
        "--trace-fds",
        "--user",
    },
    "sudo": SUDO_OPTIONS_WITH_VALUES,
    "systemd-run": SYSTEMD_RUN_OPTIONS_WITH_VALUES,
    "stdbuf": {"-e", "-i", "-o", "--error", "--input", "--output"},
    "time": {"-f", "-o", "--format", "--output"},
    "timeout": {"-k", "-s", "--kill-after", "--signal"},
    "unshare": {
        "--map-group",
        "--map-groups",
        "--map-user",
        "--map-users",
        "--mount-proc",
        "--propagation",
        "--root",
        "--wd",
    },
    "watch": {"-n", "--interval"},
    "xargs": XARGS_OPTIONS_WITH_VALUES,
}
WRAPPERS_WITH_ASSIGNMENTS = {"env", "sudo"}
UNPARSEABLE_SHELL_WORD = "\0dotfiles-unparseable-shell"
MAX_SHELL_RECURSION = 32
ESCAPED_SHELL_PUNCTUATION = {
    "\ue000": ";",
    "\ue001": "&",
    "\ue002": "|",
    "\ue003": "<",
    "\ue004": ">",
}


def _collapse_line_continuations(source: str) -> str:
    """Apply the shell's backslash-newline removal outside single quotes."""
    output: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(source):
        character = source[index]
        if (
            character == "\\"
            and quote != "'"
            and index + 1 < len(source)
            and source[index + 1] == "\n"
        ):
            index += 2
            continue
        if character == "'" and quote != '"':
            quote = None if quote == "'" else "'"
        elif character == '"' and quote != "'":
            quote = None if quote == '"' else '"'
        output.append(character)
        index += 1
    return "".join(output)


def _literal_secret(value: str) -> bool:
    candidate = value.strip("'\"").lower()
    return len(candidate) >= 8 and not candidate.startswith(SAFE_VALUE_PREFIXES)


def _normalize_ansi_c_quotes(source: str) -> str | None:
    """Convert Bash ANSI-C words to shlex-compatible quoted literals."""
    output: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(source):
        character = source[index]
        if character == "\\" and quote != "'":
            output.append(source[index : index + 2])
            index += 2
            continue
        if quote is None and source.startswith("$'", index):
            cursor = index + 2
            body: list[str] = []
            while cursor < len(source):
                if source[cursor] == "\\" and cursor + 1 < len(source):
                    body.append(source[cursor : cursor + 2])
                    cursor += 2
                    continue
                if source[cursor] == "'":
                    break
                body.append(source[cursor])
                cursor += 1
            if cursor >= len(source):
                return None
            try:
                decoded = codecs.decode("".join(body), "unicode_escape")
            except UnicodeDecodeError:
                return None
            output.append(shlex.quote(decoded))
            index = cursor + 1
            continue
        if character == "'" and quote != '"':
            quote = None if quote == "'" else "'"
        elif character == '"' and quote != "'":
            quote = None if quote == '"' else '"'
        output.append(character)
        index += 1
    return "".join(output)


# Bounded shell parsers keep their state local to preserve standalone execution.
# pylint: disable-next=too-many-branches
def _shell_parts(command: str) -> list[tuple[list[str], str]]:
    """Tokenize simple commands and retain their following control operator."""
    normalized = _normalize_ansi_c_quotes(command)
    if normalized is None:
        return [([UNPARSEABLE_SHELL_WORD], "")]
    if any(marker in normalized for marker in ESCAPED_SHELL_PUNCTUATION):
        return [([UNPARSEABLE_SHELL_WORD], "")]
    protected: list[str] = []
    index = 0
    quote: str | None = None
    punctuation_markers = {
        punctuation: marker for marker, punctuation in ESCAPED_SHELL_PUNCTUATION.items()
    }
    while index < len(normalized):
        character = normalized[index]
        if (
            character == "\\"
            and quote is None
            and index + 1 < len(normalized)
            and normalized[index + 1] in punctuation_markers
        ):
            protected.append(punctuation_markers[normalized[index + 1]])
            index += 2
            continue
        if character == "'" and quote != '"':
            quote = None if quote == "'" else "'"
        elif character == '"' and quote != "'":
            quote = None if quote == '"' else '"'
        protected.append(character)
        index += 1
    try:
        lexer = shlex.shlex("".join(protected), posix=True, punctuation_chars=";&|<>\n")
        lexer.commenters = ""
        # Newlines terminate commands in the shell. Keep them out of shlex's
        # generic whitespace so they remain visible as control operators.
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return [([UNPARSEABLE_SHELL_WORD], "")]

    parts: list[tuple[list[str], str]] = []
    segment: list[str] = []
    for token in tokens:
        if token and all(character in ";&|\n" for character in token):
            if segment:
                parts.append((segment, token))
                segment = []
        else:
            for marker, punctuation in ESCAPED_SHELL_PUNCTUATION.items():
                token = token.replace(marker, punctuation)
            segment.append(token)
    if segment:
        parts.append((segment, ""))
    return parts


def _shell_segments(command: str) -> list[list[str]]:
    """Return simple command argv groups from shell source."""
    return [segment for segment, _operator in _shell_parts(command)]


def _without_redirections(words: list[str]) -> list[str]:
    """Remove shell redirection syntax while retaining the executed argv."""
    result: list[str] = []
    index = 0
    while index < len(words):
        word = words[index]
        next_is_redirection = (
            index + 1 < len(words)
            and words[index + 1]
            and any(character in "<>" for character in words[index + 1])
            and all(character in "<>&" for character in words[index + 1])
        )
        if word.isdigit() and next_is_redirection:
            index += 1
            continue
        if (
            word
            and any(character in "<>" for character in word)
            and all(character in "<>&" for character in word)
        ):
            index += 2
            continue
        result.append(word)
        index += 1
    return result


def _heredoc_header_runs_shell(header: str) -> bool:
    """Return whether a here-document is standard input for a shell."""
    for segment in reversed(_shell_segments(header)):
        words = _unwrap_command(segment)
        if words:
            is_shell, shell_command, _arguments = _shell_command_details(words)
            return is_shell and shell_command is None
    return False


# pylint: disable-next=too-many-locals
def _heredoc_view(command: str) -> tuple[str, list[str], list[str]]:
    """Hide heredoc data while collecting shell input and expandable bodies."""
    lines = command.splitlines(keepends=True)
    output: list[str] = []
    shell_inputs: list[str] = []
    expanding_inputs: list[str] = []
    pending: list[tuple[str, bool, bool, bool, list[str]]] = []
    heredoc = re.compile(
        r"(?<!<)<<(?!<)(?P<tabs>-)?[ \t]*(?P<word>"
        r"""(?:\\.|'[^']*'|"(?:\\.|[^"])*"|[^\s;&|<>])+"""
        r")"
    )
    for line in lines:
        if pending:
            delimiter, strip_tabs, expands, runs_shell, body = pending[0]
            candidate = line.rstrip("\r\n")
            if strip_tabs:
                candidate = candidate.lstrip("\t")
            if candidate == delimiter:
                pending.pop(0)
                if runs_shell:
                    shell_inputs.append("".join(body))
                if expands:
                    expanding_inputs.append("".join(body))
                output.append("\n" if line.endswith("\n") else "")
                continue
            body.append(line)
            output.append("\n" if line.endswith("\n") else "")
            continue
        output.append(line)
        for match in heredoc.finditer(line):
            delimiter_word = match.group("word")
            normalized = _normalize_ansi_c_quotes(delimiter_word)
            try:
                delimiter_parts = shlex.split(
                    normalized if normalized is not None else delimiter_word
                )
            except ValueError:
                delimiter_parts = []
            if len(delimiter_parts) != 1:
                continue
            delimiter = delimiter_parts[0]
            quoted = any(marker in delimiter_word for marker in ("'", '"', "\\"))
            pending.append(
                (
                    delimiter,
                    bool(match.group("tabs")),
                    not quoted,
                    _heredoc_header_runs_shell(line),
                    [],
                )
            )
    for _delimiter, _strip_tabs, expands, runs_shell, body in pending:
        if runs_shell:
            shell_inputs.append("".join(body))
        if expands:
            expanding_inputs.append("".join(body))
    return "".join(output), shell_inputs, expanding_inputs


def _without_shell_comments(source: str) -> str:
    """Remove shell comments while preserving command-terminating newlines."""
    output: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(source):
        character = source[index]
        if character == "\\" and quote != "'":
            output.append(source[index : index + 2])
            index += 2
            continue
        if character == "'" and quote != '"':
            quote = None if quote == "'" else "'"
        elif character == '"' and quote != "'":
            quote = None if quote == '"' else '"'
        comment_boundary = (
            index == 0 or source[index - 1].isspace() or source[index - 1] in ";&|(){}"
        )
        if quote is None and character == "#" and comment_boundary:
            newline = source.find("\n", index)
            if newline < 0:
                break
            output.append("\n")
            index = newline + 1
            continue
        output.append(character)
        index += 1
    return "".join(output)


def _command_substitution_end(source: str, start: int) -> int | None:
    """Return the index after a balanced command substitution."""
    cursor = start
    depth = 1
    quote: str | None = None
    while cursor < len(source) and depth:
        character = source[cursor]
        if character == "\\" and quote != "'":
            cursor += 2
            continue
        if character == "'" and quote != '"':
            quote = None if quote == "'" else "'"
        elif character == '"' and quote != "'":
            quote = None if quote == '"' else '"'
        elif quote is None and character == "(":
            depth += 1
        elif quote is None and character == ")":
            depth -= 1
        cursor += 1
    return cursor if depth == 0 else None


def _backtick_substitution_end(source: str, start: int) -> int | None:
    """Return the index after an unescaped closing backtick."""
    cursor = start
    while cursor < len(source):
        if source[cursor] == "\\":
            cursor += 2
            continue
        if source[cursor] == "`":
            return cursor + 1
        cursor += 1
    return None


def _scan_command_substitutions(source: str) -> list[str]:
    """Extract literal substitutions from one heredoc-free string."""
    substitutions: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(source):
        character = source[index]
        if character == "\\" and quote != "'":
            index += 2
            continue
        if character == "'" and quote != '"':
            quote = None if quote == "'" else "'"
            index += 1
            continue
        if character == '"' and quote != "'":
            quote = None if quote == '"' else '"'
            index += 1
            continue
        is_command = quote != "'" and source.startswith("$(", index)
        if is_command and not source.startswith("$((", index):
            start = index + 2
            end = _command_substitution_end(source, start)
            if end is not None:
                substitutions.append(source[start : end - 1])
                index = end
                continue
        is_process = quote is None and source.startswith(("<(", ">("), index)
        if is_process:
            start = index + 2
            end = _command_substitution_end(source, start)
            if end is not None:
                substitutions.append(source[start : end - 1])
                index = end
                continue
        if quote != "'" and character == "`":
            end = _backtick_substitution_end(source, index + 1)
            if end is not None:
                substitutions.append(source[index + 1 : end - 1].replace(r"\`", "`"))
                index = end
                continue
        index += 1
    return substitutions


def _literal_command_substitutions(command: str) -> list[str]:
    """Extract executed substitutions while ignoring inert shell comments."""
    source, _shell_inputs, expanding_inputs = _heredoc_view(command)
    substitutions = _scan_command_substitutions(_without_shell_comments(source))
    for expanding_input in expanding_inputs:
        substitutions.extend(_scan_command_substitutions(expanding_input))
    return substitutions


def _literal_command_groups(command: str) -> list[str]:
    """Extract unquoted subshell groups without treating escaped text as code."""
    source, _shell_inputs, _expanding_inputs = _heredoc_view(command)
    source = _without_shell_comments(source)
    groups: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(source):
        character = source[index]
        if character == "\\" and quote != "'":
            index += 2
            continue
        if character == "'" and quote != '"':
            quote = None if quote == "'" else "'"
            index += 1
            continue
        if character == '"' and quote != "'":
            quote = None if quote == '"' else '"'
            index += 1
            continue
        previous = source[index - 1] if index else ""
        if (
            quote is None
            and character == "("
            and (not previous or previous not in "$<>=")
        ):
            start = index + 1
            end = _command_substitution_end(source, start)
            if end is not None:
                groups.append(source[start : end - 1])
                index = end
                continue
        index += 1
    return groups


def _decode_backslash_escapes(value: str) -> str:
    """Decode the portable escape subset accepted by echo -e and printf %b."""
    try:
        return codecs.decode(value, "unicode_escape")
    except UnicodeDecodeError:
        return value


def _render_printf(words: list[str]) -> str:
    """Render the common shell printf forms used to feed another shell."""
    arguments = words[1:]
    if arguments and arguments[0] == "--":
        arguments = arguments[1:]
    if not arguments:
        return ""
    format_string = _decode_backslash_escapes(arguments[0])
    values = arguments[1:]
    directive = re.compile(
        r"%(?P<flags>[-+ #0']*)(?P<width>\*|\d+)?"
        r"(?:\.(?P<precision>\*|\d+))?(?:hh|ll|[hljztL])?(?P<kind>[a-zA-Z%])"
    )
    rendered: list[str] = []
    value_index = 0
    first_pass = True
    while first_pass or value_index < len(values):
        first_pass = False
        cursor = 0
        consumed_value = False
        for match in directive.finditer(format_string):
            rendered.append(format_string[cursor : match.start()])
            cursor = match.end()
            kind = match.group("kind")
            if kind == "%":
                rendered.append("%")
                continue
            for field in ("width", "precision"):
                if match.group(field) == "*" and value_index < len(values):
                    value_index += 1
            value = values[value_index] if value_index < len(values) else ""
            value_index += 1
            consumed_value = True
            if kind == "b":
                rendered.append(_decode_backslash_escapes(value))
            elif kind == "q":
                rendered.append(shlex.quote(value))
            else:
                rendered.append(value)
        rendered.append(format_string[cursor:])
        if not consumed_value or len("".join(rendered)) > 65_536:
            break
    return "".join(rendered)[:65_536]


def _literal_producer_output(words: list[str]) -> str | None:
    """Return deterministic output for literal echo and printf invocations."""
    executable = os.path.basename(words[0])
    if executable == "printf":
        return _render_printf(words)
    if executable != "echo":
        return None
    index = 1
    decode_escapes = False
    while index < len(words):
        option = words[index]
        if option == "--":
            index += 1
            break
        if not re.fullmatch(r"-[neE]+", option):
            break
        if "e" in option:
            decode_escapes = True
        if "E" in option:
            decode_escapes = False
        index += 1
    output = " ".join(words[index:])
    return _decode_backslash_escapes(output) if decode_escapes else output


def _literal_substitution_output(source: str) -> str | None:
    """Return deterministic stdout for one literal command substitution."""
    parts = _shell_parts(_without_shell_comments(source))
    if len(parts) != 1:
        return None
    words = _unwrap_command(parts[0][0])
    if not words:
        return None
    output = _literal_producer_output(words)
    return output.rstrip("\n") if output is not None else None


def _literal_substitution_replacement(output: str, *, double_quoted: bool) -> str:
    """Quote deterministic substitution output for its surrounding shell word."""
    if not double_quoted:
        return shlex.join(output.split())
    return (
        output.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("`", "\\`")
    )


def _materialize_literal_substitutions(
    source: str, *, include_double_quoted: bool = False
) -> str | None:
    """Expose deterministic command-substitution output as argv."""
    replacements: list[tuple[int, int, str]] = []
    index = 0
    quote: str | None = None
    quote_start: int | None = None
    while index < len(source):
        character = source[index]
        if character == "\\" and quote != "'":
            index += 2
            continue
        if character in {"'", '"'} and (quote is None or quote == character):
            quote = None if quote == character else character
            quote_start = index if quote is not None else None
            index += 1
            continue
        active_substitution = quote is None or (include_double_quoted and quote == '"')
        quoted_literal_tilde = (
            quote == '"'
            and quote_start is not None
            and source[quote_start + 1 :].startswith("~/")
        )
        if (
            active_substitution
            and not quoted_literal_tilde
            and source.startswith("$(", index)
            and not source.startswith("$((", index)
        ):
            end = _command_substitution_end(source, index + 2)
            if end is not None:
                output = _literal_substitution_output(source[index + 2 : end - 1])
                if output is not None:
                    replacement = _literal_substitution_replacement(
                        output, double_quoted=quote == '"'
                    )
                    replacements.append((index, end, replacement))
                index = end
                continue
        if active_substitution and not quoted_literal_tilde and character == "`":
            end = _backtick_substitution_end(source, index + 1)
            if end is not None:
                output = _literal_substitution_output(
                    source[index + 1 : end - 1].replace(r"\`", "`")
                )
                if output is not None:
                    replacement = _literal_substitution_replacement(
                        output, double_quoted=quote == '"'
                    )
                    replacements.append((index, end, replacement))
                index = end
                continue
        index += 1
    if not replacements:
        return None
    materialized = source
    for start, end, replacement in reversed(replacements):
        materialized = f"{materialized[:start]}{replacement}{materialized[end:]}"
    return materialized


# pylint: disable-next=too-many-locals
def _literal_shell_inputs(command: str) -> list[str]:
    """Collect literal here-strings and pipeline data executed by a shell."""
    source, _shell_inputs, _expanding_inputs = _heredoc_view(command)
    parts = _shell_parts(_without_shell_comments(source))
    inputs: list[str] = []
    for index, (segment, _operator) in enumerate(parts):
        words = _unwrap_command(segment)
        if not words:
            continue
        is_shell, shell_command = _shell_command(words)
        if not is_shell or shell_command is not None:
            continue
        for token_index, token in enumerate(segment[:-1]):
            if token.startswith("<<<"):
                inputs.append(segment[token_index + 1])
        if index == 0 or "|" not in parts[index - 1][1]:
            continue
        producer_index = index - 1
        producer = _unwrap_command(parts[producer_index][0])
        while (
            producer
            and os.path.basename(producer[0]) in {"cat", "sed", "tee"}
            and producer_index > 0
            and "|" in parts[producer_index - 1][1]
        ):
            producer_index -= 1
            producer = _unwrap_command(parts[producer_index][0])
        if producer:
            output = _literal_producer_output(producer)
            if output is not None:
                inputs.append(output)
    return inputs


def _unique_long_option(word: str, options: set[str]) -> str | None:
    """Resolve one exact or unambiguous GNU-style long option."""
    name = word.partition("=")[0]
    if not name.startswith("--"):
        return None
    matches = [option for option in options if option.startswith(name)]
    return matches[0] if len(matches) == 1 else None


def _option_value_index(words: list[str], index: int, options: set[str]) -> int:
    """Advance past one wrapper option and any separate option argument."""
    option = words[index]
    option_name = option.split("=", 1)[0]
    matched_long = _unique_long_option(option, options)
    if option_name in options and "=" not in option and index + 1 < len(words):
        return index + 2
    if matched_long is not None and "=" not in option and index + 1 < len(words):
        return index + 2
    if option.startswith("-") and not option.startswith("--"):
        short_options = option[1:]
        for short_index, short_option in enumerate(short_options):
            if f"-{short_option}" not in options:
                continue
            has_attached_value = short_index + 1 < len(short_options)
            if not has_attached_value and index + 1 < len(words):
                return index + 2
            return index + 1
    return index + 1


def _split_env_string(value: str) -> list[str] | None:
    """Parse GNU env -S syntax, rejecting dynamic or malformed strings."""
    normalized = value.replace(r"\_", " ")
    if "$" in normalized or "\\" in normalized:
        return None
    try:
        return shlex.split(normalized)
    except ValueError:
        return None


def _env_split_option(words: list[str], index: int) -> tuple[bool, str | None, int]:
    """Return whether argv[index] is env's split-string option and its value."""
    option = words[index]
    result: tuple[bool, str | None, int] = (False, None, 0)
    long_name = _unique_long_option(option, ENV_OPTIONS_WITH_VALUES)
    if option == "-S" or long_name == "--split-string":
        _name, separator, attached = option.partition("=")
        if separator:
            return True, attached, 1
        has_value = index + 1 < len(words)
        result = (True, words[index + 1] if has_value else None, 2 if has_value else 1)
    elif option.startswith("-") and not option.startswith("--"):
        short_options = option[1:]
        split_marker = short_options.find("S")
        if split_marker >= 0 and set(short_options[:split_marker]).issubset(
            {"0", "i", "v"}
        ):
            attached = short_options[split_marker + 1 :]
            if attached:
                result = (True, attached, 1)
            else:
                has_value = index + 1 < len(words)
                result = (
                    True,
                    words[index + 1] if has_value else None,
                    2 if has_value else 1,
                )
    return result


# pylint: disable-next=too-many-branches
def _unwrap_command(words: list[str]) -> list[str] | None:
    """Remove common execution wrappers from one simple command argv."""
    words = _without_redirections(words)
    if UNPARSEABLE_SHELL_WORD in words:
        return None
    index = 0
    while index < len(words) and words[index] in CONTROL_PREFIXES:
        index += 1
    assignment = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\+?=.*")
    while index < len(words) and assignment.fullmatch(words[index]):
        index += 1

    while index < len(words):
        executable = os.path.basename(words[index])
        if executable not in COMMAND_WRAPPERS:
            break
        index += 1
        if executable == "command":
            command_options = {
                option
                for option in words[index:]
                if option.startswith("-") and option != "--"
            }
            if command_options.intersection({"-v", "-V"}):
                return []
        options_with_values = WRAPPER_OPTIONS_WITH_VALUES.get(executable, set())
        while index < len(words) and words[index].startswith("-"):
            if words[index] == "--":
                index += 1
                break
            if executable == "env":
                is_split, split_value, consumed = _env_split_option(words, index)
                if is_split:
                    if split_value is None:
                        return None
                    split_words = _split_env_string(split_value)
                    if split_words is None:
                        return None
                    words[index : index + consumed] = split_words
                    continue
            index = _option_value_index(words, index, options_with_values)
        if executable in WRAPPERS_WITH_ASSIGNMENTS:
            while index < len(words) and assignment.fullmatch(words[index]):
                index += 1
        if executable in {"chroot", "timeout"} and index < len(words):
            index += 1
        if (
            executable == "chrt"
            and index + 1 < len(words)
            and re.fullmatch(r"[+-]?\d+", words[index])
        ):
            index += 1
    return words[index:]


# Policy predicates use early returns to keep fail-closed branches explicit.
# pylint: disable-next=too-many-return-statements
def _broad_rm_target(target: str) -> bool:
    brace = re.search(r"\{([^{}]*)\}", target)
    if brace and "," in brace.group(1):
        prefix = target[: brace.start()]
        suffix = target[brace.end() :]
        alternatives = brace.group(1).split(",")
        if len(alternatives) > 32:
            return True
        if any(
            _broad_rm_target(f"{prefix}{alternative}{suffix}")
            for alternative in alternatives
        ):
            return True
    home = str(Path.home())
    if any(marker in target for marker in ("$", "`")):
        return True
    if re.fullmatch(r"/+", target):
        return True
    if target.startswith("~"):
        _home_name, separator, home_suffix = target.partition("/")
        if not separator or posixpath.normpath(home_suffix) in {"", ".", ".."}:
            return True
    if (
        target.startswith("/")
        and posixpath.dirname(target) == "/"
        and any(marker in target for marker in ("*", "?", "[", "{"))
    ):
        return True
    broad_globs = {
        "*",
        ".*",
        "./*",
        "./.*",
        "../*",
        "../.*",
        "/*",
        "/.*",
        "$HOME/*",
        "${HOME}/*",
        "~/*",
        f"{home}/*",
    }
    if target in broad_globs:
        return True

    expanded = target
    if expanded == "$HOME" or expanded.startswith("$HOME/"):
        expanded = home + expanded[len("$HOME") :]
    elif expanded == "${HOME}" or expanded.startswith("${HOME}/"):
        expanded = home + expanded[len("${HOME}") :]
    elif expanded.startswith("~"):
        expanded = os.path.expanduser(expanded)
    normalized = posixpath.normpath(expanded)
    protected_roots = {
        "/",
        "/boot",
        "/etc",
        "/home",
        "/root",
        "/usr",
        "/var",
        home,
        f"{home}/.cache",
        f"{home}/.config",
        f"{home}/.local",
    }
    broad_normalized = {
        "*",
        ".*",
        "../*",
        "../.*",
        "/*",
        "/.*",
        f"{home}/*",
        f"{home}/.*",
    }
    return normalized in protected_roots | broad_normalized


def _brace_command_matches(word: str, expected: str, *, depth: int = 0) -> bool:
    """Return whether brace expansion can produce an expected command name."""
    brace = re.search(r"\{([^{}]*,[^{}]*)\}", word)
    if brace is None:
        return os.path.basename(word) == expected
    alternatives = brace.group(1).split(",")
    if depth >= 8 or len(alternatives) > 32:
        return True
    prefix = word[: brace.start()]
    suffix = word[brace.end() :]
    return any(
        _brace_command_matches(
            f"{prefix}{alternative}{suffix}", expected, depth=depth + 1
        )
        for alternative in alternatives
    )


def _command_name_matches(word: str, expected: str) -> bool:
    """Match a command name, including deterministic shell glob spelling."""
    executable = os.path.basename(word)
    return (
        bool(re.search(r"[?*+@!]\(", executable))
        or _brace_command_matches(executable, expected)
        or (
            any(marker in executable for marker in ("*", "?", "["))
            and fnmatch.fnmatchcase(expected, executable)
        )
    )


# pylint: disable-next=too-many-return-statements
def _shell_command_details(words: list[str]) -> tuple[bool, str | None, list[str]]:
    """Extract a shell -c command and its positional arguments."""
    if os.path.basename(words[0]) not in {"bash", "dash", "sh", "zsh"}:
        return False, None, []
    options_with_values = {"-O", "-o", "+O", "+o", "--init-file", "--rcfile"}
    index = 1
    while index < len(words):
        option = words[index]
        if option == "--":
            return True, None, []
        if not option.startswith(("-", "+")) or option in {"-", "+"}:
            return True, None, []
        long_option = _unique_long_option(option, options_with_values)
        if long_option is not None:
            index += 1 if "=" in option else 2
            continue
        if option in options_with_values:
            index += 2
            continue
        if option.startswith(("-O", "-o", "+O", "+o")) and len(option) > 2:
            return True, None, []
        if option == "-c" or (not option.startswith("--") and "c" in option[1:]):
            nested_index = index + 1
            if nested_index < len(words) and words[nested_index] == "--":
                nested_index += 1
            if nested_index >= len(words):
                return True, None, []
            return True, words[nested_index], words[nested_index + 1 :]
        index += 1
    return True, None, []


def _shell_command(words: list[str]) -> tuple[bool, str | None]:
    """Extract a command passed to a shell's -c option."""
    is_shell, command, _arguments = _shell_command_details(words)
    return is_shell, command


def _dangerous_rm_argv(words: list[str]) -> bool:
    """Return whether argv is a recursive forced removal of a broad target."""
    if not _command_name_matches(words[0], "rm"):
        return False
    recursive = False
    force = False
    targets: list[str] = []
    parse_options = True
    for word in words[1:]:
        if parse_options and word == "--":
            parse_options = False
        elif parse_options and word.startswith("--"):
            option = word.split("=", 1)[0]
            recursive |= "--recursive".startswith(option)
            force |= "--force".startswith(option)
        elif parse_options and word.startswith("-"):
            recursive |= "r" in word.lower()
            force |= "f" in word.lower()
        else:
            targets.append(word)
    return recursive and force and any(_broad_rm_target(target) for target in targets)


def _expand_known_variables(source: str, variables: dict[str, str]) -> str:
    """Resolve literal shell variables needed to expose an executed command."""

    def indirect(match: re.Match[str]) -> str:
        reference = variables.get(match.group("name"))
        return variables.get(reference, match.group(0)) if reference else match.group(0)

    def transform(match: re.Match[str]) -> str:
        name = match.group("name")
        if name not in variables:
            return match.group(0)
        value = variables[name]
        return value.lower() if match.group("operation") == ",," else value.upper()

    source = re.sub(r"\$\{!(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}", indirect, source)
    source = re.sub(
        r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?P<operation>,,|\^\^)\}",
        transform,
        source,
    )

    def parameter(match: re.Match[str]) -> str:
        name = match.group("name")
        operator = match.group("operator") or ""
        fallback = match.group("fallback") or ""
        if name not in variables:
            if operator in {"-", ":-", "=", ":="}:
                if operator in {"=", ":="}:
                    variables[name] = fallback
                return fallback
            return match.group(0)
        value = variables[name]
        if operator in {":-", ":="} and not value:
            if operator == ":=":
                variables[name] = fallback
            return fallback
        if operator == ":+":
            return fallback if value else ""
        if operator == "+":
            return fallback
        return value

    expanded = re.sub(
        r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
        r"(?:(?P<operator>:-|:\+|:=|-|\+|=)(?P<fallback>[^}]*))?\}",
        parameter,
        source,
    )
    return re.sub(
        r"\$(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
        lambda match: variables.get(match.group("name"), match.group(0)),
        expanded,
    )


def _materialize_positional_parameters(source: str, arguments: list[str]) -> str:
    """Expose argv values consumed by a shell -c script for policy checks."""
    positional = arguments[1:] if arguments else []
    joined = shlex.join(positional)
    result = re.sub(r'"\$(?:@|\*)"|"\$\{(?:@|\*)\}"', joined, source)
    result = re.sub(r"\$(?:@|\*)|\$\{(?:@|\*)\}", joined, result)

    def braced_position(match: re.Match[str]) -> str:
        index = int(match.group("quoted") or match.group("unquoted"))
        value = arguments[index] if index < len(arguments) else ""
        return shlex.quote(value)

    result = re.sub(
        r'"\$\{(?P<quoted>\d+)\}"|\$\{(?P<unquoted>\d+)\}',
        braced_position,
        result,
    )
    for index in range(10):
        value = arguments[index] if index < len(arguments) else ""
        replacement = shlex.quote(value)
        for parameter in (
            f'"${{{index}}}"',
            f'"${index}"',
            f"${{{index}}}",
            f"${index}",
        ):
            result = result.replace(parameter, replacement)
    return result


# pylint: disable-next=too-many-return-statements
def _nested_argv_command(
    words: list[str], variables: dict[str, str]
) -> tuple[str | None, bool]:
    """Return nested shell source and whether it is unresolved dynamic code."""
    is_shell, shell_command, arguments = _shell_command_details(words)
    if is_shell:
        if shell_command is None:
            return None, False
        resolved = _expand_known_variables(shell_command, variables)
        resolved = _materialize_positional_parameters(resolved, arguments)
        dynamic = bool(
            re.fullmatch(
                r"\s*(?:\$[A-Za-z_][A-Za-z0-9_]*|"
                r"\$\{[A-Za-z_][A-Za-z0-9_]*\})\s*",
                resolved,
            )
        )
        return resolved, dynamic
    executable = os.path.basename(words[0])
    if executable == "script":
        index = 1
        while index < len(words):
            option = words[index]
            if option == "--":
                nested = shlex.join(words[index + 1 :])
                return (nested or None), False
            option_name = _unique_long_option(option, {"--command"})
            if option == "-c" or option_name == "--command":
                _name, separator, attached = option.partition("=")
                if separator:
                    return attached, "$" in attached or "`" in attached
                if index + 1 >= len(words):
                    return None, False
                nested = words[index + 1]
                return nested, "$" in nested or "`" in nested
            if option.startswith("-c") and option != "-c":
                nested = option[2:]
                return nested, "$" in nested or "`" in nested
            index += 1
        return None, False
    if executable != "eval":
        return None, False
    arguments = words[1:]
    if arguments and arguments[0] == "--":
        arguments = arguments[1:]
    if not arguments:
        return None, False
    resolved = _expand_known_variables(" ".join(arguments), variables)
    return resolved, "$" in resolved or "`" in resolved


def _persistent_assignments(
    segment: list[str], variables: dict[str, str]
) -> dict[str, str]:
    """Return assignments from a shell segment that contains no command."""
    index = 0
    while index < len(segment) and segment[index] in CONTROL_PREFIXES:
        index += 1
    assignments: dict[str, str] = {}
    assignment = re.compile(r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>.*)")
    while index < len(segment):
        match = assignment.fullmatch(segment[index])
        if match is None:
            return {}
        visible_variables = variables | assignments
        assignments[match.group("name")] = _expand_known_variables(
            match.group("value"), visible_variables
        )
        index += 1
    return assignments


def _builtin_variable_update(
    segment: list[str], variables: dict[str, str]
) -> tuple[dict[str, str], set[str]] | None:
    """Collect literal assignments made by shell variable builtins."""
    if not segment:
        return None
    executable = os.path.basename(segment[0])
    if executable == "unset":
        names = {word for word in segment[1:] if re.fullmatch(r"[A-Za-z_]\w*", word)}
        return {}, names
    if executable not in {"declare", "export", "local", "readonly", "typeset"}:
        return None
    updates: dict[str, str] = {}
    assignment = re.compile(r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>.*)")
    for word in segment[1:]:
        if word.startswith("-"):
            continue
        match = assignment.fullmatch(word)
        if match is None:
            continue
        updates[match.group("name")] = _expand_known_variables(
            match.group("value"), variables | updates
        )
    return updates, set()


def _dynamic_command_word(word: str) -> bool:
    """Return whether shell expansion determines the executed command name."""
    return any(marker in word for marker in ("$", "`")) or bool(
        re.search(r"\{[^{}]*,[^{}]*\}", word)
    )


def _find_executed_commands(words: list[str]) -> list[list[str]]:
    """Return every command argv executed by a find expression."""
    commands: list[list[str]] = []
    index = 1
    while index < len(words):
        if words[index] not in {"-exec", "-execdir", "-ok", "-okdir"}:
            index += 1
            continue
        start = index + 1
        end = start
        while end < len(words):
            terminates = words[end] == ";" or (
                words[end] == "+" and end > start and words[end - 1] == "{}"
            )
            if terminates:
                break
            end += 1
        if end > start:
            commands.append(words[start:end])
        index = end + 1
    return commands


# The recursive dispatcher keeps all bounded policy layers visible in one place.
# pylint: disable-next=too-many-branches,too-many-locals,too-many-return-statements
def _dangerous_shell_command(
    command: str,
    argv_check: Callable[[list[str]], bool],
    *,
    depth: int = 0,
) -> bool:
    """Inspect literal shell execution layers with bounded recursion."""
    command = _collapse_line_continuations(command)
    materialized = _materialize_literal_substitutions(command)
    if (
        materialized is not None
        and materialized != command
        and (
            depth >= MAX_SHELL_RECURSION
            or _dangerous_shell_command(materialized, argv_check, depth=depth + 1)
        )
    ):
        return True
    sanitized, shell_inputs, _expanding_inputs = _heredoc_view(command)
    sanitized = _without_shell_comments(sanitized)
    nested_sources = [
        *shell_inputs,
        *_literal_command_substitutions(command),
        *_literal_command_groups(command),
        *_literal_shell_inputs(command),
    ]
    if nested_sources:
        if depth >= MAX_SHELL_RECURSION:
            return True
        if any(
            _dangerous_shell_command(nested, argv_check, depth=depth + 1)
            for nested in nested_sources
        ):
            return True
    variables: dict[str, str] = {}
    for segment in _shell_segments(sanitized):
        assignments = _persistent_assignments(segment, variables)
        if assignments:
            variables.update(assignments)
            continue
        builtin_update = _builtin_variable_update(segment, variables)
        if builtin_update is not None:
            updates, removals = builtin_update
            variables.update(updates)
            for name in removals:
                variables.pop(name, None)
            continue
        resolved_segment = [
            _expand_known_variables(word, variables) for word in segment
        ]
        words = _unwrap_command(resolved_segment)
        if words is None:
            return True
        if not words:
            continue
        if argv_check(words):
            return True
        if _dynamic_command_word(words[0]) and any(
            argv_check([candidate, *words[1:]]) for candidate in ("rm", "git")
        ):
            return True
        if os.path.basename(words[0]) == "find":
            for executed in _find_executed_commands(words):
                nested_words = _unwrap_command(executed)
                if nested_words is None:
                    return True
                if nested_words and (
                    argv_check(nested_words)
                    or depth >= MAX_SHELL_RECURSION
                    or _dangerous_shell_command(
                        shlex.join(nested_words), argv_check, depth=depth + 1
                    )
                ):
                    return True
        if os.path.basename(words[0]) == "alias":
            for definition in words[1:]:
                _name, separator, alias_command = definition.partition("=")
                if not separator:
                    continue
                if depth >= MAX_SHELL_RECURSION or _dangerous_shell_command(
                    alias_command, argv_check, depth=depth + 1
                ):
                    return True
        complex_grammar = any(
            word in CONTROL_PREFIXES
            or word in {"case", "done", "esac", "fi", "function", "in", "}"}
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\(\)\{?", word)
            for word in resolved_segment
        )
        if complex_grammar:
            for word_index, word in enumerate(resolved_segment):
                if not any(
                    _command_name_matches(word, command_name)
                    for command_name in ("git", "rm")
                ):
                    continue
                nested_words = _unwrap_command(resolved_segment[word_index:])
                if nested_words is None or (nested_words and argv_check(nested_words)):
                    return True
        nested, unresolved_dynamic = _nested_argv_command(words, variables)
        if unresolved_dynamic:
            return True
        if nested is not None and (
            depth >= MAX_SHELL_RECURSION
            or _dangerous_shell_command(nested, argv_check, depth=depth + 1)
        ):
            return True
    return False


def _dangerous_rm(command: str) -> bool:
    return _dangerous_shell_command(command, _dangerous_rm_argv)


GIT_OPTIONS_WITH_VALUES = {
    "-C",
    "-c",
    "--config-env",
    "--git-dir",
    "--namespace",
    "--super-prefix",
    "--work-tree",
}


def _git_aliases(words: list[str]) -> dict[str, str]:
    """Return aliases defined by invocation-local Git configuration."""
    aliases: dict[str, str] = {}
    index = 1
    while index < len(words):
        word = words[index]
        value: str | None = None
        if word == "-c" and index + 1 < len(words):
            value = words[index + 1]
            index += 2
        elif word.startswith("-c") and word != "-c":
            value = word[2:]
            index += 1
        else:
            index += 1
        if value is None or not value.lower().startswith("alias."):
            continue
        alias_name, separator, alias_value = value.partition("=")
        if separator:
            aliases[alias_name[len("alias.") :].lower()] = alias_value
    return aliases


def _git_environment_aliases(words: list[str]) -> set[str]:
    """Return aliases whose invocation-local values come from the environment."""
    aliases: set[str] = set()
    index = 1
    while index < len(words):
        word = words[index]
        option_name = _unique_long_option(word, GIT_OPTIONS_WITH_VALUES)
        if option_name != "--config-env":
            index += 1
            continue
        _option, separator, attached = word.partition("=")
        if separator:
            value = attached
            index += 1
        elif index + 1 < len(words):
            value = words[index + 1]
            index += 2
        else:
            break
        key, value_separator, _environment_name = value.rpartition("=")
        if value_separator and key.lower().startswith("alias."):
            aliases.add(key[len("alias.") :].lower())
    return aliases


def _git_clean_force_disabled(words: list[str]) -> bool:
    """Return whether invocation-local config can make ``git clean`` forceful."""
    index = 1
    while index < len(words):
        word = words[index]
        value: str | None = None
        from_environment = False
        if word == "-c" and index + 1 < len(words):
            value = words[index + 1]
            index += 2
        elif word.startswith("-c") and word != "-c":
            value = word[2:].removeprefix("=")
            index += 1
        elif _unique_long_option(word, GIT_OPTIONS_WITH_VALUES) == "--config-env":
            _option, separator, attached = word.partition("=")
            if separator:
                value = attached
                index += 1
            elif index + 1 < len(words):
                value = words[index + 1]
                index += 2
            else:
                break
            from_environment = True
        else:
            index += 1
        if value is None:
            continue
        key, separator, configured = value.partition("=")
        if key.lower() != "clean.requireforce":
            continue
        if from_environment:
            return True
        if separator and configured.lower() in {"", "0", "false", "no", "off"}:
            return True
    return False


def _git_subcommand(words: list[str]) -> list[str]:
    """Remove Git global options and return its subcommand argv."""
    if not _command_name_matches(words[0], "git"):
        return []
    index = 1
    while index < len(words):
        word = words[index]
        if word == "--":
            return words[index + 1 :]
        if not word.startswith("-") or word == "-":
            return words[index:]
        option_name = word.split("=", 1)[0]
        matched_long = _unique_long_option(word, GIT_OPTIONS_WITH_VALUES)
        separate_value = (
            option_name in GIT_OPTIONS_WITH_VALUES or matched_long is not None
        ) and "=" not in word
        if word.startswith(("-C", "-c")) and word not in {"-C", "-c"}:
            separate_value = False
        index += 2 if separate_value else 1
    return []


def _dangerous_git_operation(words: list[str]) -> bool:
    """Return whether argv performs a destructive built-in Git operation."""
    argv = _git_subcommand(words)
    if not argv:
        return False
    if argv[0] == "reset":
        return any(
            word != "--" and word.startswith("--") and "--hard".startswith(word)
            for word in argv[1:]
        )
    if argv[0] != "clean":
        return False

    force = False
    for word in argv[1:]:
        if word != "--" and word.startswith("--"):
            force |= "--force".startswith(word)
        elif word.startswith("-") and not word.startswith("--"):
            force |= "f" in word[1:]
    return force


# pylint: disable-next=too-many-return-statements
def _dangerous_git_argv(words: list[str]) -> bool:
    aliases = _git_aliases(words)
    argv = _git_subcommand(words)
    if not argv:
        return False
    if argv[0] == "clean" and _git_clean_force_disabled(words):
        return True
    if argv[0].lower() in _git_environment_aliases(words):
        return True
    expanded = argv
    visited: set[str] = set()
    while expanded:
        if _dangerous_git_operation(["git", *expanded]):
            return True
        alias_name = expanded[0].lower()
        alias_value = aliases.get(alias_name)
        if alias_value is None or alias_name in visited:
            return False
        visited.add(alias_name)
        if alias_value.startswith("!"):
            shell_alias = alias_value[1:]
            return _dangerous_shell_command(
                shell_alias, _dangerous_rm_argv
            ) or _dangerous_shell_command(shell_alias, _dangerous_git_operation)
        try:
            alias_argv = shlex.split(alias_value)
        except ValueError:
            return True
        if not alias_argv:
            return False
        expanded = [*alias_argv, *expanded[1:]]
    return False


def _dangerous_git(command: str) -> bool:
    return _dangerous_shell_command(command, _dangerous_git_argv)


# pylint: disable-next=too-many-return-statements
def _contains_literal_secret(command: str) -> bool:
    normalized = _normalize_ansi_c_quotes(_collapse_line_continuations(command))
    if normalized is None:
        return True
    if URL_CREDENTIALS.search(normalized):
        return True
    for pattern in (SECRET_ASSIGNMENT, SECRET_FLAG, BEARER):
        if any(
            _literal_secret(match.group(1)) for match in pattern.finditer(normalized)
        ):
            return True
    for segment in _shell_segments(normalized):
        for index, word in enumerate(segment):
            name, separator, value = word.partition("=")
            if (
                separator
                and SECRET_NAME.fullmatch(name.removeprefix("--"))
                and _literal_secret(value)
            ):
                return True
            flag_name = word.removeprefix("--")
            if (
                word.startswith("--")
                and SECRET_NAME.fullmatch(flag_name)
                and index + 1 < len(segment)
                and _literal_secret(segment[index + 1])
            ):
                return True
        reconstructed = " ".join(segment)
        for pattern in (SECRET_ASSIGNMENT, SECRET_FLAG, BEARER):
            if any(
                _literal_secret(match.group(1))
                for match in pattern.finditer(reconstructed)
            ):
                return True
    return False


def _shell_pattern_matches(candidate: str, expected: str) -> bool:
    """Return whether one literal shell pattern can expand to expected."""
    remaining = 2_048

    def matches(pattern: str, depth: int = 0) -> bool:
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth >= 16:
            return True
        brace = re.search(r"\{([^{}]*,[^{}]*)\}", pattern)
        if brace is not None:
            prefix = pattern[: brace.start()]
            suffix = pattern[brace.end() :]
            return any(
                matches(f"{prefix}{alternative}{suffix}", depth + 1)
                for alternative in brace.group(1).split(",")
            )
        if any(marker in pattern for marker in ("*", "?", "[")):
            # Shell pathname expansion does not let a wildcard consume a
            # component's leading dot unless the pattern names that dot.
            if expected.startswith(".") and not pattern.startswith("."):
                return False
            return fnmatch.fnmatchcase(expected, pattern)
        return pattern == expected

    return matches(candidate)


def _model_unresolved_sensitive_path(
    path: str, variable_reference: re.Pattern[str], home: str
) -> str:
    """Model unknown values only where they can name a sensitive dot path."""
    components = path.split("/")
    first_home_child: int | None = None
    if path.startswith("~/"):
        first_home_child = 1
    elif path.startswith(f"{home}/"):
        first_home_child = len(home.split("/"))
    for index, component in enumerate(components):
        if variable_reference.search(component) and (
            index == first_home_child or component.startswith(".")
        ):
            components[index] = variable_reference.sub("{*,.*}", component)
    return "/".join(components)


def _expanded_sensitive_path_words(command: str) -> list[str]:
    """Expose literal and potentially sensitive shell-variable path components."""
    home = str(Path.home())
    variables = {"HOME": home}
    words: list[str] = []
    variable_reference = re.compile(
        r"\$\{[A-Za-z_][A-Za-z0-9_]*(?::?[-+=?][^{}]*)?\}"
        r"|\$[A-Za-z_][A-Za-z0-9_]*"
    )
    for segment in _shell_segments(command):
        assignments = _persistent_assignments(segment, variables)
        if assignments:
            variables.update(assignments)
        builtin_update = _builtin_variable_update(segment, variables)
        if builtin_update is not None:
            updates, removals = builtin_update
            variables.update(updates)
            for name in removals:
                variables.pop(name, None)
        for word in segment:
            expanded = _expand_known_variables(word, variables)
            words.append(
                _model_unresolved_sensitive_path(expanded, variable_reference, home)
            )
    return words


# pylint: disable-next=too-many-return-statements
def _contains_sensitive_path(command: str, *, depth: int = 0) -> bool:
    normalized = _normalize_ansi_c_quotes(_collapse_line_continuations(command))
    if normalized is None:
        return True
    normalized = _without_shell_comments(normalized)
    materialized = _materialize_literal_substitutions(
        normalized, include_double_quoted=True
    )
    if (
        materialized is not None
        and materialized != normalized
        and (
            depth >= MAX_SHELL_RECURSION
            or _contains_sensitive_path(materialized, depth=depth + 1)
        )
    ):
        return True
    if SENSITIVE_PATH_REFERENCE.search(normalized):
        return True
    words = [word for segment in _shell_segments(normalized) for word in segment]
    words.extend(_expanded_sensitive_path_words(normalized))
    for word in words:
        segments = [segment.strip("(),:") for segment in word.split("/")]
        candidates = [segment.rsplit("=", 1)[-1] for segment in segments]
        ssh_index = next(
            (
                index
                for index, candidate in enumerate(candidates)
                if _shell_pattern_matches(candidate, ".ssh")
            ),
            None,
        )
        if ssh_index is not None:
            remainder = candidates[ssh_index + 1 :]
            tracked_ssh_root = (
                ssh_index > 0
                and candidates[ssh_index - 1] == "dotfiles"
                and not any(remainder)
            )
            public_config = remainder == ["config"] or (
                remainder and remainder[0] == "config.d" and ".." not in remainder
            )
            public_key = (
                remainder and remainder[-1].endswith(".pub") and ".." not in remainder
            )
            if not (tracked_ssh_root or public_config or public_key):
                return True
            continue
        gnupg_index = next(
            (
                index
                for index, candidate in enumerate(candidates)
                if _shell_pattern_matches(candidate, ".gnupg")
            ),
            None,
        )
        if gnupg_index is not None:
            remainder = candidates[gnupg_index + 1 :]
            if any(
                _shell_pattern_matches(candidate, "private-keys-v1.d")
                for candidate in remainder
            ):
                return True
        for candidate in candidates:
            if _shell_pattern_matches(candidate, ".kube"):
                return True
            if candidate.endswith(".env.example"):
                continue
            if (
                candidate == ".env"
                or candidate.startswith(".env.")
                or candidate.endswith(".env")
            ):
                return True
    return False


def _option_value(words: list[str], names: set[str]) -> str | None:
    """Return the last value supplied for an option in one argv."""
    value: str | None = None
    for index, word in enumerate(words):
        name, separator, attached = word.partition("=")
        matched_long = _unique_long_option(word, names)
        if name in names or matched_long is not None:
            if separator:
                value = attached
            elif index + 1 < len(words):
                value = words[index + 1]
        elif word.startswith("-n") and "-n" in names and word != "-n":
            value = word[2:]
    return value


def _enabled_flag(words: list[str], short_name: str, long_name: str) -> bool:
    """Return whether a boolean CLI flag is enabled."""
    false_values = {"0", "false", "no", "off"}
    enabled = False
    for word in words:
        if word in (short_name, long_name):
            enabled = True
        elif word.startswith((f"{short_name}=", f"{long_name}=")):
            enabled = word.split("=", 1)[1].lower() not in false_values
    return enabled


def _has_finite_value(words: list[str], names: set[str]) -> bool:
    value = _option_value(words, names)
    return value is not None and value.lower() not in {"", "-1", "all"}


def _sed_terminates(words: list[str]) -> bool:
    """Return whether a sed program contains an executed quit command."""
    if not words or os.path.basename(words[0]) != "sed":
        return False
    scripts: list[str] = []
    index = 1
    while index < len(words):
        word = words[index]
        if word in {"-e", "--expression"} and index + 1 < len(words):
            scripts.append(words[index + 1])
            index += 2
            continue
        if word.startswith("--expression="):
            scripts.append(word.split("=", 1)[1])
        elif not word.startswith("-"):
            scripts.append(word)
            break
        index += 1
    quit_command = re.compile(
        r"(?:^|[;\n{}])\s*(?:(?:\d+(?:,\d+)?)|(?:/[^/\n]*/))?\s*q"
        r"(?:\s*(?:;|$))"
    )
    return any(quit_command.search(script) for script in scripts)


def _bounded_consumer(words: list[str]) -> bool:
    if not words:
        return False
    executable = os.path.basename(words[0])
    if executable in {"head", "tail"}:
        value = _option_value(words, {"-n", "--lines"})
        return value is None or (value.isdigit() and int(value) >= 0)
    if executable == "sed":
        return "-n" in words or "--quiet" in words or "--silent" in words
    if executable == "rg":
        return _has_finite_value(words, {"-m", "--max-count"})
    return False


def _terminating_consumer(words: list[str]) -> bool:
    if not words:
        return False
    executable = os.path.basename(words[0])
    if executable == "head":
        value = _option_value(words, {"-n", "--lines"})
        return value is None or (value.isdigit() and int(value) >= 0)
    if executable == "rg":
        return _has_finite_value(words, {"-m", "--max-count"})
    return _sed_terminates(words)


# pylint: disable-next=too-many-return-statements
def _log_command(words: list[str]) -> tuple[str, list[str]] | None:
    """Return a supported log producer and the argv after its executable."""
    unwrapped = _unwrap_command(words)
    if not unwrapped:
        return None
    executable = os.path.basename(unwrapped[0])
    arguments = unwrapped[1:]
    if executable == "journalctl":
        return executable, arguments
    if executable == "kubectl":
        if "--" in arguments:
            arguments = arguments[: arguments.index("--")]
        if "logs" in arguments:
            return executable, arguments[arguments.index("logs") + 1 :]
        return None
    if executable not in {"docker", "podman"}:
        return None
    try:
        log_index = arguments.index("logs")
    except ValueError:
        return None
    global_options_with_values = {
        "-H",
        "--config",
        "--connection",
        "--context",
        "--host",
        "--log-level",
        "--url",
    }
    prefix: list[str] = []
    prefix_index = 0
    while prefix_index < log_index:
        word = arguments[prefix_index]
        name = word.split("=", 1)[0]
        if name in global_options_with_values:
            prefix_index += 1 if "=" in word else 2
        elif word.startswith("-"):
            prefix_index += 1
        else:
            prefix.append(word)
            prefix_index += 1
    if prefix and prefix[-1] not in {"compose", "container"}:
        return None
    return executable, arguments[log_index + 1 :]


def _producer_is_bounded(kind: str, words: list[str]) -> bool:
    if kind == "kubectl":
        return _has_finite_value(
            words, {"--limit-bytes", "--since", "--since-time", "--tail"}
        )
    if kind in {"docker", "podman"}:
        return _has_finite_value(words, {"--since", "--tail", "--until"})
    return _has_finite_value(words, {"-n", "--lines", "--since", "--until"})


# Log parsing shares bounded shell state to recognize nested producers/consumers.
# pylint: disable-next=too-many-branches,too-many-locals,too-many-return-statements,too-many-statements
def _unbounded_logs(command: str, *, depth: int = 0) -> bool:
    command = _collapse_line_continuations(command)
    sanitized, shell_inputs, _expanding_inputs = _heredoc_view(command)
    sanitized = _without_shell_comments(sanitized)
    nested_sources = [
        *shell_inputs,
        *_literal_command_substitutions(command),
        *_literal_command_groups(command),
        *_literal_shell_inputs(command),
    ]
    if nested_sources:
        if depth >= MAX_SHELL_RECURSION:
            return True
        if any(_unbounded_logs(nested, depth=depth + 1) for nested in nested_sources):
            return True

    variables: dict[str, str] = {}
    parts: list[tuple[list[str], str]] = []
    for segment, operator in _shell_parts(sanitized):
        assignments = _persistent_assignments(segment, variables)
        if assignments:
            variables.update(assignments)
            parts.append((segment, operator))
            continue
        builtin_update = _builtin_variable_update(segment, variables)
        if builtin_update is not None:
            updates, removals = builtin_update
            variables.update(updates)
            for name in removals:
                variables.pop(name, None)
            parts.append((segment, operator))
            continue
        resolved_segment = [
            _expand_known_variables(word, variables) for word in segment
        ]
        parts.append((resolved_segment, operator))
        words = _unwrap_command(resolved_segment)
        if not words:
            continue
        nested, unresolved_dynamic = _nested_argv_command(words, variables)
        if unresolved_dynamic:
            return True
        if nested is not None and (
            depth >= MAX_SHELL_RECURSION or _unbounded_logs(nested, depth=depth + 1)
        ):
            return True
        if os.path.basename(words[0]) == "find":
            for executed in _find_executed_commands(words):
                nested_words = _unwrap_command(executed)
                if nested_words is None:
                    return True
                if nested_words and (
                    depth >= MAX_SHELL_RECURSION
                    or _unbounded_logs(shlex.join(nested_words), depth=depth + 1)
                ):
                    return True
        complex_grammar = any(
            word in CONTROL_PREFIXES
            or word in {"case", "done", "esac", "fi", "function", "in", "}"}
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\(\)\{?", word)
            for word in resolved_segment
        )
        if complex_grammar:
            for word_index in range(len(resolved_segment)):
                nested_words = resolved_segment[word_index:]
                if _log_command(nested_words) is None:
                    continue
                if depth >= MAX_SHELL_RECURSION or _unbounded_logs(
                    shlex.join(nested_words), depth=depth + 1
                ):
                    return True

    for index, (segment, operator) in enumerate(parts):
        producer = _log_command(segment)
        if producer is None:
            continue
        kind, words = producer
        consumers: list[list[str]] = []
        next_index = index + 1
        next_operator = operator
        while "|" in next_operator and next_index < len(parts):
            consumer_segment, next_operator = parts[next_index]
            consumer = _unwrap_command(consumer_segment)
            if consumer:
                consumers.append(consumer)
            next_index += 1
        bounded_pipe = any(_bounded_consumer(consumer) for consumer in consumers)
        terminating_pipe = any(
            _terminating_consumer(consumer) for consumer in consumers
        )
        follows = _enabled_flag(words, "-f", "--follow")
        if follows and not terminating_pipe:
            return True
        if not follows and not bounded_pipe and not _producer_is_bounded(kind, words):
            return True
    return False


def policy_reason(command: str) -> str | None:
    """Return a generic denial reason without echoing sensitive input."""
    if _dangerous_rm(command) or _dangerous_git(command):
        return "Broad destructive command blocked by the portable Codex policy."
    if _contains_literal_secret(command):
        return (
            "Credential-shaped literal blocked; use a protected file or "
            "environment reference."
        )
    if _contains_sensitive_path(command):
        return "Sensitive local path blocked by the portable Codex policy."
    if _unbounded_logs(command):
        return "Unbounded log command blocked; add a line, time, or output limit."
    return None


def _deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(payload, separators=(",", ":")))


def main() -> None:
    """Evaluate one Codex hook event from standard input."""
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError, OSError:
        return
    if not isinstance(event, dict):
        return
    event_name = event.get("hook_event_name")
    if event_name != "PreToolUse" or event.get("tool_name") != "Bash":
        return
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return
    command = tool_input.get("command")
    if not isinstance(command, str):
        return
    reason = policy_reason(command)
    if reason:
        _deny(reason)


if __name__ == "__main__":
    main()
