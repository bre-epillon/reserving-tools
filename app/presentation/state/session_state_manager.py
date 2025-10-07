import streamlit as st
from datetime import datetime
import pandas as pd
import os

files = {}

for file in os.listdir("inputs"):
    if file.endswith(".xlsx") and file.startswith("data_202509"):
        files[file] = os.path.join("inputs", file)


def initialize_session_state(debug: bool = False):
    """Initialize or retrieve the session state with repositories and services."""

    # Get current date information
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    st.session_state.setdefault("debug", debug)
    st.session_state.setdefault("current_date", current_date)
    st.session_state.setdefault("time", time)

    st.session_state.setdefault("transactions_file", None)
    st.session_state.setdefault("transactions_data", None)

    # import data if not already in session state and cache them in session state
    if st.session_state.transactions_data is None:
        st.session_state.transactions_file = files.get("data_202509.xlsx", None)

        st.session_state.transactions_data = (
            pd.read_excel(
                st.session_state.transactions_file,
                sheet_name="Final",
                engine="openpyxl",
            )
            if st.session_state.transactions_file
            else None
        )
