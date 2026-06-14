# Security Policy

## Supported versions

Security fixes are applied to the latest published version and the `main`
branch. Older releases may be asked to upgrade before a fix is provided.

## Reporting a vulnerability

Do not open a public issue containing credentials, private endpoints, customer
data, or exploit details. Use GitHub's private vulnerability reporting for this
repository:

https://github.com/clawbobot/code-puppy-cn/security/advisories/new

If private reporting is unavailable, retain the details privately and open only
a sanitized issue asking the maintainer to establish a secure contact channel.

## Credential handling

- Supply provider credentials through environment variables or Code Puppy's
  local configuration.
- Never commit `.env`, private keys, OAuth codes, diagnostic dumps containing
  secrets, or `~/.code_puppy` configuration.
- Diagnostic output and bug reports must be reviewed and redacted before
  sharing.
- Revoke and rotate any credential that has been pasted into chat, logs, issue
  trackers, or source control.
