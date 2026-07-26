# Release checklist

This project is versioned and published independently.

1. Update the version in `pyproject.toml` and `src/<package>/__init__.py`.
2. Add user-visible changes to `CHANGELOG.md`.
3. Run the test suite on native Windows and Linux.
4. Build with `python -m build`.
5. Install the wheel in a clean environment and run
   `python -m <package> --help`.
6. Create an annotated tag such as
   `git tag -a v0.1.0 -m "Version 0.1.0"`.
7. Push the tag. The release workflow builds the wheel and source distribution
   and attaches both to the matching GitHub release.

PyPI publishing should use trusted publishing. Report schemas are public
interfaces: add fields freely in a minor release, but do not remove or rename
existing fields without a documented major-version migration.
