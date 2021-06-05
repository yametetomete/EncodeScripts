import tempfile


def get_temp_filename(prefix: str = "", suffix: str = "") -> str:
    return f"{prefix}{next(tempfile._get_candidate_names())}{suffix}"  # type: ignore
