"""对外接口。"""

from tokenizer import tokenize
from vocab import count, top


def keyword_summary(text, k=3):
    """给出出现次数最多的前 k 个词元及其占比。

    返回 total 与 top 两个键。top 是 (词, 次数, 占比) 三元组的列表，
    占比按词元总数计算并保留四位小数。文本不含词元时返回总数零与空列表。
    """
    tokens = tokenize(text)
    if not tokens:
        return {"total": 0, "top": []}
    counts = count(tokens)
    return {"total": len(tokens),
            "top": [(word, n, round(n / len(tokens), 4))
                    for word, n in top(counts, k)]}
