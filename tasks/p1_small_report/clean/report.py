"""关键词报告对外接口。"""

import ranking
import tokenizer


def keyword_report(text, k=3):
    """给出文本中出现次数最多的前 k 个词及其占比。

    占比按词元总数计算并保留四位小数。文本不含词元时返回总数零与空列表。
    """
    words = tokenizer.tokenize(text)
    if not words:
        return {"count": 0, "top": []}
    top = ranking.ranked(ranking.counts(words), k)
    return {"count": len(words),
            "top": [(w, n, round(n / len(words), 4)) for w, n in top]}
