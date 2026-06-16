# Codex for Open Source Application Task

## Objective

Apply for OpenAI's Codex for Open Source program using the public
`clawbobot/code-puppy-cn` repository after the first release is validated.

Official program page:

- https://developers.openai.com/community/codex-for-oss
- https://openai.com/form/codex-for-oss/

The program is intended for active open-source maintainers. Selected
maintainers may receive six months of ChatGPT Pro with Codex, API credits for
open-source maintenance work, and conditional access to Codex Security.

## Current Readiness

Repository:

- Public URL: https://github.com/clawbobot/code-puppy-cn
- License: MIT
- Status: pre-release MVP
- Current public adoption signal: early, not yet strong

Assessment:

Apply after `v0.1.0` is published and the repository has enough public evidence
to support the application. Do not present the project as widely adopted before
there is real usage, stars, forks, issues, downstream users, or maintainer
workflow evidence.

## Required Application Inputs

The official form asks for:

- First name and last name.
- Email associated with the ChatGPT account.
- GitHub username with public profile visibility.
- Public GitHub repository URL.
- Maintainer role: primary maintainer or core maintainer.
- Why the repository qualifies, up to 500 characters.
- Interest area: Codex Security and/or API credits.
- OpenAI Organization ID.
- How API credits will be used, up to 500 characters.
- Optional additional context, up to 500 characters.

## Evidence To Prepare

Before submitting, collect:

- `v0.1.0` GitHub Release URL.
- Passing GitHub Actions run for the release commit.
- Installation and smoke-test proof from a clean machine.
- README and bilingual user guide links.
- Short explanation of why China-region model setup and bilingual CLI/TUI access
  helps developers maintain open-source projects.
- Maintainer workflow examples:
  - issue triage;
  - pull request review;
  - release workflow automation;
  - deterministic defect-fix demo;
  - optional Codex Security use case.
- Any public adoption signals available at submission time:
  - stars;
  - forks;
  - issues or discussions;
  - external users;
  - downloads;
  - downstream projects.

## Suggested Form Draft

Repository URL:

```text
https://github.com/clawbobot/code-puppy-cn
```

Role:

```text
Primary maintainer
```

Why does this repository qualify? Keep under 500 characters:

```text
code-puppy-cn is an MIT-licensed bilingual distribution of Code Puppy for
developers who need Chinese/English workflows and easier access to
China-available models. It preserves upstream compatibility while adding
setup, diagnostics, docs, and deterministic maintenance demos for OSS coding,
review, and release workflows.
```

How will you use API credits for your project? Keep under 500 characters:

```text
Use credits to validate Codex-assisted OSS maintenance workflows: issue triage,
pull request review, release checks, bilingual documentation updates, and
deterministic defect-fix demos. Results will be used to improve the public repo,
document reproducible workflows, and reduce maintainer review and testing load.
```

Anything else we should know? Keep under 500 characters:

```text
This is an early-stage public fork/distribution. The first release focuses on
transparent upstream compatibility, bilingual UX, diagnostics, and safe model
configuration. We will share public evidence from CI, release artifacts, docs,
and maintainer workflow demos rather than claiming broad adoption prematurely.
```

## Submission Checklist

- [ ] Publish `v0.1.0`.
- [ ] Confirm repository remains public.
- [ ] Confirm GitHub profile visibility is public.
- [ ] Record latest passing CI URL.
- [ ] Record release URL.
- [ ] Confirm README and docs describe user value clearly.
- [ ] Collect adoption and workflow evidence.
- [ ] Find OpenAI Organization ID in the OpenAI Platform dashboard.
- [ ] Review the Codex for Open Source Program Terms.
- [ ] Submit the official form.
- [ ] Save submission date and follow-up status in this document.

## Follow-Up Tracking

| Date | Status | Notes |
| ---- | ------ | ----- |
| TBD  | Draft  | Waiting for `v0.1.0` release and public evidence. |
