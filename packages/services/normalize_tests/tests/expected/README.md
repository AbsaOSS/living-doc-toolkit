# normalize-tests golden

`ui-test-catalog.json` is what `normalize-tests` writes, in the inner view, over the repository's
[`doc-source.json`](../../../../../tests/fixtures/collector-gh/doc-source.json) and
[`ui-tests.json`](../../../../../tests/fixtures/collector-gh/ui-tests.json). The command keeps the fixture's two
feature files in input order: four `FUNC-001` scenarios, then two `US-001` scenarios. None are unlinked.

- Every link carries its criterion's state: `active`, apart from `US-001-04`, `deprecated`
- No link is to a `planned` or `in_review` criterion, so the release view drops none
- The fixture's scenarios carry no steps, line, rule or background
- The documentation input's two warnings, forwarded

`test_service.py` masks only `metadata.generated_at` in its comparison, and compares the release view with it too,
which differs only in `document.view`. To refresh the golden after an intended change, run `normalize-tests` over
that fixture pair with no `GITHUB_*` variable set, compare every other field, and review the output's own stats and
warnings before replacing the file.
