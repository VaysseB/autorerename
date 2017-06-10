

def first_map(func: callable, items: iter):
    """
    Return the first result that `bool() == True`.
    """
    for item in items:
        res = func(item)
        if res:
            return res
