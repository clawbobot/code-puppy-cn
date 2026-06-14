# Code Puppy CN MVP Acceptance

## Supported flow

1. Install `code-puppy-cn`.
2. Start with `pup-cn`.
3. Select Chinese or English on first launch.
4. Run `/cn-setup` and configure a model through the upstream models.dev registry.
5. Run `/doctor-cn` or `pup-cn-doctor --json`.
6. Open `demo/code-fix`, invoke the `code-fix` skill, and repair the failing test.
7. Confirm that the assistant edits the file, runs the test, and summarizes the
   result in the active interface language.

## Automated checks

```bash
uv run pytest tests/cn
uv run ruff check code_puppy tests/cn
uv build
```

## Optional live checks

Live provider calls require credentials supplied only through environment
variables. Never commit keys or generated credential files.

```bash
export DASHSCOPE_API_KEY=...
export DEEPSEEK_API_KEY=...
pup-cn-doctor
```

Real coding loops are optional for the first release. Provider discovery,
configuration, redaction, and tool-calling compatibility remain covered by
contract tests without requiring secrets in CI.

## Release gate

- Windows, macOS, and Ubuntu CI passes.
- Python 3.11, 3.13, and 3.14 are represented in CI.
- English and Chinese catalogs have matching keys and valid placeholders.
- Diagnostic JSON remains English-keyed regardless of interface locale.
- No provider or model aliases are added.
- No secrets appear in the repository or test output.
- The built wheel installs and runs diagnostics in a clean environment.
