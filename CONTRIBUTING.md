# Contributing to Code Puppy CN

Code Puppy CN is a thin distribution of
[Code Puppy](https://github.com/mpfaffenberger/code_puppy). Contributions
should preserve that relationship and avoid duplicating upstream capabilities.

## Before opening a change

1. Check whether the capability already exists upstream.
2. Keep generic runtime improvements suitable for an upstream contribution.
3. Keep China-region setup, diagnostics, and translations in the CN experience
   layer.
4. Do not add provider implementations, model aliases, or real credentials.

## Local checks

```bash
uv sync --dev
uv run ruff check code_puppy tests/cn scripts
uv run pytest tests/cn -q --no-cov
uv build
```

Changes to shared runtime behavior should also run the complete non-integration
suite:

```bash
uv run pytest tests --ignore tests/integration
```

See [UPSTREAM.md](UPSTREAM.md) for the synchronization policy and
[docs/P0_ACCEPTANCE.md](docs/P0_ACCEPTANCE.md) for the release gate.
