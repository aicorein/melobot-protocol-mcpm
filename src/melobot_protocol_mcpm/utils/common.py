def truncate(s: str, max_len: int = 1000) -> str:
    return s if len(s) <= max_len else s[:max_len] + "..."
