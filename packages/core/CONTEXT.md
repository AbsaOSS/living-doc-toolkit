# living-doc-core

Parent: `../../CONTEXT.md`

What every command shares. Its behaviour is [README.md](README.md); this file maps that page to the code.

## Code map

What realises each fact of [README.md](README.md):

- Depends on `living-doc-utilities==0.8.0` only → `packages/core/pyproject.toml::living-doc-utilities`
- The package exports `setup_logging` and `__version__` only → `packages/core/src/living_doc_core/__init__.py::__all__`
- `[LEVEL] message` on stderr → `packages/core/src/living_doc_core/logging_config.py::setup_logging`
- The reader table → `packages/core/src/living_doc_core/readers.py::READERS`
- Keyed by contract name, never by producer → `packages/core/src/living_doc_core/readers.py::contract_names`
- Every read through `read_artifact`, returning a contract model → `packages/core/src/living_doc_core/readers.py::read_documentation`, `packages/core/src/living_doc_core/readers.py::read_tests`
- The roles each command takes → `packages/core/src/living_doc_core/input_validation.py::COMMAND_ROLES`
- The six validation steps, in order → `packages/core/src/living_doc_core/input_validation.py::validate_inputs`
- The first failing step ends validation, with every occurrence → `packages/core/src/living_doc_core/input_validation.py::InputValidationError`
- An `InputProblem`'s line → `packages/core/src/living_doc_core/input_validation.py::InputProblem.__str__`
- `ValidatedInputs`, `None` for a role not taken → `packages/core/src/living_doc_core/input_validation.py::ValidatedInputs`
- `metadata.producer.version` is never compared → `packages/core/src/living_doc_core/input_validation.py::_unknown_producers`
- An unknown command or role, or a second tests path, is a `ValueError` → `packages/core/src/living_doc_core/input_validation.py::_roles`
- The view filter → `packages/core/src/living_doc_core/views.py::select_records`
- What `release` drops → `packages/core/src/living_doc_core/views.py::RELEASE_DROPS`
- A kept entity is the input's own, or a copy without its dropped criteria → `packages/core/src/living_doc_core/views.py::_with_criteria`
- `metadata.run` from the `GITHUB_*` variables → `packages/core/src/living_doc_core/run_context.py::RUN_VARIABLES`
- An unset or empty variable is `None` → `packages/core/src/living_doc_core/run_context.py::run_context`
- The producer's name and version → `packages/core/src/living_doc_core/envelope.py::PRODUCER_NAME`, `packages/core/src/living_doc_core/envelope.py::TOOLKIT_VERSION`
- A forwarded warning's context → `packages/core/src/living_doc_core/envelope.py::forwarded`
- `metadata.stats`, `producer.utilities_version` and the four source counts at `0` → utilities
