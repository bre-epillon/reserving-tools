import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER
from shared.constants import SUBLOBS, YEARS
from shared.utils import (
    create_pivot_table,
    get_month,
    get_quarter,
    get_last_month_cutoff,
    get_last_quarter_cutoff,
    get_custom_cutoff_month,
    get_custom_cutoff_quarter,
)
from shared.colored_logging import info, warning, error, debug, success
import pandas as pd
import numpy as np

st.set_page_config(page_title="Monthly Results", page_icon="📈", layout="wide")

initialize_session_state()

st.title("Monthly Results")
st.sidebar.title("Navigation")
st.sidebar.markdown(NAVIGATION)

st.sidebar.title("Usage Instructions")
st.sidebar.markdown(USAGE)

st.sidebar.title("Details")
st.sidebar.markdown(DETAILS)

st.sidebar.title("Disclaimer")
st.sidebar.markdown(DISCLAIMER)


st.write(
    "This page provides an overview of the Monthly movements for each line of business (LoB), both at the claim level and policy level."
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

# st.dataframe(policies_pivot)
# st.dataframe(claims_pivot)


st.write("LoB Level Summary")
monthly_data = st.session_state.transactions_data.copy()
monthly_data["CutOffDate"] = monthly_data["CutOffDate"].dt.strftime("%Y-%m-%d")


@st.cache_data(ttl=60)
def get_monthly_data(month):
    return st.session_state.transactions_data.query(
        f"CutOffDate >= '{get_custom_cutoff_month(date=st.session_state.current_date, actual_month=month)}'"
    )


st.selectbox(
    "Select monthly data",
    options=[i for i in range(1, 13)],
    key="selected_month",
    index=int(get_month(st.session_state.current_date)) - 1,
)

monthly_data = get_monthly_data(month=st.session_state.selected_month)

st.write(
    f"Showing data from {get_custom_cutoff_month(date=st.session_state.current_date, actual_month=st.session_state.selected_month)} onwards"
)

# monthly_data = monthly_data[
#     monthly_data["CutOffDate"] > get_last_month_cutoff(st.session_state.current_date)
# ]

monthly_pivot = create_pivot_table(
    monthly_data,
    index=["UWY"],
    columns="Final LOB",
    values="value",
    fill_value=0,
    aggfunc="sum",
)

st.dataframe(monthly_data.head())
st.dataframe(monthly_pivot)

with st.expander("See Summary by policy level"):
    lob_policy_pivot = create_pivot_table(
        st.session_state.transactions_data,
        index=["LOB"],
        columns="Measure",
        values="value",
    )
    st.dataframe(lob_policy_pivot)
