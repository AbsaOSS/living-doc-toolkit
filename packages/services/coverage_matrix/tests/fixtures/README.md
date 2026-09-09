# coverage-matrix test fixtures

| Path | What it is | How it is made |
|---|---|---|
| `corpus/` | A small `.feature` corpus (`us/*.feature`) — the mining input. | Hand-authored, committed. |
| `golden/doc_source.json`, `golden/ui_tests.json` | **Real** `living-doc-collector-gh` output for `corpus/`. | Generated — see below. |
| `golden/expected_coverage_matrix.json` | Expected `coverage-matrix.json` for the golden inputs. | Generated — see below. |
| `synthetic/` | Hand-authored inputs for shapes the corpus can't produce (empty inputs, a cross-source `US-1` id collision, an unmatched AC). | Hand-authored, committed. |

The golden inputs are the collector's actual mined JSON, not hand-written, so a
schema/parser change in `collector-gh` that alters the mined output shows up here as a
failing `test_golden_files.py`.

## Refreshing the golden fixtures

Two steps, both manual (the pin-and-vendor automation is roadmap Phase 5):

```bash
# 1. Re-mine the corpus with collector-gh's doc-source + ui-tests modes.
#    Needs collector-gh checked out next to this repo, or LIVING_DOC_COLLECTOR_GH set.
python packages/services/coverage_matrix/tests/fixtures/generate_golden_inputs.py

# 2. Regenerate the expected coverage matrix from the refreshed inputs.
python packages/services/coverage_matrix/tests/fixtures/golden/regenerate_expected.py

# 3. Review the diff and re-run the gate.
make qa-coverage
```

`generate_golden_inputs.py` records the exact `collector-gh` commit it was last run
against; bump that comment when you re-run it against a newer collector.
