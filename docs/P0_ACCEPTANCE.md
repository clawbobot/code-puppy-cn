# P0 Acceptance

The first packaged release remains blocked until every required item below
passes.

## Clean installation

```bash
uv tool install --force .
pup-cn --version
```

For the optional Google Vertex user plugin:

```bash
uv tool install --force --with "pydantic-ai-slim[google]==1.56.0" .
```

The expected version is `0.1.0`.

## Interactive setup

```text
/language zh-CN
/cn-setup
```

Verify provider selection, dynamically ranked models, masked credential input,
configuration persistence, immediate model activation, and no `cn-` model alias.

The non-interactive equivalent is:

```text
/cn-setup list
/cn-setup deepseek <model-id>
```

## Diagnostics

```bash
pup-cn-doctor --json --no-network
```

Reports must not contain credential values. JSON field names remain English in
both locales. `pup-cn-doctor --live` is available as an optional provider check
but is not required for `0.1.0`.

## Live-provider validation

Real provider calls are not a release gate for `0.1.0`. They remain available
as an optional post-release quality exercise through `scripts/live_acceptance.py`.
No provider credentials are required by CI or the release workflow.

## Automated regression

```bash
uv run pytest tests/cn -q --no-cov
uv run ruff check code_puppy tests/cn scripts
uv build
uv run --no-project python scripts/smoke_package.py dist/*.whl
```

The complete upstream non-integration suite must also pass before publication.
