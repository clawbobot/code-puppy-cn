# P0 Acceptance

GitHub publication remains blocked until every required item below passes.

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
pup-cn-doctor --live
```

The live check must execute one harmless real Tool Calling request. Reports must
not contain credential values. JSON field names remain English in both locales.

## Real coding loops

Run three isolated loops for Alibaba Cloud and DeepSeek:

```bash
uv run python scripts/live_acceptance.py \
  --model <configured-model-key> --locale zh-CN --runs 3 \
  --output work/acceptance/<provider>-zh-CN.json
```

Run at least one English loop per provider:

```bash
uv run python scripts/live_acceptance.py \
  --model <configured-model-key> --locale en-US --runs 1 \
  --output work/acceptance/<provider>-en-US.json
```

Required success rate: at least 80% for both Alibaba Cloud and DeepSeek.

## Automated regression

```bash
uv run pytest tests/cn -q --no-cov
uv run ruff check code_puppy tests/cn scripts
uv build
```

The complete upstream non-integration suite must also pass before publication.
