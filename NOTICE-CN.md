# Code Puppy CN Notice

Code Puppy CN is a thin distribution based on
[Code Puppy](https://github.com/mpfaffenberger/code_puppy), originally created
by Michael Pfaffenberger and contributors.

The upstream project and this distribution are licensed under the MIT License.
China-region additions are intentionally kept in a small experience layer so
upstream fixes and features can continue to be merged.

Upstream baseline for Code Puppy CN 0.1.0:

- Version: `0.0.567`
- Commit: `6df8f79`

CN-specific changes:

- Separate package and command names.
- Runtime `en-US` / `zh-CN` internationalization.
- China-region provider filtering built on the upstream models.dev registry.
- Diagnostics, bilingual `code-fix` skill, and optional metadata-only audit.
