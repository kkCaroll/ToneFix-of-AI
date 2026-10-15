"""序列解析与摘要。"""


def parse(text):
    """把逗号分隔的数字串解析成浮点数列表。空串与纯空白返回空列表。"""
    if not text.strip():
        return []
    return [float(part) for part in text.split(",")]


def mean(values):
    """算术平均。空序列抛 ValueError。"""
    if not values:
        raise ValueError("空序列")
    return sum(values) / len(values)
