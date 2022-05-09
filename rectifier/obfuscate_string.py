import re


def obfuscate_string(input: str, visible_chars_length: int = 4):
    return f'{input[:visible_chars_length]}{re.sub("(?!-).", "*", input[visible_chars_length:])}'
