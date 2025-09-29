import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER
from shared.constants import SUBLOBS, YEARS
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import create_pivot_table
import pandas as pd
import numpy as np

st.set_page_config(page_title="Policy Analyzer Tool", page_icon="📈", layout="wide")

initialize_session_state()

st.title("Policy Analyzer Tool")
st.sidebar.title("Navigation")
st.sidebar.markdown(NAVIGATION)

st.sidebar.title("Usage Instructions")
st.sidebar.markdown(USAGE)

st.sidebar.title("Details")
st.sidebar.markdown(DETAILS)

st.sidebar.title("Disclaimer")
st.sidebar.markdown(DISCLAIMER)


st.write(
    "This page provides a shotcut to analyze policy-level data. It is based on the transactions data imported in the previous page."
)

st.selectbox(
    "Select policy to analyze",
    options=st.session_state.transactions_data["ClaimReference"].unique(),
)


policies_pivot = create_pivot_table(
    st.session_state.transactions_data,
    index=["PolicyReference"],
    columns="Measure",
    values="value",
)


st.dataframe(policies_pivot)


# get all simulated IBNR BE values as a dataframe with LoB and UWY as index
# simulated_ibnr_df = ibnr_be_factory.get_all_simulated_ibnr_be_by_lob(
#     simulation_n=st.session_state.get("num_simulations", 1000)
# )

# st.dataframe(simulated_ibnr_df)
