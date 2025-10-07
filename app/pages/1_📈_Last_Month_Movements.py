import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER
from shared.constants import SUBLOBS, YEARS, formats
from shared.utils import (
    create_pivot_table,
    get_quarter,
    get_last_quarter_cutoff,
    get_custom_cutoff_quarter,
)
from shared.colored_logging import info, warning, error, debug, success
import pandas as pd
import numpy as np

st.set_page_config(page_title="Last Month Movements", page_icon="📈", layout="wide")

initialize_session_state()

st.title("Last Month Movements")
st.sidebar.title("Navigation")
st.sidebar.markdown(NAVIGATION)

st.sidebar.title("Usage Instructions")
st.sidebar.markdown(USAGE)

st.sidebar.title("Details")
st.sidebar.markdown(DETAILS)

st.sidebar.title("Disclaimer")
st.sidebar.markdown(DISCLAIMER)


st.write(
    "This page provides an overview of the quarterly movements for each line of business (LoB), both at the claim level and policy level."
)

df = st.session_state.transactions_data.copy()
df["date"] = pd.to_datetime(df["CutOffDate"])
df = df[df["Measure"].isin(["GClmO", "GClmP"])]

last_month = df["date"].max().to_period("M")
mask_last_month = df["date"].dt.to_period("M") == last_month

st.write(f"Data is available up to: **{last_month}**")


with st.expander("Supporting Selection Filters"):
    col1, col2 = st.columns(2)
    with col1:
        lob_selector = st.multiselect(
            "Select LOB (if not selected, all will be selected)",
            options=df["Final LOB"].unique(),
            key="selected_lob",
            default=df["Final LOB"].unique(),
        )

    with col2:
        uwy_selector = st.multiselect(
            "Select UWY (if not selected, all will be selected)",
            options=df["UWY"].unique(),
            key="selected_uwy",
            default=df["UWY"].unique(),
        )


df = df[df["Final LOB"].isin(lob_selector) & df["UWY"].isin(uwy_selector)]
# Split data
df_total = df.copy()

df_last_month = df.loc[mask_last_month].copy()


# Pivot table for totals
pivot_total = df_total.pivot_table(
    index=["Final LOB", "UWY"],
    columns="Measure",
    values="value",
    aggfunc="sum",
    fill_value=0,
).reset_index()

# Pivot table for last month
pivot_last = df_last_month.pivot_table(
    index=["Final LOB", "UWY"],
    columns="Measure",
    values="value",
    aggfunc="sum",
    fill_value=0,
).reset_index()

# Merge them
result = pivot_total.merge(
    pivot_last, on=["Final LOB", "UWY"], suffixes=("_Total", "_LastMonth"), how="left"
).fillna(0)

# Sum all columns ending with _Total and _LastMonth
total_cols = [col for col in result.columns if col.endswith("_Total")]
lastmonth_cols = [col for col in result.columns if col.endswith("_LastMonth")]

result["Incurred_Total"] = result[total_cols].sum(axis=1)
result["Incurred_LastMonth"] = result[lastmonth_cols].sum(axis=1)


# Format number columns in thousands with 'k' suffix
def format_thousands_colored(val):
    if isinstance(val, (int, float, np.integer, np.floating)):
        color = "green" if val >= 0 else "red"
        return f'<span style="color:{color}">{val / 1000:,.1f}k</span>'
    return val


def format_thousands(val):
    if isinstance(val, (int, float, np.integer, np.floating)):
        return f"{val / 1000:,.1f}k"
    return val


number_cols = result.select_dtypes(include=[np.number]).columns
result_formatted = result.copy()
for col in number_cols:
    if col != "UWY":  # Avoid formatting UWY which is year
        if col.endswith("_Total"):
            result_formatted[col] = result_formatted[col].apply(format_thousands)
        elif col.endswith("_LastMonth"):
            result_formatted[col] = result_formatted[col].apply(
                format_thousands_colored
            )

st.write(result_formatted.to_html(escape=False, index=False), unsafe_allow_html=True)
