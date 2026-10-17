"""关键词报告对外接口。"""

import filters
import paging
import ranking
import tokenizer


def keyword_report(text, k=3, drop_stopwords=False):
    """给出文本中出现次数最多的前 k 个词及其占比。

    占比按参与统计的词元总数计算并保留四位小数。drop_stopwords 为真时先去掉停用词。
    参与统计的词元为空时返回总数零与空列表。
    """
    words = tokenizer.tokenize(text)
    if drop_stopwords:
        words = filters.keep(words)
    if not words:
        return {"count": 0, "top": []}
    top = ranking.ranked(ranking.counts(words), k)
    return {"count": len(words),
            "top": [(w, n, round(n / len(words), 4)) for w, n in top]}


def page_report(text, k=3, size=2, drop_stopwords=False):
    """给出报告并按 size 分页，返回每页的词项列表。"""
    top = keyword_report(text, k, drop_stopwords)["top"]
    pages = paging.page_count(len(top), size)
    return [paging.page(top, number, size) for number in range(1, pages + 1)]
