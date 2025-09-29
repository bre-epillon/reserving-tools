import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER
from shared.constants import SUBLOBS, YEARS
from shared.utils import (
    create_pivot_table,
    get_quarter,
    get_last_quarter_cutoff,
    get_custom_cutoff_quarter,
)
from shared.colored_logging import info, warning, error, debug, success
import pandas as pd
import numpy as np

st.set_page_config(page_title="Quarterly Results", page_icon="📈", layout="wide")

initialize_session_state()

st.title("Quarterly Results")
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


policies_pivot = create_pivot_table(
    st.session_state.transactions_data,
    index=["PolicyReference"],
    columns="Measure",
    values="value",
)

claims_pivot = create_pivot_table(
    st.session_state.transactions_data,
    index=["ClaimReference"],
    columns="Measure",
    values="value",
)

st.dataframe(policies_pivot)
st.dataframe(claims_pivot)


st.write("LoB Level Summary")
quarterly_data = st.session_state.transactions_data.copy()
quarterly_data["CutOffDate"] = quarterly_data["CutOffDate"].dt.strftime("%Y-%m-%d")


@st.cache_data(ttl=60)
def get_quarterly_data(quarter):
    info(f"Filtering data for quarter: {quarter}")
    return st.session_state.transactions_data.query(
        f"CutOffDate >= '{get_custom_cutoff_quarter(date=st.session_state.current_date, actual_quarter=quarter)}'"
    )


st.selectbox(
    "Select quarterly data",
    options=[i for i in range(1, 5)],
    key="selected_quarter",
    index=int(get_quarter(st.session_state.current_date)),
)

quarterly_data = get_quarterly_data(st.session_state.selected_quarter)

st.write(
    f"Showing data from {get_custom_cutoff_quarter(date=st.session_state.current_date, actual_quarter=st.session_state.selected_quarter)} onwards"
)

# quarterly_data = quarterly_data[
#     quarterly_data["CutOffDate"] > get_last_quarter_cutoff(st.session_state.current_date)
# ]

quarterly_pivot = create_pivot_table(
    quarterly_data,
    index=["UWY"],
    columns="Final LOB",
    values="value",
    fill_value=0,
    aggfunc="sum",
)

st.dataframe(quarterly_data.head())
st.dataframe(quarterly_pivot)

with st.expander("See Summary by policy level"):
    lob_policy_pivot = create_pivot_table(
        st.session_state.transactions_data,
        index=["LOB"],
        columns="Measure",
        values="value",
    )
    st.dataframe(lob_policy_pivot)
