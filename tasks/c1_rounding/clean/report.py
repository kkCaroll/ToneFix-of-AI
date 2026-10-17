"""关键词报告对外接口。"""

from decimal import Decimal, ROUND_HALF_UP


import cache
import config
import filters
import paging
import ranking
import tokenizer


def share(n, total):
    """占比，按十进制四舍五入保留四位小数。"""
    value = (Decimal(n) / Decimal(total)).quantize(Decimal("0.0001"),
                                                   rounding=ROUND_HALF_UP)
    return float(value)



def keyword_report(text, k=None, drop_stopwords=False, use_cache=True):
    """给出文本中出现次数最多的前 k 个词及其占比。

    占比按参与统计的词元总数计算，以十进制四舍五入保留四位小数。
    drop_stopwords 为真时先去掉停用词。k 缺省时取配置里的默认值。
    参与统计的词元为空时返回总数零与空列表。
    """
    size = config.resolve_k(k)

    def build():
        words = tokenizer.tokenize(text)
        if drop_stopwords:
            words = filters.keep(words)
        if not words:
            return {"count": 0, "top": []}
        table = ranking.counts(words)
        top = ranking.ranked(table, size)
        return {"count": len(words),
                "top": [(w, n, share(n, len(words))) for w, n in top]}

    if not use_cache:
        return build()
    return cache.memo((text, size, drop_stopwords), build)


def page_report(text, k=None, size=None, drop_stopwords=False):
    """给出报告并按 size 分页，返回每页的词项列表。"""
    width = config.resolve_page_size(size)
    top = keyword_report(text, k, drop_stopwords)["top"]
    pages = paging.page_count(len(top), width)
    return [paging.page(top, number, width) for number in range(1, pages + 1)]
