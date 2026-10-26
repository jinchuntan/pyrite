# Pyrite: ten prepared issue contributions

Prepared 26 October 2026. The code is committed on ten independent branches of jinchuntan/pyrite, based on upstream dev. **No upstream PR has been opened:** the connected GitHub integration rejected the first creation request with HTTP 403, "Resource not accessible by integration". PR creation access is the remaining submission blocker.

| Issue | Change | Review diff | PR description |
|---|---|---|---|
| [#1318](https://github.com/pyrite-wiki/pyrite/issues/1318) | fix(storage): plan non-constant default repairs before DDL | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:fix/schema-repair-defaults?expand=1) | [Body](pr-1318.md) |
| [#1254](https://github.com/pyrite-wiki/pyrite/issues/1254) | fix(types): remove security-merge annotation regressions | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:fix/security-type-annotations?expand=1) | [Body](pr-1254.md) |
| [#1325](https://github.com/pyrite-wiki/pyrite/issues/1325) | fix(export): report every omitted site source and fail partially | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:fix/export-site-load-failures?expand=1) | [Body](pr-1325.md) |
| [#1332](https://github.com/pyrite-wiki/pyrite/issues/1332) | fix(tasks): preserve non-mapping metadata during unrelated edits | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:fix/task-metadata-loading?expand=1) | [Body](pr-1332.md) |
| [#672](https://github.com/pyrite-wiki/pyrite/issues/672) | docs: align test-stage contracts with the CI interpreter matrix | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:docs/test-stage-contracts?expand=1) | [Body](pr-672.md) |
| [#1300](https://github.com/pyrite-wiki/pyrite/issues/1300) | fix(kb): honor configured exclusions across entry file walks | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:fix/kb-file-exclusions?expand=1) | [Body](pr-1300.md) |
| [#1274](https://github.com/pyrite-wiki/pyrite/issues/1274) | fix(links): warn consistently on undeclared relations | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:fix/undeclared-link-relations?expand=1) | [Body](pr-1274.md) |
| [#1171](https://github.com/pyrite-wiki/pyrite/issues/1171) | test(docs): guard component paths and public symbol references | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:docs/component-reference-checks?expand=1) | [Body](pr-1171.md) |
| [#851](https://github.com/pyrite-wiki/pyrite/issues/851) | feat(csv): add opt-in spreadsheet text escaping | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:feature/spreadsheet-safe-csv?expand=1) | [Body](pr-851.md) |
| [#1316](https://github.com/pyrite-wiki/pyrite/issues/1316) | test(storage): reject unclassified non-raising database handlers | [Compare](https://github.com/pyrite-wiki/pyrite/compare/dev...jinchuntan:test/database-handler-classifier-guard?expand=1) | [Body](pr-1316.md) |

## Scope

Seven PRs propose fixes for the issue's current groomed scope. Three are explicitly scoped contributions that leave their issues open: #1171 (component paths/public symbols, with map and exhaustive anchor work remaining), #851 (shared csv-safe implementation plus representative runtime routes; exhaustive emitter runtime fixtures remain), and #1316 (explicit database handler shapes; broad Exception conversion sites remain).

## Validation

- Final combined integration/structural selection: 2,006 passed, 2 skipped, with one export-test inventory classification failure subsequently corrected.
- Final combined export/security-inventory rerun: 362 passed. The export branch alone also passed its complete experimental inventory (355 tests).
- Full Ruff check and format check: 870 Python files clean on the combined tree.
- Exclusion/health/layering compatibility: 80 passed.
- Same-environment mypy comparison for #1254: 609 to 605 errors, zero files rose, three fell; no baseline rewrite.
- Before-fix failures were verified for the new behavior regressions, with controls identified in tests. Individual descriptions carry the focused evidence.
- A broader affected-suite attempt exercised more than 20,000 tests but was not fully green. Ownership and DNS failures were reproduced on unchanged upstream; model/dependency availability affected that environment. Subsequent focused runs repaired integration failures found during development. No full-suite or upstream-CI pass is claimed.

## Submission

For each row, use its Compare link to open a draft PR into pyrite-wiki/pyrite dev and copy its title/body from the corresponding file. Review the CI results before merge. The JSON file records the exact remote commits and trees tested and uploaded. No validation workflow or this submission packet belongs in a product PR.

AI-assisted with Codex; product commits include Co-authored-by trailers.
