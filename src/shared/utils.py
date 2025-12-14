# Funções utilitárias


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
