# utilities-golden fixtures

Copied byte-for-byte from [`AbsaOSS/living-doc-utilities`](https://github.com/AbsaOSS/living-doc-utilities) at tag
`v0.8.0`, commit
[`1901382`](https://github.com/AbsaOSS/living-doc-utilities/tree/1901382/tests/fixtures/golden/expected), from
`tests/fixtures/golden/expected/`:

| File | Entity |
|---|---|
| `us-001-customer-login.json` | `US-001` |
| `feat-001-login-page.json` | `FEAT-001` |
| `feat-002-breached-password-check.json` | `FEAT-002` |
| `feat-003-registration-page.json` | `FEAT-003` |
| `func-001-validate-password-strength.json` | `FUNC-001` |
| `func-002-reject-breached-password.json` | `FUNC-002` |

- Each is one entity as `living-doc-utilities`' parsers author it from its canonical source, without `source_ref`,
  which a collector fills.
- `packages/services/normalize_docs`' tests build a `doc-source.json` from all six, with a `source_ref` added to each,
  and compare every authored field of the `generator-ready.json` that `normalize-docs` writes with these files.
- To refresh them, copy the six files again from one `living-doc-utilities` tag, at the version the packages pin, and
  update the tag and commit above.
