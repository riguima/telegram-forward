import re


def is_valid_phone_number(phone_number: str) -> bool:
    regex = re.compile(r'\+\d{13}')
    return bool(regex.findall(phone_number))
