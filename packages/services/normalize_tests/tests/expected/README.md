# normalize-tests golden

`ui-test-catalog.json` is what `normalize-tests` writes over the repository's
[`ui-tests.json`](../../../../../tests/fixtures/collector-gh/ui-tests.json). The command keeps the fixture's two
feature files in input order: four `FUNC-001` scenarios, then two `US-001` scenarios. None are unlinked.

`test_service.py` masks only `metadata.generated_at` in its comparison. To refresh the golden after an intended
change, run `normalize-tests` over that fixture, compare every other field, and review the output's own stats and
warnings before replacing the file.
