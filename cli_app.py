"""Compatibility wrapper for the installed transformer-design command."""

from transformer_design.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
