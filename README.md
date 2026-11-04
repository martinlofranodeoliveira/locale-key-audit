# locale-key-audit

Find missing and unexpected translation keys in nested JSON catalogs without
printing translations. This MIT Python library and CLI support a local release
check for small multilingual apps. Python 3.11+, no runtime dependencies,
telemetry, browser, translation provider or network.

## Use

`PYTHONPATH=src python3 -m locale_key_audit < catalogs.json` from the checkout.
Or install with `python3 -m pip install .` and run `locale-key-audit catalogs.json`.
Supply one regular UTF-8 JSON file or `-` (default stdin). Symlinks, directories
and FIFOs are refused. The CLI accepts at most 1 MiB and rejects duplicate JSON
object keys and nonfinite numbers. No input files are changed. Exit code 0 means
equal leaf-key coverage, 1 means differences, 2 means invalid input/arguments.
Errors are fixed codes, with no translation text or input filenames.

```json
{"reference":{"nav":{"home":"Home","help":"Help"}},"locales":{"pt-BR":{"nav":{"home":"Início"}}}}
```

Result:
```json
{"valid":false,"reference_keys":2,"locales":[{"locale":"pt-BR","missing":["/nav/help"],"extra":[],"matched":1}]}
```

## Exact API contract

`from locale_key_audit import analyze; report = analyze(payload)`.
The pure `analyze` function accepts only a built-in dict with exactly `reference`
and `locales`. `reference` is a built-in dict. `locales` is a built-in dict with
0..20 entries, each mapping a unique ASCII tag matching
`[A-Za-z][A-Za-z0-9-]{0,34}` to a built-in catalog dict. Catalog trees contain
only built-in dicts and built-in string leaves. Empty dicts are allowed and
contribute zero leaf keys. Arrays, null, booleans, numbers and other types are
invalid. String values may be empty and have at most 2000 Unicode code points;
LF, CR and TAB are allowed, other C0 controls and unpaired surrogates are not.
Keys contain 1..80 Unicode code points, with no C0 controls or surrogates. Slash,
tilde and literal dots in keys are allowed. All catalogs must be validated before
returning any result. A catalog root has depth 0; dicts or string leaves may be
at depth 12 at most. Count root and every dict or leaf as one node; each catalog
is limited to 10,000 nodes. Cyclic or over-depth inputs are invalid.

Invalid inputs raise `ValueError("INPUT_INVALID")`, never a partial report or a
message containing translation values. Preserve input; never normalize, modify,
translate or trim strings and keys. No I/O, environment, imports with operational
effects, callbacks or dependencies in the engine.

Flatten only string leaves as JSON Pointer paths: escape `~` to `~0` and `/` to
`~1` in each key, join segments with `/`, with a leading `/`. Thus literal
`"a.b"` differs from `{"a":{"b":...}}`. This is path notation only, not JSON
Pointer evaluation. For each locale compute missing reference paths, extra
locale paths and the count of shared paths. Values themselves do not affect key
coverage. Sort locale tags and each missing/extra list by Python string order.
Return exactly `{"valid":bool,"reference_keys":int,"locales":[{"locale":str,"missing":[str],"extra":[str],"matched":int}]}`.
`valid` is true if every locale has no missing and no extra paths, including no
locales. An empty reference is valid. A dict/string conflict naturally produces
leaf-path differences. Reports include tags and key paths, never translations.

This tool checks key presence only. It does not assess grammar, translation
quality, ICU message syntax, placeholders, plural rules or rendering, and is not
a translation service. Use synthetic catalogs when filing public issues.

## Development

`python3 scripts/checks-offline.py` runs read-only source and tests in a Linux
Bubblewrap namespace with no network, home, credentials or effective capabilities,
and compares hashes afterwards. CI root bootstrap is only for a disposable
GitHub-hosted runner; local tests run without sudo. Independent controller
acceptance is frozen separately from model-authored public tests.

AI-assisted implementation, validated with public and independent tests. MIT;
copyright 2026 Martin Lofrano. Contributions with reproducible examples welcome.
