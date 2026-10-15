"""词频与排序。"""


def count(tokens):
    """统计每个词元的出现次数。"""
    counts = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def sort_key(pair):
    """排序键。"""
    word, n = pair
    return (-n, word)


def top(counts, k):
    """按次数降序、同次按词形升序取前 k 项。"""
    ranked = sorted(counts.items(), key=sort_key)
    return ranked[:k]
