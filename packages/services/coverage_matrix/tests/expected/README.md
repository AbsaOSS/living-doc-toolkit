# coverage-matrix golden

`coverage-matrix.json` is what `coverage-matrix` writes, in the inner view, over the repository's
[`doc-source.json`](../../../../../tests/fixtures/collector-gh/doc-source.json) and
[`ui-tests.json`](../../../../../tests/fixtures/collector-gh/ui-tests.json):

- three entities, `US-001`, `FUNC-001` and `FUNC-002`, in that order;
- six counted criteria, four covered and two not covered, 66.7; `FUNC-002` has no counted criterion and no
  percentage;
- two planned criteria, one for `1.1.0` and one in the backlog;
- the documentation input's two warnings, forwarded.

`test_service.py` masks only `metadata.generated_at` in its comparison, and compares the release view with it too,
which differs only in `document.view`. To refresh the golden after an intended change, run `coverage-matrix` over
that fixture pair with no `GITHUB_*` variable set, compare every other field, and review the output's own stats and
warnings before replacing the file.
