"""Loads the human-curated domain pack (lab test dictionary)."""
import json
from decimal import Decimal
from pathlib import Path

DICT = json.loads((Path(__file__).with_name("lab_dictionary.json")).read_text())


def unit_factor(code: str, unit: str):
    """Return Decimal factor to the canonical UCUM unit, or None if the unit is not accepted."""
    spec = DICT["tests"].get(code)
    if spec is None or unit not in spec["units"]:
        return None
    return Decimal(str(spec["units"][unit]))
