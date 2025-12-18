# Funções utilitárias
import re
import unicodedata


def plural(count: int, singular: str, plural: str) -> str:
    if count == 1:
        return singular
    return plural


def format_list_to_markdown(textos: list[str]) -> str:
    return "\n".join([f"- {texto}" for texto in textos])


def string_to_list(string: str) -> list[str]:
    items: list[str] = []
    for item in string.split(","):
        item = item.strip()
        if item:
            items.append(item)
    return items


def remove_diacritics(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if unicodedata.category(c) != "Mn"
    )


def remove_control_characters(text: str) -> str:
    """
    Remove control characters from text, keeping common whitespace characters.
    """
    return "".join(
        c
        for c in text
        if not (unicodedata.category(c)[0] == "C" and c not in " \n\r\t")
    )


def sanitize_text(text: str) -> str:
    """
    Sanitize text for matching: lowercase, normalize whitespace, remove accents and control chars.
    """
    lower = text.lower()
    clean = re.sub(r"\s+", " ", lower)
    clean = remove_diacritics(clean)
    clean = remove_control_characters(clean)
    return clean.strip()


def pretty_print(obj: object) -> str:
    lines = [obj.__class__.__name__ + ":"]
    for key, val in vars(obj).items():
        lines += "{}: {}".format(key, val).split("\n")
    return "\n    ".join(lines)
