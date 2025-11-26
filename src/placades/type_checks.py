def above_five_check(n):
    if n > 5:
        msg = f"The input {n} is above 5."
        raise ValueError(msg)
    return n


def float_check(n):
    try:
        n = float(n)
    except Exception as e:
        msg = f"The input {n} cannot be converted to float."
        raise ValueError(msg)
    return n


def check_parameter(*args):
    for a in args:
        if a is None:
            raise ValueError
