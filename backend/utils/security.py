import re
import unicodedata


def safe_display_name(filename: str) -> str:
    name = unicodedata.normalize("NFKC", filename or "")
    name = name.replace("\\", "/").split("/")[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()
    name = re.sub(r"[^\w .()\-]", "_", name, flags=re.UNICODE)
    return name[:160] or "uploaded-media"
