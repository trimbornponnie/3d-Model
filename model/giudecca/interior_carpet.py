"""Carpet interiors: the north row (interior_carpet_north) and the middle and
south rows with the campo strip (interior_carpet_ms); docs/INTERIORS.md."""
from __future__ import annotations

import importlib
import importlib.util


def build(ctx) -> None:
    for name in ('interior_carpet_north', 'interior_carpet_ms'):
        if importlib.util.find_spec(f'giudecca.{name}') is not None:
            importlib.import_module(f'giudecca.{name}').build(ctx)
