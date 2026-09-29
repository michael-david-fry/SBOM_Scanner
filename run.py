#!/usr/bin/env python3
"""Launch the SBOM KEV Scanner GUI.

Run this from the project root:

    python run.py

It is a thin wrapper around ``python -m sbom_kev`` that also gives a clear
error if it is run with a Python that is too old or missing Tkinter.
"""

from __future__ import annotations

import sys


def main() -> int:
    if sys.version_info < (3, 10):
        sys.stderr.write(
            "SBOM KEV Scanner requires Python 3.10 or newer. "
            f"You are running {sys.version.split()[0]}.\n"
        )
        return 1

    try:
        import tkinter  # noqa: F401
    except Exception:  # pragma: no cover - environment-specific
        sys.stderr.write(
            "Tkinter is not available in this Python installation.\n"
            "On Windows/macOS it ships with the official python.org installer.\n"
            "On Linux, install it via your package manager "
            "(e.g. 'sudo apt install python3-tk').\n"
        )
        return 1

    from sbom_kev.app import main as app_main

    return app_main()


if __name__ == "__main__":
    raise SystemExit(main())
