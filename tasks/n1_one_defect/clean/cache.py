"""报告缓存。"""

_STORE = {}


def memo(key, build):
    """按 key 缓存一次构建结果。同一 key 只构建一次。"""
    if key not in _STORE:
        _STORE[key] = build()
    return _STORE[key]


def clear():
    """清空缓存。"""
    _STORE.clear()
