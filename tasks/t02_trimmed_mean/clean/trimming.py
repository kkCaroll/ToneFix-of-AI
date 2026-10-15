"""截尾统计。"""

import series


def trimmed_mean(values, fraction):
    """截尾均值。两端各去掉 fraction 比例的元素后取算术平均。

    fraction 取 0 到 0.5，每端去掉的个数向下取整。fraction 为零时等同于算术平均。
    去掉后若无剩余元素，抛 ValueError。
    """
    ordered = sorted(values)
    cut = int(len(ordered) * fraction)
    kept = ordered[cut:len(ordered) - cut]
    return series.mean(kept)


def trim_report(text, fraction):
    """解析文本并给出原均值与截尾均值。"""
    values = series.parse(text)
    return {"n": len(values), "mean": series.mean(values),
            "trimmed": trimmed_mean(values, fraction)}
