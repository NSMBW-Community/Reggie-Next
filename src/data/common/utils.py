import pickletools


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


def DecodeOldReggieInfo(data, validKeys):
    """
    Decode the provided level info data into a dictionary, which will
    have only the keys specified. Raises an exception if the data can't
    be parsed.
    """
    # The idea here is that we implement just enough of the pickle
    # protocol (v2) to be able to parse the dictionaries that past
    # Reggies have pickled, even if PyQt4 isn't available.
    #
    # We keep track of the stack and memo, just enough to figure out
    # in what order the strings are pushed to the stack. (We need to
    # implement the memo because default level info uses memoization to
    # avoid encoding the '-' string more than once.) Then we filter out
    # 'PyQt4.QtCore' and 'QString'. Assuming nobody's crazy enough to
    # use those as actual level info field values, that should leave us
    # with exactly 12 strings (6 field names and 6 fields). Then we just
    # put the dictionary together in the same way as the SETITEMS pickle
    # instruction, and we're done.

    # Figure out in what order strings are pushed to the pickle stack
    stack = []
    memo = {}
    for inst, arg, _ in pickletools.genops(data):
        if inst.name in ['SHORT_BINSTRING', 'BINSTRING', 'BINUNICODE']:
            stack.append(arg)
        elif inst.name == 'GLOBAL':
            # In practice, this is used to push sip._unpickle_type,
            # which then gets BINGET'd over and over. So we have to take
            # it into account, or else we get confused and end up
            # pushing some random string to the stack repeatedly instead
            stack.append(None)
        elif inst.name == 'BINPUT' and stack:
            memo[arg] = stack[-1]
        elif inst.name == 'BINGET' and arg in memo:
            stack.append(memo[arg])

    # Filter out uninteresting strings and check that the length is right
    strings = [s for s in stack if s not in {'PyQt4.QtCore', 'QString', None}]
    if len(strings) != 12:
        raise ValueError(f'Wrong number of strings in level metadata ({len(strings)})')

    # Convert e.g. [a, b, c, d, e, f] -> {a: b, c: d, e: f}
    # https://stackoverflow.com/a/12739974
    it = iter(strings)
    levelinfo = dict(zip(it, it))

    # Double-check that the keys are as expected, and return
    if set(levelinfo) != validKeys:
        raise ValueError('Wrong keys in level metadata: ' + str(set(levelinfo)))

    return levelinfo
