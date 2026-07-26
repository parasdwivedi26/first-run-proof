"""FirstRun Proof command implementation."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path

from .common import CommandResult, executable_available, print_report, run, write_json


FENCE = re.compile(
    r"^```(?P<language>bash|sh|shell|console|powershell|pwsh)?\s*$",
    re.IGNORECASE,
)
ENV_REFERENCE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")


def extract_workflow(markdown: str, section: str, shell_name: str = "sh") -> list[str]:
    lines = markdown.splitlines()
    wanted = _slug(section)
    start = None
    level = None
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading and _slug(heading.group(2)) == wanted:
            start = index + 1
            level = len(heading.group(1))
            break
    if start is None:
        raise ValueError(f"section not found: {section}")

    end = len(lines)
    for index in range(start, len(lines)):
        heading = re.match(r"^(#{1,6})\s+", lines[index])
        if heading and len(heading.group(1)) <= level:
            end = index
            break

    blocks: list[str] = []
    in_fence = False
    current: list[str] = []
    console = False
    include = False
    for line in lines[start:end]:
        fence = FENCE.match(line) if not in_fence else None
        if fence:
            in_fence = True
            language = (fence.group("language") or "").lower()
            console = language == "console"
            compatible = (
                {"", "console", "powershell", "pwsh"}
                if shell_name == "powershell"
                else {"", "console", "bash", "sh", "shell"}
            )
            include = language in compatible
            current = []
            continue
        if in_fence and line.strip() == "```":
            command_lines = _console_commands(current) if console else current
            if include and command_lines:
                blocks.append("\n".join(command_lines))
            in_fence = False
            continue
        if in_fence:
            current.append(line)
    if not blocks:
        raise ValueError(f"section '{section}' has no {shell_name} code blocks")
    return blocks


def _console_commands(lines: list[str]) -> list[str]:
    commands = []
    for line in lines:
        if line.startswith("$ "):
            commands.append(line[2:])
        elif line.startswith("> ") and commands:
            commands[-1] += "\n" + line[2:]
    return commands


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_script(blocks: list[str], shell_name: str = "sh") -> str:
    prelude = "$ErrorActionPreference = 'Stop'\n" if shell_name == "powershell" else "set -eu\n"
    marked = []
    for index, block in enumerate(blocks, 1):
        marker = (
            f"Write-Output '__FIRSTRUN_STEP__:{index}'"
            if shell_name == "powershell"
            else f"printf '%s\\n' '__FIRSTRUN_STEP__:{index}'"
        )
        marked.append(marker + "\n" + block)
    return prelude + "\n\n".join(marked) + "\n"


def run_local(
    script: str, workspace: Path, timeout: float, shell_name: str = "auto"
) -> CommandResult:
    if shell_name == "auto":
        shell_name = "powershell" if os.name == "nt" and shutil.which("sh") is None else "sh"
    if shell_name == "powershell":
        shell = ["powershell", "-NoProfile", "-NonInteractive", "-Command", "-"]
    else:
        shell = ["sh", "-s"]
    return run(shell, cwd=workspace, input_text=script, timeout=timeout)


def run_container(
    script: str, workspace: Path, image: str, timeout: float, shell_name: str = "sh"
) -> CommandResult:
    if not executable_available("docker"):
        return CommandResult(["docker"], 127, "", "docker executable was not found")
    mount = f"{workspace.resolve()}:/workspace"
    shell = "pwsh" if shell_name == "powershell" else "sh"
    shell_args = ["-NoProfile", "-NonInteractive", "-Command", "-"] if shell_name == "powershell" else ["-s"]
    return run(
        ["docker", "run", "--rm", "-i", "-v", mount, "-w", "/workspace", image, shell, *shell_args],
        input_text=script,
        timeout=timeout,
    )


def diagnose(script: str, result: CommandResult, shell_name: str = "sh") -> list[str]:
    combined = result.stdout + "\n" + result.stderr
    findings = []
    command_missing = re.search(r"(?:not found|is not recognized).*?([A-Za-z0-9_.-]+)?", combined)
    if command_missing:
        findings.append("a command appears to be missing from the clean environment")
    permission = re.search(r"permission denied", combined, re.IGNORECASE)
    if permission:
        findings.append("a file or command is not executable by the new user")
    if shell_name == "powershell":
        referenced = set(
            re.findall(r"\$env:([A-Za-z_][A-Za-z0-9_]*)", script, re.IGNORECASE)
        )
    else:
        referenced = {
            first or second for first, second in ENV_REFERENCE.findall(script)
        }
    missing_vars = sorted(name for name in referenced if name not in os.environ)
    if missing_vars:
        findings.append("referenced environment variables are undocumented or unset: " + ", ".join(missing_vars))
    ports = sorted(set(re.findall(r"(?:localhost|127\.0\.0\.1):(\d{2,5})", script)))
    if ports:
        findings.append("the workflow expects local port(s): " + ", ".join(ports))
    if result.timed_out:
        findings.append("the workflow timed out; an interactive prompt or long-running service may be blocking")
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="firstrun")
    subparsers = parser.add_subparsers(dest="action", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("readme")
    verify.add_argument("--section", default="quick-start")
    mode = verify.add_mutually_exclusive_group()
    mode.add_argument("--image", help="Run in a fresh Docker image.")
    mode.add_argument("--local", action="store_true", help="Run locally (not a clean-room proof).")
    verify.add_argument(
        "--shell",
        choices=["auto", "sh", "powershell"],
        default="auto",
        help="Workflow language. Auto selects PowerShell on native Windows and sh elsewhere.",
    )
    verify.add_argument("--timeout", type=float, default=300)
    verify.add_argument("--output", default="firstrun-report.json")
    verify.add_argument("--log", default="firstrun.log")
    verify.add_argument("--github-summary")
    verify.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    readme = Path(args.readme).resolve()
    shell_name = args.shell
    if shell_name == "auto":
        shell_name = "powershell" if os.name == "nt" and not args.image else "sh"
    try:
        blocks = extract_workflow(
            readme.read_text(encoding="utf-8"), args.section, shell_name
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    script = build_script(blocks, shell_name)
    result = (
        run_container(script, readme.parent, args.image, args.timeout, shell_name)
        if args.image
        else run_local(script, readme.parent, args.timeout, shell_name)
    )
    findings = diagnose(script, result, shell_name)
    if result.exit_code and not findings:
        findings.append(f"the workflow exited with code {result.exit_code}")
    started_steps = [
        int(value)
        for value in re.findall(
            r"__FIRSTRUN_STEP__:(\d+)", result.stdout + "\n" + result.stderr
        )
    ]
    first_failed_step = started_steps[-1] if result.exit_code and started_steps else None
    report = {
        "status": "pass" if result.exit_code == 0 else "fail",
        "summary": (
            f"{len(blocks)} quick-start block(s) completed"
            if result.exit_code == 0
            else f"quick-start failed with exit code {result.exit_code}"
        ),
        "mode": f"container:{args.image}" if args.image else "local",
        "shell": shell_name,
        "section": args.section,
        "steps": blocks,
        "started_steps": started_steps,
        "first_failed_step": first_failed_step,
        "result": result.as_dict(),
        "findings": findings,
    }
    write_json(args.output, report)
    Path(args.log).write_text(result.stdout + result.stderr, encoding="utf-8")
    summary_path = args.github_summary or os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        Path(summary_path).write_text(_markdown_summary(report), encoding="utf-8")
    print_report(report, json_output=args.json)
    return 0 if result.exit_code == 0 else 1


def _markdown_summary(report: dict) -> str:
    icon = "PASS" if report["status"] == "pass" else "FAIL"
    lines = [f"## FirstRun Proof: {icon}", "", report["summary"], ""]
    lines.extend(f"- {finding}" for finding in report["findings"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
