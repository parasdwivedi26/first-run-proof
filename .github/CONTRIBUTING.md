# Contributing

Contributions are welcome when they make this proof more accurate, portable, or useful.

## Development setup

```shell
cd <tool-folder>
python -m pip install -e .
python -m unittest discover -s tests -v
```

Use Python 3.10 or newer. The project must remain installable and testable from
its repository root. Keep the Python runtime dependency-free unless a new
dependency removes more complexity than it adds.

## Before opening a pull request

1. Add or update a test that demonstrates the behavior.
2. Run the suite on your current operating system.
3. Update the relevant guide and limitation text.
4. Keep JSON report keys backward compatible within a minor release.
5. Avoid broad frameworks when a small function or backend is enough.

Platform-specific changes should include Windows and Linux behavior notes.
Platform-specific code is acceptable when the public CLI and report semantics
stay aligned.

## Commit and pull request scope

Prefer one focused change. A useful pull request explains the failure case, the command that reproduces it, and how the report changes. Generated reports, build output, and local test workspaces should not be committed.

## Reporting bugs

Include:

- operating system and Python version
- exact command, with secrets removed
- smallest safe input or contract
- exit code and report
- whether Docker, Git, a compiler, or a shell backend was involved
