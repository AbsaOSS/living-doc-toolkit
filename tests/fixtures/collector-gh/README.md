# collector-gh fixtures

Copied from [`AbsaOSS/living-doc`](https://github.com/AbsaOSS/living-doc) at commit
[`972dba3`](https://github.com/AbsaOSS/living-doc/tree/972dba3/docs/examples/_expected/collector-gh), with one
change each:

| File | Source path in `living-doc` |
|---|---|
| `doc-source.json` | `docs/examples/_expected/collector-gh/doc-source/doc-source.json` |
| `ui-tests.json` | `docs/examples/_expected/collector-gh/ui-tests/ui-tests.json` |

- The one change: `metadata.generated_at` is `2026-10-21T06:47:26Z`, the commit time of `972dba3`. Everything else
  is byte-for-byte, the `<normalized-for-snapshot>` commit in each `source_ref.url` included.
  - Why: `living-doc`'s snapshot sets `generated_at` to the string `<normalized-for-snapshot>`, which the contract
    model rejects, so `read_artifact` would fail both files with `SCHEMA_VALIDATION_FAILED`.
- Both were written by `AbsaOSS/living-doc-collector-gh` `0.1.1` on `living-doc-utilities` `0.7.0`, for the
  project `living-doc-examples`.
- `packages/core`'s tests and the `integration.yml` jobs read this one copy.
- To refresh them, copy both files again from one `living-doc` commit, set `metadata.generated_at` to that commit's
  time, and update the commit above.
