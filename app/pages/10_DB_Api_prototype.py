import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.colored_logging import info, warning, error, debug, success
import pandas as pd
from shared.utils import get_sidebar
from services.reinsurance_api import ReinsuranceDataAPI
import os

st.set_page_config(page_title="DataBase API Test", page_icon="📈", layout="wide")

initialize_session_state()

current_uwy = st.session_state.uwy

st.title("Database prototype")
get_sidebar()

st.write("This page provides a small framework to test the DB API")

api = st.session_state.db_api

# df = api.get_reinsurance_data()
# st.write(df)

# number = api.get_policies_number()
# st.info(number["data"]["number_of_policies"])

pr = api.get_policy_premiums("ENR16005805A")
st.info(pr["data"])
