"""词元切分。"""

import re

TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]*[A-Za-z]|[A-Za-z]")


def tokenize(text):
    """按字母切分，保留词内撇号与连字符，统一转小写。"""
    return [match.group(0).lower() for match in TOKEN.finditer(text)]
