import os
import tempfile


def get_temp_filename(prefix: str = "", suffix: str = "") -> str:
    return f"{prefix}{next(tempfile._get_candidate_names())}{suffix}"  # type: ignore


def bin_to_plat(binary: str) -> str:
    if os.name == "nt":
        return binary if binary.lower().endswith(".exe") else f"{binary}.exe"
    else:
        return binary if not binary.lower().endswith(".exe") else binary[:-len(".exe")]
