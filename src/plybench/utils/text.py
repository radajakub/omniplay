def to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    if value in ("true", "True", "1", "yes", "Yes", "YES", "y", "Y"):
        return True
    if value in ("false", "False", "0", "no", "No", "NO", "n", "N"):
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def extract_params(param_string: str) -> dict[str, str]:
    return {k: v for k, v in (param.split("=") for param in param_string.split(",") if param)}


def inline_multiline_string(prompt: str) -> str:
    return " ".join(line.strip() for line in prompt.split("\n") if line.strip())


def _num_to_char(number: int, start: str) -> str:
    return chr(ord(start) + number)


def number_to_char_upper(number: int) -> str:
    return _num_to_char(number, "A")


def number_to_char_lower(number: int) -> str:
    return _num_to_char(number, "a")


def _char_to_num(char: str, start: str) -> int:
    return ord(char) - ord(start)


def char_to_number_upper(char: str) -> int:
    return _char_to_num(char, "A")


def char_to_number_lower(char: str) -> int:
    return _char_to_num(char, "a")


def order_suffix(order: int) -> str:
    last_char = str(order)[-1]
    return {"1": "st", "2": "nd", "3": "rd"}.get(last_char, "th")
