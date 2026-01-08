import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import create_pivot_table, get_quarter, get_sidebar, get_year
import pandas as pd

st.set_page_config(
    page_title="One Dollar Claims Analyzer Tool", page_icon="📈", layout="wide"
)

initialize_session_state()

st.title("One Dollar Claims Analyzer Tool")
get_sidebar()

st.write(
    "This page provides a shotcut to analyze claims-level data. It is based on the transactions data automatically imported from the ABE&MBE file."
)

ALL_CLAIMS = st.session_state.transactions_data["ClaimReference"].dropna().unique()

col1, col2, col3 = st.columns(3)

with col1:
    st.selectbox(
        "Select quarter",
        options=[i for i in range(1, 5)],
        key="selected_quarter",
        index=int(get_quarter(st.session_state.current_date)) - 1,
    )
with col2:
    st.selectbox(
        "Select year",
        options=[i for i in range(2017, 2027)],
        key="selected_year",
        index=int(get_year(st.session_state.current_date)) - 2017,
    )
with col3:
    st.slider(
        "Select treshold",
        min_value=1,
        max_value=10000,
        value=100,
        key="selected_treshold",
    )

st.write("### One Dollar Claims Summary")

quarter = st.session_state.selected_quarter
year = st.session_state.selected_year

filtered_data = st.session_state.transactions_data.query(
    f"CutOffDate <= '{year}-{(quarter - 1) * 3 + 1:02}-01' and Measure in ['GClmP', 'GClmO']"
)

claims_incurred_at_quarter = (
    filtered_data.groupby(["ClaimReference", "PolicyReference", "UWY", "Final LOB"])[
        "value"
    ]
    .sum()
    .reset_index()
)

treshold_query = f"abs(value) <= {st.session_state.selected_treshold} and value != 0"
claims_incurred_at_quarter_list = claims_incurred_at_quarter.query(
    treshold_query
).ClaimReference.unique()

st.write(
    f"Total number of claims incurred at Q{quarter} {year}: **{len(claims_incurred_at_quarter_list)}**"
)

st.dataframe(claims_incurred_at_quarter.query(treshold_query))


st.write(
    st.session_state.transactions_data.query(
        f"ClaimReference in {list(claims_incurred_at_quarter_list)}"
    )
    .groupby(["Final LOB", "UWY"])["value"]
    .sum()
    .unstack(fill_value=0)
)
