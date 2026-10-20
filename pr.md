<!-- What problem does it solve or what feature does it add? -->
## Overview

The toolkit now runs as a GitHub Action. A root composite `action.yml` runs one command per step, in a venv of its own built from the Python on `PATH`, as `living-doc-collector-gh` and `living-doc-generator-markdown` already do.

The same change does three more things:
- fixes the root `requirements.txt`, which is what the action installs;
- gives `test.yml` the other repos' CI shape;
- fixes release notes, which neither the draft nor the presence check could read from a PR body.

**The action**
- **Inputs:** `command` (`normalize-issues`, `normalize-tests`, `coverage-matrix`), `input` and `output`. `view` and `document-title` are taken by `normalize-issues` only. `tests-input` and `fail-under` are taken by `coverage-matrix` only. `verbose-logging` defaults to `'false'`.
- **Output:** `output-path`, the absolute path of the file the command wrote.
- **Venv step:** `living-doc-generator-markdown`'s at `012e31a`, with two changes. The install and the import check run from `$GITHUB_ACTION_PATH`, because pip reads `./packages/...` against the directory it runs in. The variable, not `${{ github.action_path }}`: in a `container:` job the expression gives the runner host's path. The import check imports `living_doc_cli.main`, which pulls in the other five packages.
- **`main.py`, the run step's entry point:**
  - checks the inputs, then runs `python -I -m living_doc_cli.main <command> --<option>=<value> …` on the venv's interpreter. `-I` is stricter than the issue's `-E`: it also keeps the caller's working directory off `sys.path`, so a `click.py` or `json.py` in the caller's checkout cannot shadow the venv's module;
  - passes the CLI's exit code through, and sets `output-path` once the command succeeds;
  - fails with one line on any of these: an unknown `command`, `normalize-tests` (not available yet), a non-empty input the command does not take, an empty required input, or a `fail-under` that is not a number;
  - for `verbose-logging: 'true'`, adds `--verbose` and logs the command line at DEBUG. The CLI reads no environment variable, but `INPUT_VERBOSE_LOGGING` stays in the run step's `env:`.
- **Inputs reach the run step only through its `env:`.** No `run:` script holds `${{ inputs.* }}`.
- **Open question, decided on #81:** option 1, the named inputs `tests-input` and `fail-under`, taken by `coverage-matrix` only. Links: [question](https://github.com/AbsaOSS/living-doc-toolkit/issues/81#issuecomment-6297160564), [answer](https://github.com/AbsaOSS/living-doc-toolkit/issues/81#issuecomment-6298050161).

**Package list**
- **`requirements.txt`** lists the six package directories in dependency order, `./packages/core` to `./apps/cli`, `services/coverage_matrix` included. It has no `-e` and no tool, so `pip install -r requirements.txt` from the root now works.
- **`requirements-dev.txt`** opens with `-r requirements.txt` and pins the gate and test tools, plus `PyYAML`.
- **`make install`** installs `requirements-dev.txt`, then reinstalls the six packages editable with `[dev]`.
- **No guard on `requirements.txt`.** The issue's package-list test and `generator-markdown`'s `tools/check_runtime_requirements.py` are left out as overengineering. `DEVELOPER.md` states the rule instead: a new package goes into `requirements.txt`, a development tool into `requirements-dev.txt`.
- **`make qa`** now runs `qa-root` after the packages: Black and ruff over `main.py` and `tests/`; Pylint and mypy over `main.py`, as the packages leave out their tests; pytest over `tests/`.
- **Dependabot** gets a `pip` entry on `/`.
- **mypy:** each package's `exclude` gains `build/`. A plain install builds each package in place, beside its `src/`, and `mypy .` would then find every module twice.

**CI**
- **`test.yml`** follows `generator-markdown`'s shape:
  - static checks once, on 3.10;
  - tests with the coverage gate, on 3.10–3.14;
  - a `QA Gate` that always runs and fails on a failed or cancelled job.

  `detect` now sets `python_changed=true` on a manual run, and counts `Makefile`, `action.yml`, `tests/fixtures/`, a JSON file under `packages/` (the services' schemas) and a renamed file's old path.
- **`integration.yml`** uses `make install`. It adds a job that runs both commands over the committed fixtures, plus the three venv jobs. That job checks the repository out under `toolkit/`, runs it as `uses: ./toolkit` and puts a `click.py` in the workspace, so it fails without the `cd` into the action's directory or without the CLI's `-I`; with `uses: ./` both would pass unnoticed.

**Release notes and links**
- **`release_draft.yml`** passes `release-notes-title: '## [Rr]elease [Nn]otes'`. The default needs a colon that no heading has.
- **`check_pr_release_notes.yml`** matches `## [Rr]elease [Nn]otes`, so it stops at the heading, not at the template's comment line above it.
- **`link-check.yml`** sets `docs_changed=true` on a manual run, so a manual run checks every page.

**Docs**
- **`README.md`** gets § GitHub Action: a usage step, the inputs, the output, and the requirements (Python 3.10 or later on `PATH`, a Linux runner).
- **`DEVELOPER.md`** gets § Action venv and § CI. Its install section now explains `requirements.txt` and `requirements-dev.txt`.
- **`docs/troubleshooting.md`**: "How do I update the toolkit?" no longer suggests `pip install --upgrade living-doc-toolkit`, because the toolkit is not on PyPI. Its reinstall line left out `coverage_matrix` and is now `pip install -r requirements.txt`.
- **`docs/recipes/github-actions-normalize-issues.md`** and its `.yml` now run the toolkit through the action. Before, they ran `pip install -r requirements.txt` in the caller's own repository, where no such file exists. The `--document-version` examples are gone, because the action does not pass that option.
- **`.github/copilot-instructions.md`** and **`devops-engineer.agent.md`** no longer say the root `requirements.txt` is missing or editable-only.

<!-- Summarize the key changes for release notes. -->
## Release Notes
- The toolkit runs as a GitHub Action: `uses: AbsaOSS/living-doc-toolkit@<ref>` with `command`, `input` and `output`, in a venv of its own built from the Python on `PATH` (3.10 or later). `coverage-matrix` takes `tests-input` and `fail-under`; `normalize-issues` takes `view` and `document-title`. The `output-path` output is the absolute path of the file written.
- `pip install -r requirements.txt` installs every package, `coverage-matrix` included.
- An input the chosen command does not take, an unknown `command`, or `normalize-tests` fails the step with one line.

## Framework

- [x] Stays inside the frame. This is packaging and CI only. The action runs the existing `normalize-issues` and `coverage-matrix` commands, which is the Toolkit row's own work. It renders nothing and calls no source system, and no transform, schema or CLI option changes.

<!-- Add attached issue that this PR solves. -->
## Related
Closes #81

### `test.yml` job names

| Before | After |
|---|---|
| `Detect Python Changes` (`detect`) | `Detect Python Changes` (`detect`) |
| `QA (Black, Pylint, mypy, Pytest) — Python 3.10` … `— Python 3.14` (`qa`) | `Black Format Check (Python 3.10)`, `Ruff and Pylint Analysis (Python 3.10)`, `Mypy Type Check (Python 3.10)` (`static-checks`) |
| | `Python Tests (Python 3.10)` … `(Python 3.14)` (`tests`) |
| `No Python Changes` (`noop`) | `QA Gate` (`qa-gate`) |

The ruleset requires `check-release-notes` only, so no rename touches a required check. `QA Gate` and every `integration.yml` job are the checks to mark as required: `integration.yml` runs on every pull request, and its action jobs are the only ones that run the action itself.

`integration.yml`: `Run Integration Tests` stays, now on `make install`. New jobs: `Action - Commands Over the Fixtures`, `Action Venv - Isolation and Reuse`, `Action Venv - Rebuilt When Python Changes` and `Action Venv - Python 3.9 Is Rejected`.

### `make qa`

Green on macOS with Python 3.10.18, after `make install` into a fresh venv:

| Part | Pylint | mypy | Tests | Coverage |
|---|---|---|---|---|
| `core` | 10.00 | clean | 47 passed | 94.39% |
| `datasets-generator-ready` | 10.00 | clean | 44 passed | 100.00% |
| `collector-gh` | 9.95 | clean | 61 passed | 86.70% |
| `normalize` | 9.96 | clean | 43 passed | 94.34% |
| `coverage` | 9.86 | clean | 40 passed | 98.35% |
| `cli` | 9.84 | clean | 30 passed | 98.81% |
| root (`main.py`, `tests/`) | 10.00 | clean | 44 passed | 98.84% |

- Black is clean in every part, and so is ruff.
- On Python 3.14.7, `make install`, `make coverage` and `make integration` pass.
- `actionlint` 1.7.12 passes on the five changed workflows, including each `uses: ./` and `uses: ./toolkit` step's inputs against `action.yml`.

The action's two steps were also run locally against real interpreters, outside GitHub:
- `normalize-issues` and then `coverage-matrix` on 3.12 wrote their files and set `output-path`. The venv was reused: `pyvenv.cfg`'s mtime was unchanged.
- A `view` passed to `coverage-matrix` failed with one line.
- Python 3.9 on `PATH` failed with the one-line error and created no venv.
- As `Action - Commands Over the Fixtures` runs them, the toolkit under `toolkit/` and a `click.py` in the working directory: both commands wrote their files and set `output-path`. The CLI run without `-I` stopped on the workspace's `click.py`, and the install without the `cd` failed on a missing `requirements.txt`.

The `integration.yml` jobs themselves run on this PR.

### Acceptance criteria

| # | Criterion | Where |
|---|---|---|
| 1 | `uses: ./` runs `normalize-issues` and `coverage-matrix` over committed fixtures, sets the output, uploads the artifacts | `.github/workflows/integration.yml:56-115`: the same local-action form, `uses: ./toolkit` (`:77`, `:88`), from a checkout under `toolkit/` (`:64`), with a `click.py` in the workspace (`:72-73`); assertions `:96-107`; `upload-artifact` `:109-115`. `Action Venv - Isolation and Reuse` runs both commands as `uses: ./` (`:143`, `:154`). |
| 2 | Python from `PATH`, one-line error below 3.10 or without `venv`; only `requirements.txt` into `$RUNNER_TEMP`; reuse only for the same interpreter; six pip variables cleared; import check; `-E`; caller unchanged | `action.yml:50`, `:52-54`, `:55-65`, `:66-69`, `:84` (`main.py` with `-E`); `main.py:188` (the CLI with `-I`, which includes `-E`); `tests/test_action_yml.py:111-199`; `integration.yml:117` (isolation and reuse), `:201` (rebuild), `:255` (3.9) |
| 3 | An unknown `command` lists the valid ones; `normalize-tests` is not available yet; an input the command does not take is named | `main.py:78-97`, `:127-129`; `tests/test_main.py:69`, `:81`, `:97`, `:122`, `:135` |
| 4 | `verbose-logging: 'true'` gives DEBUG output | `main.py:177-178`, `:152-153`, `:190`; `tests/test_main.py:281`, `:297`. The `'false'` default is `action.yml:32`, which no test reads; an empty value is off (`tests/test_main.py:297`). |
| 5 | Inputs reach the run step only through `env:` | `action.yml:74-82`; the two `run:` scripts, `:49-70` and `:84`, hold no `${{ inputs.* }}` |
| 6 | `requirements.txt` lists all six, with no `-e` and no tool; the package-list test fails on a planted package; `make runtime-requirements` accepts an in-repo package and rejects tools and other non-pins; both run in `make qa` | **Partly met.** `requirements.txt:3-8` lists all six packages, with no `-e` and no tool. The package-list test and the `make runtime-requirements` guard are not in this PR: they were dropped as overengineering. `DEVELOPER.md:71-75` states the rule they enforced. |
| 7 | `requirements-dev.txt` opens with `-r requirements.txt`; `make install` is editable; Dependabot covers both files | `requirements-dev.txt:3`; `Makefile:78-87`; `.github/dependabot.yml:22-42` |
| 8 | `test.yml`: tests on 3.10–3.14, static checks once on 3.10, `qa-gate` fails on a failed or cancelled job | `.github/workflows/test.yml:73-109`, `:111-141`, `:143-153` |
| 9 | A manual `link-check.yml` run checks every page | `.github/workflows/link-check.yml:54-57` |
| 10 | `release_draft.yml` passes `release-notes-title` | `.github/workflows/release_draft.yml:67` |
| 11 | `check_pr_release_notes.yml` matches `## [Rr]elease [Nn]otes`; this body keeps the comment line | `.github/workflows/check_pr_release_notes.yml:40`; this body's `## Release Notes` |
| 12 | `README.md` documents the action; `DEVELOPER.md` states the venv rules once; no page says `requirements.txt` is missing or editable-only | `README.md:74-137`; `DEVELOPER.md:334` (§ Action venv), `:410` (§ CI), `:37-77` (§ Install); `docs/troubleshooting.md:558-572`; `docs/recipes/github-actions-normalize-issues.md` and `.yml`; `.github/copilot-instructions.md:137`; `.github/agents/devops-engineer.agent.md:98` |
| 13 | The open question was decided on the issue before the input mapping was coded | **Not met as written; accepted on #81** ([comment](https://github.com/AbsaOSS/living-doc-toolkit/issues/81#issuecomment-6299027246)). The [question](https://github.com/AbsaOSS/living-doc-toolkit/issues/81#issuecomment-6297160564) was posted at 17:37Z. The input mapping (`main.py:48-53`) was committed in `957ce48` at 18:17Z, before the [answer](https://github.com/AbsaOSS/living-doc-toolkit/issues/81#issuecomment-6298050161) (option 1) was recorded at 18:22Z. The mapping matches the decision. |
| 14 | `make qa` green | see `make qa` above |
| 15 | No planning id in the diff or this body | `git diff master \| grep '^+' \| grep -E …` prints nothing |
| 16 | `## Framework` | above |