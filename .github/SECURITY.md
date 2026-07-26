# Security policy

## Supported versions

Security fixes are applied to the latest minor release.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose data, execute unintended commands, escape an isolation boundary, or modify files outside a declared workspace. Use GitHub's private vulnerability reporting for the repository.

Include the affected command, operating system, version, reproduction steps, impact, and any known mitigation. Remove real credentials and personal data from logs.

## Trust boundaries

This tool may execute user-supplied commands or inspect a selected target
program.

- Run contracts, scenarios, and scripts only from sources you trust.
- Treat Docker images, installers, completion scripts, test commands, and
  selected executables as code.
- Isolation and tracing features reduce a specific risk; they are not a general
  sandbox for untrusted programs.
- Review report contents before sharing them.

The tool does not upload reports or telemetry.
