import pandas as pd


def load_input_tables(input_file):
    """loads the tables from the Summary sheet of the input file (Finance allocation file)"""
    raw_df = pd.read_excel(input_file, sheet_name="Summary", header=None)

    n_rows = 10
    n_cols = 17
    table_ranges = {
        "GEP": (5, 2),  # (start_row, start_col)
        "GClmP": (20, 2),
        "GClmO": (35, 2),
        "IBNR BE": (50, 2),
        "IBNR Stat": (50, 22),
    }

    tables = {}
    for table_name, (start_row, start_col) in table_ranges.items():
        t = raw_df.iloc[start_row : start_row + n_rows, start_col : start_col + n_cols]
        t = t.reset_index(drop=True).set_index(t.columns[0])
        t.index.name = None
        t.columns = t.iloc[0]
        t = t[1:]

        for col in t.columns:
            t[col] = pd.to_numeric(t[col], errors="coerce")

        # replace 2017 by 2017 & prior
        t.loc[2017] += t.loc[2016]
        t = t[1:]

        # group subclasses
        t["ENTOT"] = t[["ENOFF", "ENONS", "ENCON", "ENOTH"]].sum(axis=1)
        t["LITOT"] = t[["LIIND", "LIMLT", "LISHT"]].sum(axis=1)
        t["DCTOT"] = t[
            ["DCBON", "DCMAR", "DCFIL", "DCFRO", "DCSPE", "DCLIA", "DCPRO", "DCENR"]
        ].sum(axis=1)

        t.fillna(0, inplace=True)
        tables[table_name] = t

    return tables


def summary_to_data_table(df):
    """transforms sumamry df to data prop required by the dash data_table"""
    df = df.reset_index()
    df.columns = [col if col != "index" else "UWY" for col in df.columns]
    return df.to_dict("records")
