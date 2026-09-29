# SBOM KEV Scanner

A polished Python desktop application (Tkinter) that ingests a Software Bill of
Materials (SBOM), lists its components, resolves each component to its known
CVEs, and cross-references those CVEs against the local **CISA Known Exploited
Vulnerabilities (KEV)** catalog.

KEV is treated as its own status category — a component either matches a KEV or
it does not. Alongside it, the app shows a per-component **CVE count** and a
**Critical / High / Medium / Low** severity breakdown derived from the CVSS
data OSV returns (with an **Unknown** bucket for CVEs that carry no severity,
so the counts always reconcile with the CVE total).

## Features

- **Ingests CycloneDX and SPDX** JSON SBOMs, with format auto-detection.
- **Lists every component** with its version.
- **Resolves components to CVEs** using a pluggable resolver model inspired by
  [Dependency-Track](https://dependencytrack.org/):
  - **OSV.dev** (online, matches by Package URL) — the primary source.
  - **KEV name match** (offline heuristic, matches component vendor/product
    names against KEV entries) — an optional, clearly-labeled fallback.
- **Handles Linux distribution packages correctly.** OSV scopes distro
  advisories to a specific OS release, so a bare distro PURL matches nothing.
  For `apk`/`deb`/`rpm` components the scanner targets the release-scoped OSV
  ecosystem instead (`Alpine:v3.24`, `Debian:12`, `Ubuntu:22.04`,
  `Rocky Linux:8`, `AlmaLinux:9`, `Mageia:9`); Red Hat RPMs match directly from
  the PURL. It also extracts the canonical CVE from OSV `upstream`/`related`
  fields (which distro advisories use) so those are not silently dropped.
- **Flags Known Exploited Vulnerabilities** per component, with the matching
  CVE IDs and a ransomware-use indicator.
- **Counts CVEs and classifies severity** per component (Critical / High /
  Medium / Low / Unknown) from OSV's CVSS data, with SBOM-wide totals in the
  summary tiles.
- **Auto-loads the local KEV catalog** on startup and offers a **Refresh KEV**
  button that runs the sibling `kev sync/update_kev.py` updater.
- **Responsive UI**: parsing, scanning, and refreshing run on background
  threads with a progress bar; the window never freezes.

## Requirements

- **Python 3.10+** (developed and tested on 3.13).
- **No third-party packages.** Only the standard library is used
  (`tkinter`, `urllib`, `json`, `subprocess`, `threading`).
- Internet access is required only when the **OSV.dev** source is enabled and
  when using **Refresh KEV**.

## Project layout

```
SBOM/
├─ sbom_kev/                 # the application package
│  ├─ app.py                 # Tkinter GUI (thin view)
│  ├─ models.py              # Component, ScanResult, KevStatus
│  ├─ sbom_parser.py         # CycloneDX/SPDX parsing + auto-detect
│  ├─ kev_catalog.py         # loads & indexes the KEV catalog
│  ├─ resolvers.py           # CveResolver protocol, stub, name-match fallback
│  ├─ osv_resolver.py        # OSV.dev online resolver
│  ├─ scanner.py             # orchestration + KEV matching
│  ├─ refresh.py             # runs update_kev.py and interprets the result
│  ├─ viewmodel.py           # headless presentation logic (rows, tiles)
│  └─ theme.py               # colors, fonts, ttk styling
├─ kev sync/                 # existing CISA KEV catalog updater
│  ├─ update_kev.py
│  └─ json/known_exploited_vulnerabilities.json
├─ tests/                    # unit tests (offline) + fixtures
└─ requirements.txt
```

## Installing (pip)

The project builds a standard Python wheel. Install it into any Python 3.10+
environment:

```powershell
pip install sbom_kev_scanner-1.0.0-py3-none-any.whl
```

This installs a **`sbom-kev`** command that launches the GUI, and bundles a
snapshot of the CISA KEV catalog so the app works immediately offline. Use
**Refresh KEV** in the app to update the catalog; the refreshed copy is stored
per-user (e.g. `%LOCALAPPDATA%\sbom-kev` on Windows) and takes precedence over
the bundled snapshot.

```powershell
sbom-kev
```

## Running from source

**Windows:** double-click **`SBOM KEV Scanner.bat`** in the project root.

**Any platform**, from the project root:

```powershell
python run.py
```

(All of `sbom-kev`, `python run.py`, and `python -m sbom_kev` are equivalent;
`run.py` adds a friendly check for Python version and Tkinter availability.)

## Building the distributable

From the project root:

```powershell
python -m pip install build
python -m build
```

This produces `dist/sbom_kev_scanner-1.0.0-py3-none-any.whl` (wheel) and
`dist/sbom_kev_scanner-1.0.0.tar.gz` (sdist). The wheel bundles the KEV catalog
snapshot and the updater under `sbom_kev/data/`, so it is self-contained.

Then:

1. The status bar shows the loaded KEV catalog version and record count.
2. Click **Open SBOM** and choose a CycloneDX or SPDX JSON file. The component
   inventory populates immediately.
3. Choose your CVE source(s): **OSV.dev** (default on) and/or **KEV name
   match**.
4. Click **Scan**. Each component is resolved to CVEs and checked against the
   KEV catalog. The table fills in a KEV status and the matching CVE IDs;
   KEV-affected rows are highlighted.
5. Use **Refresh KEV** at any time to pull the latest CISA catalog.
6. After a scan, click **Export evidence** to write an audit report (see below).

## Evidence report (for audits / JIRA)

After a scan, **Export evidence** writes two files you can attach to a ticket:

- a human-readable **Markdown** report (`kev-evidence_<sbom>_<timestamp>.md`), and
- a machine-verifiable **JSON** record with the same data.

The report is designed to substantiate a statement like *"we scanned SBOM X on
date Y and found no Known Exploited Vulnerabilities."* It captures, and
cross-links by SHA-256:

- the exact SBOM file scanned (name, **SHA-256**, format, component count),
- the **UTC scan timestamp** and tool version,
- the **CISA KEV catalog** version, release date, record count, and **SHA-256**,
- the CVE source (OSV) and that matching is **version-aware**,
- the KEV result, and a **full component inventory** with each component's
  check status and CVE count, plus an appendix listing any component that could
  not be checked (no PURL) — so a "no KEV" result is never overstated.

An auditor can re-verify by confirming the two SHA-256 values and re-running the
scan.

## KEV status meanings

A KEV designation belongs to a specific **CVE**, and applicability requires the
component's installed **version** to fall in that CVE's affected range. The
scanner therefore separates version-confirmed matches from name-only ones:

| Status | Meaning |
| --- | --- |
| **KEV Listed** | A version-aware source (OSV) confirmed a CVE affects this exact version, and that CVE is in the CISA KEV catalog. A substantiated finding. |
| **Possible KEV (version unverified)** | The component's product name matches a CISA KEV entry, but its installed version was not confirmed to be in the affected range. A lead to investigate — not a confirmed finding. Produced only by the optional KEV name-match resolver. |
| **Not in KEV** | CVEs were resolved (version-aware) and none are in the KEV catalog. |
| **No CVE data** | No CVEs could be resolved (source disabled/offline, or the component has no PURL to match on). |

> Why this distinction matters: a CVE being in the KEV catalog does **not** mean
> every version of the product is affected. For example, several Apache Tomcat
> CVEs are in the KEV catalog, but their affected-version ranges exclude current
> releases — so a current Tomcat is *not* KEV-affected even though "Tomcat"
> appears in the catalog. The name-match resolver can only see the product name,
> so its hits are always reported as **Possible KEV**, never confirmed.

## Severity classification

Each resolved CVE is classified into **Critical / High / Medium / Low** using
the CVSS data OSV returns:

1. If a CVSS v3.x vector or numeric base score is present, it is bucketed by
   the standard ranges (Critical 9.0–10.0, High 7.0–8.9, Medium 4.0–6.9,
   Low 0.1–3.9).
2. Otherwise the advisory's qualitative rating (e.g. GitHub's "high" /
   "moderate") is used.
3. If neither is available, the CVE is counted as **Unknown** severity.

The CISA KEV catalog itself carries no CVSS severity, so KEV status remains a
separate, independent category. The per-component `Severity` column is a
compact `C:_ H:_ M:_ L:_ U:_` summary (zeros omitted); the summary tiles show
the SBOM-wide totals. Because unknown-severity CVEs get their own bucket, the
severity counts always add up to the CVE count.

> Note: CVSS v2 and v4 vectors are not scored numerically; those fall back to
> the advisory's qualitative rating when present, otherwise Unknown.

## Testing

The entire core is network-free and unit-tested. Run the suite from the project
root:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

An optional live OSV test is skipped by default. To exercise the real API:

```powershell
$env:SBOM_KEV_LIVE_OSV = "1"; python -m unittest tests.test_osv_resolver; Remove-Item Env:\SBOM_KEV_LIVE_OSV
```

A manual GUI smoke check (requires a display) constructs the window, loads a
sample SBOM, and runs an offline scan:

```powershell
python tests/_smoke_gui.py
```

## Data sources & attribution

- **CISA Known Exploited Vulnerabilities Catalog** —
  https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- **OSV.dev** — https://osv.dev (this product uses the OSV API but is not
  endorsed or certified by OSV).
- Component-to-CVE resolution design is informed by the analyzer model used in
  [Dependency-Track](https://github.com/DependencyTrack/dependency-track).
