# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Regenerate the coverage-matrix golden *input* fixtures from real collector output.

This is a developer tool, not a test. It runs ``living-doc-collector-gh``'s ``doc-source``
and ``ui-tests`` modes over the committed ``.feature`` corpus in
``tests/fixtures/corpus/`` and writes the mined JSON to
``tests/fixtures/golden/doc_source.json`` / ``ui_tests.json``.

The only post-processing is determinism normalisation: the dynamic
``metadata.original_metadata.generated_at`` timestamp and any GitHub-Actions
environment fields are pinned to fixed values, and the source-file URL is reduced to a
repo-relative form so the fixture does not bake in a local checkout path.

Usage::

    # collector-gh checked out next to this repo (../living-doc-collector-gh), or:
    export LIVING_DOC_COLLECTOR_GH=/path/to/living-doc-collector-gh
    python packages/services/coverage_matrix/tests/fixtures/generate_golden_inputs.py

After running it, regenerate the expected output with
``tests/fixtures/golden/regenerate_expected.py`` and re-run ``make qa-coverage``.

Pinned collector-gh commit: b6c935d3541b6580b2ed356b458c1427d9a3659e (2026-09-08).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

FIXTURES_DIR = Path(__file__).resolve().parent
CORPUS_DIR = FIXTURES_DIR / "corpus"
GOLDEN_DIR = FIXTURES_DIR / "golden"

ORG = "absa-group"
REPO = "aul-ui"
PINNED_GENERATED_AT = "2026-01-01T00:00:00+00:00"


def _find_collector_gh() -> Path:
    """Locate the living-doc-collector-gh checkout."""
    env = os.environ.get("LIVING_DOC_COLLECTOR_GH")
    candidates = [Path(env)] if env else []
    candidates.append(FIXTURES_DIR.parents[5] / "living-doc-collector-gh")
    for candidate in candidates:
        if (candidate / "doc_source" / "collector.py").is_file():
            return candidate
    raise SystemExit(
        "Could not find living-doc-collector-gh. Check it out next to this repo or set "
        "LIVING_DOC_COLLECTOR_GH to its path."
    )


def _pin_metadata(metadata: dict) -> dict:
    """Pin the dynamic / environment-derived metadata fields to fixed values."""
    metadata["producer"]["build"] = None
    metadata["run"] = {key: None for key in ("run_id", "run_attempt", "actor", "workflow", "ref", "sha")}
    original = metadata.get("original_metadata") or {}
    original["generated_at"] = PINNED_GENERATED_AT
    metadata["original_metadata"] = original
    return metadata


def _clean_url(url: str | None) -> str | None:
    """Reduce the collector's git-blob URL to a repo-relative form (drops the local path)."""
    if not url:
        return url
    marker = "/corpus/us/"
    if marker in url:
        return f"https://github.com/{ORG}/{REPO}/blob/main/" + url.split(marker, 1)[1]
    return url


def main() -> None:
    collector_root = _find_collector_gh()
    sys.path.insert(0, str(collector_root))

    from doc_source.collector import GHDocSourceCollector  # pylint: disable=import-outside-toplevel
    from ui_tests.collector import GHUITestsCollector  # pylint: disable=import-outside-toplevel

    us_dir = str(CORPUS_DIR / "us")
    doc_repos = [{"organization-name": ORG, "repository-name": REPO, "us-paths": [us_dir]}]
    ui_repos = [{"organization-name": ORG, "repository-name": REPO, "paths": [us_dir]}]

    with tempfile.TemporaryDirectory() as tmp:
        with mock.patch("doc_source.collector.ActionInputs.get_doc_source_repositories", return_value=doc_repos):
            assert GHDocSourceCollector(tmp).collect(), "doc-source collection failed"
            doc_source = json.loads((Path(tmp) / "doc-source" / "doc-source.json").read_text(encoding="utf-8"))

        with mock.patch("ui_tests.collector.ActionInputs.get_ui_tests_repositories", return_value=ui_repos):
            assert GHUITestsCollector(tmp).collect(), "ui-tests collection failed"
            ui_tests = json.loads((Path(tmp) / "ui-tests" / "ui-tests.json").read_text(encoding="utf-8"))

    doc_source["metadata"] = _pin_metadata(doc_source["metadata"])
    for story in doc_source.get("user_stories", []):
        story["url"] = _clean_url(story.get("url"))
    ui_tests["metadata"] = _pin_metadata(ui_tests["metadata"])

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    (GOLDEN_DIR / "doc_source.json").write_text(
        json.dumps(doc_source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (GOLDEN_DIR / "ui_tests.json").write_text(
        json.dumps(ui_tests, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {GOLDEN_DIR / 'doc_source.json'}")
    print(f"Wrote {GOLDEN_DIR / 'ui_tests.json'}")


if __name__ == "__main__":
    main()
