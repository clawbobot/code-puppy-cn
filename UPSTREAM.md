# Upstream Collaboration

Code Puppy CN is a thin, MIT-licensed distribution of
[Code Puppy](https://github.com/mpfaffenberger/code_puppy).

## Repository layout

- `upstream` tracks the original Code Puppy repository.
- CN-specific release work is maintained on this repository's `main` branch.
- The Python package remains `code_puppy` to minimize merge conflicts.
- Public commands are `code-puppy-cn`, `pup-cn`, and `pup-cn-doctor`.

## Change ownership

Suitable for upstream contribution:

- Generic JSON-backed internationalization runtime.
- Locale normalization, fallback, and interpolation behavior.
- Locale-neutral command registration hooks.

Distribution-specific:

- Simplified Chinese resources and onboarding copy.
- `/cn-setup` and `/doctor-cn`.
- China provider discovery and compatibility checks.
- The localized `code-fix` skill and optional metadata-only audit log.

## Sync procedure

```bash
git fetch upstream
git merge upstream/main
uv sync --dev
uv run pytest tests/cn
```

Resolve conflicts by preserving upstream provider, model, agent, MCP, and skill
implementations. CN code should compose those capabilities rather than copy them.

The current release baseline is recorded in [NOTICE-CN.md](NOTICE-CN.md).
