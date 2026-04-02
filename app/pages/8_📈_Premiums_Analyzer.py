import streamlit as st
import plotly.express as px
from presentation.state.session_state_manager import initialize_session_state
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import create_pivot_table, get_quarter, get_sidebar, get_year
from shared.constants import LOB, LOB_MAPPING, SUBLOBS, YEARS, formats
import pandas as pd
import requests
from services.premiums_visualizer import PremiumsVisualizer

st.set_page_config(page_title="Premiums Analyzer", page_icon="📈", layout="wide")

initialize_session_state()
get_sidebar()


# Function to fetch data from our FastAPI backend
@st.cache_data
def fetch_data_from_api():
    url = "http://127.0.0.1:8000/data"
    response = requests.get(url)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("Failed to fetch data from API")
        return pd.DataFrame()


historical_premiums = fetch_data_from_api()
with st.expander("Show Raw Data"):
    st.write("### Data Preview")
    st.dataframe(historical_premiums)

    st.write("### Basic Stats")
    st.write(historical_premiums.describe())

    current_uwy = st.session_state.uwy

st.title("Premiums Analyzer")

st.write("## Premiums Over Time (By Year)")

macro_lob = st.segmented_control(
    options=list(LOB_MAPPING.keys()),
    key="selected_lob",
    help="Select LoB to view.",
    label="LoB to Display",
    default="Energy",
)

display_mode = st.segmented_control(
    options=["standard", "cumulative"],
    key="selected_display_mode",
    help="Select how to view the premiums written.",
    label="View",
    default="standard",
)

pv = PremiumsVisualizer(historical_premiums)

new_fig = pv.get_figure(
    macro_lob=macro_lob,
    color_map_style="focus",
    display_mode=display_mode,
    current_uwy=current_uwy,
)
st.plotly_chart(new_fig, use_container_width=True)
