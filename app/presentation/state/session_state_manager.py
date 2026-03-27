import streamlit as st
from datetime import datetime
import pandas as pd
import os
from shared.colored_logging import info, warning, error, debug, success
from services.reinsurance_api import ReinsuranceDataAPI

files = {}

for file in os.listdir("inputs"):
    if file.endswith(".xlsx") and file.startswith("data_202"):
        files[file] = os.path.join("inputs", file)


def initialize_session_state(debug: bool = False):
    """Initialize or retrieve the session state with repositories and services."""

    # Get current date information
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    month = now.strftime("%B")
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    uwy = year - 1 if month in ["January", "February", "March"] else year

    st.session_state.setdefault("debug", debug)
    st.session_state.setdefault("current_date", current_date)
    st.session_state.setdefault("time", time)
    st.session_state.setdefault("month", month)
    st.session_state.setdefault("quarter", quarter)
    st.session_state.setdefault("year", year)
    st.session_state.setdefault("uwy", uwy)

    st.session_state.setdefault("transactions_file", None)
    st.session_state.setdefault("transactions_data", None)

    st.session_state.setdefault("ri_outward", None)

    st.session_state.setdefault("historical_premiums", None)

    # import data if not already in session state and cache them in session state
    if st.session_state.transactions_data is None:
        data_file_name = "data_202603.xlsx"
        st.session_state.transactions_file = files.get(data_file_name, None)

        st.session_state.transactions_data = (
            pd.read_excel(
                st.session_state.transactions_file,
                sheet_name="Final",
                engine="openpyxl",
            )
            if st.session_state.transactions_file
            else None
        )

        info(f"Transactions data {data_file_name=} loaded into session state.")

        st.session_state.historical_premiums = (
            pd.read_csv(
                "inputs/premiums_2026-02-27.csv",  # "Expected GGWP (USD)","Policy Underwriting Month","Policy Underwriting Year","Reserving Class Code","Reserving Class Full Name level 1"
            )
            if os.path.exists("inputs/premiums_2026-02-27.csv")
            else None
        )

        info("Historical premiums data loaded into session state.")

        st.session_state.db_api = ReinsuranceDataAPI(
            "inputs/ProductionReport_2025Q4.xlsx"
        )

        info("Database API loaded into session state.")

        # st.session_state.ri_outward = (
        #     pd.read_excel(
        #         st.session_state.transactions_file,
        #         sheet_name="RI Outward",
        #         engine="openpyxl",
        #     )
        #     if st.session_state.transactions_file
        #     else None
        # )

        # info("RI Outward data loaded into session state.")
