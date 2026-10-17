"""词频排序。"""


def counts(words):
    """统计每个词的出现次数。"""
    table = {}
    for word in words:
        table[word] = table.get(word, 0) + 1
    return table


def order(item):
    """排序键。"""
    word, n = item
    return (-n, word)


def ranked(table, k):
    """取前 k 项，按次数降序、同次按词形升序。"""
    return sorted(table.items(), key=order)[:k]
