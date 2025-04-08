import math

def replace_nan_with_none(data):
    """
    递归遍历数据，将所有 nan 值替换为 None
    """
    if isinstance(data, list):
        return [replace_nan_with_none(item) for item in data]
    elif isinstance(data, dict):
        return {k: replace_nan_with_none(v) for k, v in data.items()}
    elif isinstance(data, float) and math.isnan(data):
        return None
    return data