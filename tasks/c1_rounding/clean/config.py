"""默认配置。"""

DEFAULT_K = 3
DEFAULT_PAGE_SIZE = 2


def resolve_k(k):
    """缺省时换成默认的词项个数。"""
    return DEFAULT_K if k is None else k


def resolve_page_size(size):
    """缺省时换成默认的页大小。"""
    return DEFAULT_PAGE_SIZE if size is None else size
