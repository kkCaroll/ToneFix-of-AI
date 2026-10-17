"""结果分页。"""


def page(items, number, size):
    """取第 number 页，页码从 1 开始。越界返回空列表。"""
    start = (number - 1) * size
    return list(items[start:start + size])


def page_count(total, size):
    """总页数。页大小非正时抛 ValueError。"""
    if size <= 0:
        raise ValueError("页大小必须为正")
    return (total + size - 1) // size
