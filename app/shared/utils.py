import pandas as pd
from shared.colored_logging import info, warning, error, debug, success


def create_pivot_table(
    df: pd.DataFrame, index, columns, values, aggfunc="sum", fill_value=0
):
    """Creates a pivot table from the given DataFrame."""
    debug(f"DataFrame shape before pivot: {df.shape}")
    debug(
        f"Creating pivot table with index={index}, columns={columns}, values={values}"
    )

    pivot_df = df.pivot_table(
        index=index,
        columns=columns,
        values=values,
        aggfunc=aggfunc,
        fill_value=fill_value,
    )
    return pivot_df


def get_month(date: str) -> str:
    """Extracts the month from a date."""
    return date.split("-")[1]


def get_year(date: str) -> str:
    """Extracts the year from a date."""
    return int(date.split("-")[0])


def get_quarter(date):
    """Extracts the quarter from a date."""
    return (int(get_month(date)) - 1) // 3 + 1


def get_last_quarter_cutoff(date: str):
    """Returns the last quarter cutoff date given a date."""
    year = get_year(date)
    month = int(get_month(date))
    if month in [1, 2, 3]:
        return f"{int(year) - 1}-12-31"
    elif month in [4, 5, 6]:
        return f"{year}-03-31"
    elif month in [7, 8, 9]:
        return f"{year}-06-30"
    else:
        return f"{year}-09-30"


def get_last_month_cutoff(date: str):
    """Returns the last month cutoff date given a date."""
    year = get_year(date)
    month = int(get_month(date))
    if month == 1:
        return f"{int(year) - 1}-12-31"
    else:
        return f"{year}-{month - 1:02d}-31"


def get_custom_cutoff_month(date: str, actual_month: int):
    """Returns the cutoff date given a date and number of months back."""
    year = get_year(date)
    if actual_month < 10:
        return f"{year}-0{actual_month}-01"
    return f"{year}-{actual_month}-01"


def get_custom_cutoff_quarter(date: str, actual_quarter: int):
    """Returns the cutoff date given a date and number of quarters back."""
    assert actual_quarter in [1, 2, 3, 4], "Quarter must be between 1 and 4"
    actual_month = (actual_quarter - 1) * 3 + 1
    return get_custom_cutoff_month(date, actual_month)
