def align(x, boundary):
    rem = x % boundary

    if rem != 0:
        x += boundary - rem

    return x


def clamp(var: int, min_value: int, max_value: int):
    return min(max_value, max(min_value, var))


def find_first_available_id(used: set[int], maximum: int, minimum: int = 0):
    """
    Returns the smallest integer in the range [minimum = 0, maximum) that is
    not in the given set. If there is no such integer, None is returned.
    """
    for i in range(minimum, maximum):
        if i not in used:
            return i

    return None
