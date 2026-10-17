"""停用词过滤。"""

STOPWORDS = frozenset({"the", "a", "an", "and", "or", "of", "to", "in", "is", "it"})


def keep(words):
    """去掉停用词，保留其余词的原有顺序。"""
    return [word for word in words if word not in STOPWORDS]
