import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
import os
import pandas as pd
from shared.colored_logging import info, warning, error, debug, success
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER

st.set_page_config(page_title="Import Inputs", page_icon="📂", layout="wide")

initialize_session_state()
info("Session state initialized.")

formats = {
    "millions": lambda x: f"{x / 1e6:.1f}m",
    "default": lambda x: f"{x:.2f}",
    "thousands": lambda x: f"{x / 1e3:.1f}k",
    "billions": lambda x: f"{x / 1e9:.2f}b",
}


st.sidebar.title("Navigation")
st.sidebar.markdown(NAVIGATION)

st.sidebar.title("Usage Instructions")
st.sidebar.markdown(USAGE)

st.sidebar.title("Details")
st.sidebar.markdown(DETAILS)

st.sidebar.title("Disclaimer")
st.sidebar.markdown(DISCLAIMER)


files = {}

for file in os.listdir("inputs"):
    if file.endswith(".xlsx") and file.startswith("data_202508"):
        files[file] = os.path.join("inputs", file)


def display_import_data_module():
    """
    Display the module for importing IBNR Allocation data.
    Saves uploaded files in session state for application-wide access.
    """
    # File upload
    st.write("## Step 1: Upload Input Files")
    transactions_file = st.file_uploader(
        "Upload the Transaction Data File",
        type=["xlsx", "xlsm"],
        help="Upload an Excel file with columns: ...",
        key="ibnr_file_uploader",
    )

    # Save files in session state if uploaded
    if transactions_file is not None:
        success(f"IBNR file {transactions_file.name} uploaded.")
        st.session_state.transactions_file = transactions_file
        st.success(f"File uploaded: {transactions_file.name}")
    else:
        warning("No IBNR file uploaded yet.")
        st.warning("No ibnr file uploaded yet. Please upload a file to proceed.")

    # Only create importer if both files are uploaded
    if "transactions_file" in st.session_state and "abe_mbe_file" in st.session_state:
        debug("Both files uploaded, creating Importer instance.")


if st.session_state.transactions_data is not None:
    st.write("## Transactions Data Imported Successfully")
    st.write("Below a small summary of the imported data")

    st.write("### Transactions Data Sample")
    st.dataframe(st.session_state.transactions_data.head())
