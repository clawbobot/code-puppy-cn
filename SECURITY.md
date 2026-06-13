# Security Policy

## Supported versions

Code Puppy CN is currently a pre-release MVP. Security fixes are applied to the
latest development branch and, after the first release, to the latest published
version.

## Reporting a vulnerability

Do not open a public issue containing credentials, private endpoints, customer
data, or exploit details. Use the repository owner's private security reporting
channel after the public repository is created.

Until that channel is available, retain the report privately and provide only a
sanitized notice through the maintainer's published contact channel.

## Credential handling

- Supply provider credentials through environment variables or Code Puppy's
  local configuration.
- Never commit `.env`, private keys, OAuth codes, diagnostic dumps containing
  secrets, or `~/.code_puppy` configuration.
- Diagnostic output and bug reports must be reviewed and redacted before
  sharing.
- Revoke and rotate any credential that has been pasted into chat, logs, issue
  trackers, or source control.
