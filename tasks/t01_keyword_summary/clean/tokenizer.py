"""把文本切成词元。"""

import re

TOKEN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def tokenize(text):
    """按字母序列切分，保留词内撇号，统一转小写。"""
    return [match.group(0).lower() for match in TOKEN.finditer(text)]
