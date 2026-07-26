from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from shutil import which
from typing import Mapping, Sequence


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def run(
    command: Sequence[str],
    *,
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = 30,
    input_text: str | None = None,
) -> CommandResult:
    parts = [str(part) for part in command]
    try:
        completed = subprocess.run(
            parts, cwd=cwd, env=dict(env) if env else None, input=input_text,
            text=True, encoding="utf-8", errors="replace", capture_output=True,
            timeout=timeout,
        )
        return CommandResult(parts, completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else exc.stderr or ""
        return CommandResult(parts, 124, stdout, stderr, True)
    except OSError as exc:
        return CommandResult(parts, 127, "", str(exc))


def executable_available(name: str) -> bool:
    return which(name) is not None


def write_json(path: str | Path, value: object) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def print_report(report: dict, *, json_output: bool = False) -> None:
    if json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"{report.get('status', 'unknown').upper()}: {report.get('summary', '')}".rstrip())
    for item in report.get("findings", []):
        print(f"- {item}")

