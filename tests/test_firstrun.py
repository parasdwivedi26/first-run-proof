import os
import tempfile
import unittest
from pathlib import Path

from firstrun_proof.cli import build_script, extract_workflow, main, run_local


class FirstRunTests(unittest.TestCase):
    def test_extracts_stateful_section_only(self):
        if os.name == "nt":
            shell_name = "powershell"
            first = "$Value = 'works'"
            second = "if ($Value -ne 'works') { exit 1 }"
            language = "powershell"
        else:
            shell_name = "sh"
            first = "VALUE=works"
            second = 'test "$VALUE" = works'
            language = "sh"
        blocks = extract_workflow(
            f"""# Project

## Quick start

```{language}
{first}
```

```{language}
{second}
```

## Other

```sh
exit 9
```
""",
            "quick-start",
            shell_name,
        )
        self.assertEqual(2, len(blocks))
        with tempfile.TemporaryDirectory() as directory:
            result = run_local(
                build_script(blocks, shell_name), Path(directory), 10, shell_name
            )
        self.assertEqual(0, result.exit_code, result.stderr + result.stdout)

    def test_main_writes_report_and_log(self):
        shell_name = "powershell" if os.name == "nt" else "sh"
        language = "powershell" if os.name == "nt" else "sh"
        command = "Write-Output ready" if os.name == "nt" else "printf 'ready\\n'"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readme = root / "README.md"
            readme.write_text(
                f"# Demo\n\n## Quick start\n\n```{language}\n{command}\n```\n",
                encoding="utf-8",
            )
            report = root / "report.json"
            log = root / "run.log"
            exit_code = main(
                [
                    "verify",
                    str(readme),
                    "--local",
                    "--shell",
                    shell_name,
                    "--output",
                    str(report),
                    "--log",
                    str(log),
                ]
            )
            self.assertTrue(report.exists())
            self.assertIn("ready", log.read_text(encoding="utf-8"))
        self.assertEqual(0, exit_code)


if __name__ == "__main__":
    unittest.main()
