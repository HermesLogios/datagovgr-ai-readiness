"""Metadata checks of the study, applied to one dataset record.

The checks are the functions of scripts/04_metadata_checks.py. The script is loaded from its
file, so that every check exists in one place and the scores are those of the study.
"""

import importlib.util
import sys
import threading
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKS_SCRIPT = ROOT / "scripts" / "04_metadata_checks.py"
SCRIPT_MODULE_NAME = "datagovgr_metadata_checks"

# Criteria scored from the metadata, in the order of the script.
CHECK_IDS = ("M1", "M2", "M3", "M4", "M6", "M7", "M9", "Q5", "Q6")

_lock = threading.Lock()
_script = None


@dataclass(frozen=True)
class CheckOutput:
    score: int | None
    reason: str
    measurements: dict


def checks_script():
    """Module of scripts/04_metadata_checks.py, loaded once, with its table of file types filled."""
    global _script
    with _lock:
        if _script is None:
            spec = importlib.util.spec_from_file_location(SCRIPT_MODULE_NAME, CHECKS_SCRIPT)
            module = importlib.util.module_from_spec(spec)
            sys.modules[SCRIPT_MODULE_NAME] = module
            spec.loader.exec_module(module)
            found = tuple(code for code, _, _ in module.CHECKS)
            if found != CHECK_IDS:
                raise RuntimeError(f"{CHECKS_SCRIPT.name} holds the checks {found}, expected {CHECK_IDS}")
            module.FILE_TYPES.update(module.load_file_types())
            _script = module
    return _script


def run_metadata_checks(record: dict, reference_date: date) -> dict[str, CheckOutput]:
    """Applies the nine metadata checks to a dataset record.

    The reference date is the day against which the age of the last change is measured (Q5):
    the date of the snapshot for a stored record, the day of the check for a record read from
    the portal.
    """
    script = checks_script()
    outputs = {}
    with _lock:
        script.REFERENCE_DATE = reference_date
        for code, _, check in script.CHECKS:
            values = dict(check(record))
            prefix = code.lower() + "_"
            score = values.pop(prefix + "score")
            reason = values.pop(prefix + "reason")
            outputs[code] = CheckOutput(
                score=None if score is None else int(score),
                reason=reason or "",
                measurements={key.removeprefix(prefix): value for key, value in values.items()},
            )
    return outputs


def visible_text(value) -> str:
    """Text of a metadata field as the checks read it."""
    return checks_script().visible_text(value)
