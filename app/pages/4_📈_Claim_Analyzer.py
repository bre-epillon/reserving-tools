import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER
from shared.constants import SUBLOBS, YEARS
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import create_pivot_table
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="Claim Analyzer Tool", page_icon="📈", layout="wide")

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

st.multiselect(
    "Select claim(s) to analyze",
    options=st.session_state.transactions_data["ClaimReference"].unique(),
    key="selected_claims",
    help="You can select multiple claims by holding down the Ctrl (Windows) or Command (Mac) key while clicking.",
)

with st.expander("Multiple Claims selection help"):
    st.write(
        """
        - Use the dropdown to select one or more claims to analyze.
        - You can select multiple claims by holding down the Ctrl (Windows) or Command (Mac) key while clicking.
        - To clear your selection, click the 'x' next to the selected claim(s) in the input box.
        """
    )
    string_match = (
        st.text_input(
            "Or enter a substring to filter claims (case-insensitive):",
            value="",
            key="claim_string_match",
        )
        .strip()
        .upper()
    )

    if string_match:
        pattern = re.compile(string_match, re.IGNORECASE)
        filtered_claims = [
            claim
            for claim in st.session_state.transactions_data["ClaimReference"].unique()
            if pattern.search(str(claim))
        ]

        st.write(f"Claims matching '{string_match}': {filtered_claims}")

selected_claims = st.session_state.get("selected_claims", [])
string_match = st.session_state.get("claim_string_match", "").strip().upper()

filtered_claims = []
if selected_claims:
    st.write(f"Selected claims: {selected_claims}")
    filtered_claims = selected_claims
elif string_match:
    st.write(f"Claims matching '{string_match}': {filtered_claims}")
    filtered_claims = string_match
elif not selected_claims and not string_match:
    st.warning(
        "Please select at least one claim or enter a substring to filter claims."
    )

if not filtered_claims:
    st.stop()
else:
    st.write(f"Filtered claims: {filtered_claims}")
# if filtered_claims
# filtered_data = st.session_state.transactions_data[
#     st.session_state.transactions_data["ClaimReference"].isin(filtered_claims)
# ]

# policies_pivot = create_pivot_table(
#     df=filtered_data,
#     index=["PolicyReference"],
#     columns="Measure",
#     values="value",
# )


# st.dataframe(policies_pivot)


# get all simulated IBNR BE values as a dataframe with LoB and UWY as index
# simulated_ibnr_df = ibnr_be_factory.get_all_simulated_ibnr_be_by_lob(
#     simulation_n=st.session_state.get("num_simulations", 1000)
# )

# st.dataframe(simulated_ibnr_df)
