import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER
from shared.constants import SUBLOBS, YEARS
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import create_pivot_table
import pandas as pd
import numpy as np
import re
import plotly.express as px

st.set_page_config(page_title="Claim Analyzer Tool", page_icon="📈", layout="wide")

initialize_session_state()

st.title("Claims Analyzer Tool")
st.sidebar.title("Navigation")
st.sidebar.markdown(NAVIGATION)

st.sidebar.title("Usage Instructions")
st.sidebar.markdown(USAGE)

st.sidebar.title("Details")
st.sidebar.markdown(DETAILS)

st.sidebar.title("Disclaimer")
st.sidebar.markdown(DISCLAIMER)

st.write(
    "This page provides a shotcut to analyze claims-level data. It is based on the transactions data imported in the previous page."
)
ALL_CLAIMS = st.session_state.transactions_data["ClaimReference"].dropna().unique()
st.multiselect(
    "Select claim(s) to analyze",
    options=ALL_CLAIMS,
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
        filtered_claims_match = [
            claim for claim in ALL_CLAIMS if pattern.search(str(claim))
        ]

        st.write(f"Claims matching '{string_match}': {filtered_claims_match}")
    else:
        st.warning("No claims match the provided substring.")

selected_claims = st.session_state.get("selected_claims", [])
string_match = st.session_state.get("claim_string_match", "").strip().upper()

filtered_claims = []
if selected_claims:
    st.write(f"Selected claims: {selected_claims}")
    filtered_claims = selected_claims
elif string_match:
    st.write(f"Claims matching '{string_match}': {filtered_claims_match}")
    filtered_claims = filtered_claims_match
elif not selected_claims and not string_match:
    filtered_claims = ALL_CLAIMS.tolist()

if selected_claims or string_match:
    st.write(f"Filtered claims: {filtered_claims}")


filtered_claims_data = st.session_state.transactions_data[
    st.session_state.transactions_data["ClaimReference"].isin(filtered_claims)
]

st.write(
    f"Showing data for {len(filtered_claims_data['ClaimReference'].unique())} claim(s) from a total of {len(ALL_CLAIMS)} claims."
)


policies_pivot = create_pivot_table(
    df=filtered_claims_data,
    index=["ClaimReference"],
    columns="Measure",
    values="value",
    aggfunc="sum",
)


st.dataframe(policies_pivot)

# Filter only paid and outstanding
df = filtered_claims_data[filtered_claims_data["Measure"].isin(["GClmP", "GClmO"])]

# Compute cumulative sum over time
df = df.sort_values("CutOffDate")
df["cumulative"] = df.groupby("Measure")["value"].cumsum()

# Plot cumulative evolution
fig = px.line(
    df,
    x="CutOffDate",
    y="cumulative",
    color="Measure",
    markers=True,
    title="Cumulative Claim Cost Evolution",
)

if len(filtered_claims) != len(ALL_CLAIMS):
    st.download_button(
        label="Download filtered claims data as CSV",
        data=filtered_claims_data.to_csv(index=False).encode("utf-8"),
        file_name="filtered_claims_data.csv",
        mime="text/csv",
    )

    st.plotly_chart(fig)
