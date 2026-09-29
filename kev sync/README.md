# CISA KEV catalog updater

`update_kev.py` is the complete update-and-sync process for CISA's Known
Exploited Vulnerabilities (KEV) catalog. It conditionally downloads the
official JSON catalog, validates its structure and record count, atomically
places the verified file in the collection, and retains download metadata for
efficient conditional checks.

The collection contains:

- `json/known_exploited_vulnerabilities.json` — the verified, directly usable
  official catalog
- `repo/known_exploited_vulnerabilities.meta.json` — saved ETag, Last-Modified,
  SHA-256, release version, and download metadata

The implementation uses only Python's standard library.

Catalogs created by the earlier `repo/` layout are moved into `json/`
automatically on the next update.

## Run it

From this folder on Windows:

```powershell
python .\update_kev.py
```

The default output is a concise human-readable status report.

The default directory is the directory containing the script, so an n8n
Execute Command node can use:

```text
python "W:\NVD\kev sync\update_kev.py" --json --quiet
```

In JSON mode, stdout contains exactly one machine-readable JSON result and
progress goes to stderr. Existing automation that uses `--quiet` without
`--json` remains compatible and continues to receive compact JSON. Exit code
`0` means success, `1` means the catalog update failed, and `2` means another
updater already owns the collection lock.

## Suggested n8n schedule

CISA can add KEVs at any time. An hourly check is inexpensive because the
updater saves CISA's ETag and Last-Modified values and normally receives a `304
Not Modified` response:

```text
python "W:\NVD\kev sync\update_kev.py" --json --quiet
```

Useful maintenance commands:

```powershell
# Show whether the remote catalog would change local state
python .\update_kev.py --dry-run

# Recompute the saved local file's SHA-256 before checking CISA
python .\update_kev.py --deep-verify

# Ignore saved conditional-request metadata and fetch a fresh copy
python .\update_kev.py --force

# Indented JSON for debugging
python .\update_kev.py --pretty
```

The verified catalog remains available if a future download or validation
fails.

Source: [CISA Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
