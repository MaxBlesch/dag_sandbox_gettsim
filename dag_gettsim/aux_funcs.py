import copy


def elementwise_min(x, y):
    """
    Calculating a pandas Series which contains the elementwise minimum of x and y.
    Parameters
    ----------p
    x : pd.Series
    y : pd.Series, int or float

    Returns
    -------
    Pandas Series which contains the elementwise minimum of x and y.
    """
    out = copy.deepcopy(x)
    out.loc[x > y] = y
    return out
