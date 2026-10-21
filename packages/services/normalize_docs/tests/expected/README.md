# normalize-docs goldens

What `normalize-docs` writes over the repository's fixture, [`tests/fixtures/collector-gh/doc-source.json`](../../../../../tests/fixtures/collector-gh/doc-source.json):

| File | Options |
|---|---|
| `generator-ready-inner.json` | none: the `inner` view, the project id as the title, version `1.0.0` |
| `generator-ready-release.json` | `--view release` |

- `metadata.generated_at` is the fixture's own, `2026-10-21T06:47:26Z`; `test_service.py` masks it in the comparison.
- To refresh them after an intended change, run the command over the fixture in each view, set `generated_at` back,
  and review the diff: every other field is the command's output.
