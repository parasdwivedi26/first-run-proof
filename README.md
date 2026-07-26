# FirstRun Proof

FirstRun Proof executes all shell blocks from one Markdown section as a single stateful workflow.

## Install

```shell
python -m pip install .
```

```shell
firstrun verify README.md --section quick-start --image ubuntu:latest
```

A dual shell/PowerShell demonstration is available at [`examples/README.md`](examples/README.md).

The container receives the README directory at `/workspace`. Variables, working-directory changes, and files persist between blocks because they are combined into one shell program. A local mode is available for quick iteration:

```shell
firstrun verify README.md --section quick-start --local
```

Local mode is not a clean-room proof. Container mode is the CI-ready path.

Supported fences are `shell`, `sh`, `bash`, `powershell`, `pwsh`, and `console`. `--shell auto` selects native PowerShell for local Windows runs and `sh` for Linux or the default container path. Use `--shell powershell` with an image that contains `pwsh`. In `console` blocks, lines beginning with `$ ` are commands and lines beginning with `> ` continue the preceding command.

The report contains the first failing block number, captured output, missing-command hints, referenced-but-unset environment variables, local ports, and timeout/interactivity hints. `--github-summary PATH` writes a compact Markdown result.

## Development

```shell
python -m unittest discover -s tests -v
```

FirstRun Proof supports native Windows and Linux. Docker is recommended for the clean-room guarantee.

## Project

- [Changelog](CHANGELOG.md)
- [Contributing](.github/CONTRIBUTING.md)
- [Security policy](.github/SECURITY.md)
- [Code of conduct](.github/CODE_OF_CONDUCT.md)
- [Release process](docs/releasing.md)
- [MIT license](LICENSE)
