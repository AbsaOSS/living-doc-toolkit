# Living Documentation Toolkit

[![CI](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/test.yml)
[![Integration Tests](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/integration.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-toolkit/actions/workflows/integration.yml)

## Purpose

A GitHub Action that runs one toolkit command per step: it turns the JSON a collector wrote into the file a
generator reads. It is the normalize step of a living-documentation pipeline, between `living-doc-collector-gh` and
`living-doc-generator-markdown`; it carries every transformation and renders nothing.

## Contents

- [Overview](#overview)
- [Usage tip](#usage-tip)
- [Inputs and outputs](#inputs-and-outputs)
- [Where next](#where-next)
- [Developer Guide](#developer-guide)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview

- **`normalize-docs`**: one `doc-source.json` to `generator-ready.json`, with every authored field of every entity the view keeps, and the input's warnings → [command](packages/services/normalize_docs/README.md)
- **`normalize-tests`**: one `ui-tests.json` to `ui-test-catalog.json`, each scenario unchanged, grouped by feature file and by every User Story or Functionality it links → [command](packages/services/normalize_tests/README.md)
- **`coverage-matrix`**: one `doc-source.json` and one `ui-tests.json` to `coverage-matrix.json` → [command](packages/services/coverage_matrix/README.md)
  - It counts each `active` or `deprecated` acceptance criterion of User Stories and Functionalities, per declared aspect, from linking scenarios.
  - It adds a summary per entity, for the whole matrix and for the planned work; a scenario link it does not count as written is a warning in the file.
- One command per step, through the composite action at the repository root → [Action reference](docs/action.md)
- Contract artifacts only: a command reads its inputs through `living-doc-utilities`' `read_artifact`, and validates them together before it transforms them → [Core](packages/core/README.md)
- No copy of a contract: the models and schemas come from the installed `living-doc-utilities` (`==0.8.0`) → [Contracts](https://github.com/AbsaOSS/living-doc-utilities/tree/master/docs/contracts)
- Pipeline-ready: it chains with the other `living-doc-*` actions → [The frame](https://github.com/AbsaOSS/living-doc/blob/master/docs/introduction/principles.md#the-frame)
- GitHub Actions first: a step in a workflow is the supported way to run it; a local run is a development and debugging aid, not a second deployment target → [CLI run](DEVELOPER.md#cli-run), [Local Integration Run](DEVELOPER.md#local-integration-run)
- AI-free: collect → normalize → generate is deterministic tooling, with no LLM call anywhere in that path → [AI-free Principle](CONTRIBUTING.md#ai-free-principle)
  - The tooling is Python, JSON Schema validation, and Jinja2 and Markdown templates.
  - The agentic layer in [`living-doc` `agentic/`](https://github.com/AbsaOSS/living-doc/tree/master/agentic) can speed up authoring GitHub Issues and `.feature` files.
  - It is never a runtime dependency: a human writing the same input by hand is a fully supported, identical path.

## Usage tip

One step that normalizes a collector's documentation output, after `actions/setup-python`
([Prerequisites](docs/action.md#prerequisites)):

```yaml
- name: Normalize the collected documentation
  id: normalize
  uses: AbsaOSS/living-doc-toolkit@v0.1.0
  with:
    command: normalize-docs
    input: doc-source.json
    output: output/generator-ready.json
    view: release
    document-title: Payments service
```

The three commands chained: [Commands](docs/action.md#commands). Where the output goes next: [Outputs](docs/action.md#outputs).

## Inputs and outputs

Every input at a glance; required flags, defaults, which command takes which, and errors are in the
[action reference](docs/action.md#inputs).

- `command` (required): `normalize-docs`, `normalize-tests` or `coverage-matrix`
- `input` (required): the input JSON file
- `output` (required): the JSON file the command writes
- `view`: `inner` or `release`
- `document-title`: the document title, for `normalize-docs`
- `tests-input`: the tests JSON file, which `coverage-matrix` requires
- `fail-under`: the coverage percentage below which `coverage-matrix` fails the step
- `verbose-logging`: debug logging

The one output, `output-path`, is the absolute path of the file the command wrote ([Outputs](docs/action.md#outputs)).

## Where next

| I want to… | Read |
|---|---|
| set every input, chain the commands, read the output, handle an error | [Action reference](docs/action.md) |
| run `living-doc` by hand: options, log and error lines, exit codes | [CLI](apps/cli/README.md) |
| know what `normalize-docs` writes | [normalize-docs](packages/services/normalize_docs/README.md) |
| know how `normalize-tests` groups scenarios | [normalize-tests](packages/services/normalize_tests/README.md) |
| know how `coverage-matrix` counts | [coverage-matrix](packages/services/coverage_matrix/README.md) |
| know the reader table, input validation, view filter, run context and envelope every command shares | [Core](packages/core/README.md) |
| read the contracts, codes and pipeline rules the toolkit implements | [`living-doc-utilities` contracts](https://github.com/AbsaOSS/living-doc-utilities/tree/master/docs/contracts) |
| spec a new command or package | [Specification](SPEC.md) |
| set up the repository, run the gates or a local run | [Developer guide](DEVELOPER.md) |
| contribute a change | [Contributing](CONTRIBUTING.md) |

## Developer Guide

Setup, the gates, the local runs, CI and the documentation rules: [DEVELOPER.md](DEVELOPER.md).

## Contributing

Bug reports, feature requests, branch and pull request conventions, and the AI-free principle:
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

Licensed under the Apache License, Version 2.0; see [LICENSE](LICENSE).

## Contact

Questions, bugs and feature requests: the [GitHub Issues page](https://github.com/AbsaOSS/living-doc-toolkit/issues).
Maintained by [ABSA Group Limited](https://github.com/AbsaOSS).
