# How to Contribute?

## Purpose

This page is how to contribute: reporting a bug, proposing a feature, the AI-free principle, and naming and
describing branches and pull requests. Anyone who wants to contribute reads it.

Read before: [README](README.md) · Next: [Developer guide](DEVELOPER.md)

## Contents

- [Identifying and Reporting Bugs](#identifying-and-reporting-bugs)
- [Proposing New Features](#proposing-new-features)
- [AI-free Principle](#ai-free-principle)
- [Contributing to Development](#contributing-to-development)
- [Branch Naming](#branch-naming)
- [PR Naming](#pr-naming)
- [PR Description](#pr-description)
- [Target Branches](#target-branches)

## **Identifying and Reporting Bugs**
* **Ensure the bug has not already been reported** by searching our **[GitHub Issues](https://github.com/AbsaOSS/living-doc-toolkit/issues)**.
* If you cannot find an open issue describing the problem, use the **Bug report** template to open a new one. Tag it with the **bug** label.

## **Proposing New Features**

* **Check if the feature has already been requested** by searching through our **[GitHub Issues](https://github.com/AbsaOSS/living-doc-toolkit/issues)**.
* If the feature request doesn't exist, feel free to create a new one. Tag it with the **request** label.

## AI-free Principle

This pipeline runs AI-free; contributions must keep every collect → normalize → generate step deterministic — no LLM call in that path.

## Contributing to Development

* Check _Issues_ for the desired feature or bug and make sure no one else is already working on it. If it is not filed yet, create a detailed issue first.
* Fork the repository and create a working branch off an issue (see **Branch Naming** below).
* Write the code and include tests for it.
* Commit messages should reference the GitHub Issue and give a concise description, e.g. `#34 - Implement Feature X`.
* Push to your fork and open a Pull Request (see **PR Naming**, **PR Description**, and **Target Branches** below).

**Monorepo PR scope.** Prefer PRs that touch a single package. Split a change that spans multiple packages unless they must change together (e.g. an adapter and the contract it implements).

## Branch Naming

Branches have to start with one of the allowed prefixes, followed immediately by the issue number, then a kebab-case scope: `<prefix>/<issue>-<scope>`.

- `feature/`: new functionality and enhancements
- `fix/`: bug fixes and defect resolutions
- `docs/`: documentation-only updates; a docs-only PR uses `docs/`, not `feature/`
- `chore/`: maintenance, CI, dependency bumps and non-behavioural refactors

Examples:
- `feature/542-add-hierarchy-support`
- `fix/567-handle-empty-response`
- `docs/203-contributing-rework`
- `chore/318-update-ci-python-version`

Use lowercase kebab-case, hyphens only, and reflect the actual scope; avoid vague terms such as `update` or `changes`. The `check-pr-requirements` CI check rejects a branch that has no issue number.

Rename before pushing if needed:
```shell
git branch -m <prefix>/<issue>-<new-scope>
```

Check the current branch:
```shell
git rev-parse --abbrev-ref HEAD | grep -E '^(feature|fix|docs|chore)/[0-9]+-' \
  || echo 'Branch naming violation (expected <prefix>/<issue>-<scope>)'
```

`refactor/` and `perf/` may become prefixes later; they are not enforced yet.

## PR Naming

PR titles have to carry the related issue number, using one of these formats: `#123: Title` or `123 - Title`.

Examples:
- `#567: Handle empty response`
- `203 - Rework contribution guide`

## PR Description

The PR body has to include these sections: `## Overview`, `## Release Notes`, `## Related`.
- **Overview** – what changed and why.
- **Release Notes** – short, user-facing summary for the changelog.
- **Related** – link the issue with a closing keyword, e.g. `Closes #123` or `Fixes AB#12345`.

## Target Branches

PRs have to target `main`, `master`, `support/*`, or `release/*`.

### Community and Communication

If you have any questions or need help, don't hesitate to reach out through our GitHub discussion section. We're here to help!

#### Thanks!

Your contributions are invaluable to us. Thank you for being part of the AbsaOSS community and helping us grow and improve!

The AbsaOSS Team
