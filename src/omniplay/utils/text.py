def to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    if value in ('true', 'True', '1', 'yes', 'Yes', 'YES', 'y', 'Y'):
        return True
    if value in ('false', 'False', '0', 'no', 'No', 'NO', 'n', 'N'):
        return False
    raise ValueError(f'Invalid boolean value: {value}')


def extract_params(param_string: str) -> dict[str, str]:
    return {k: v for k, v in (param.split('=') for param in param_string.split(',') if param)}


def inline_multiline_string(prompt: str) -> str:
    return ' '.join(line.strip() for line in prompt.split('\n') if line.strip())
