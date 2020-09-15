
def trim_address(address):
    return address[:4] + '...' + address[-4:]


def format_balance(number: str, digits_after_point=0):
    res = float(number) / 1e12
    return f'{res:,.{digits_after_point}f}'
