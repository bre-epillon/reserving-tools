import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import create_pivot_table, get_quarter, get_sidebar, get_year
from shared.constants import LOB, LOB_MAPPING, SUBLOBS, YEARS, formats
import pandas as pd

color_map = {
    2016: "#FECB52",
    2017: "#EF553B",
    2018: "#00CC96",
    2019: "#AB63FA",
    2020: "#FFA15A",
    2021: "#19D3F3",
    2022: "#FF6692",
    2023: "#B6E880",
    2024: "#FF97FF",
    2025: "#636EFA",
    2026: "#8C564B",
    2027: "#17BECF",
}

st.set_page_config(page_title="Premiums Analyzer", page_icon="📈", layout="wide")

initialize_session_state()

current_uwy = st.session_state.uwy

st.title("Premiums Analyzer")
get_sidebar()

st.write("This page provides a ...")


historical_premiums = st.session_state.historical_premiums

group_sum = historical_premiums.groupby(
    ["Policy Underwriting Year", "Reserving Class Code"]
)["Expected GGWP (USD)"].transform("sum")

historical_premiums["monthly_percentage_value"] = (
    historical_premiums["Expected GGWP (USD)"] / group_sum * 100
)

st.dataframe(historical_premiums)

col1, col2 = st.columns(2)
with col1:
    # st.selectbox(
    #     "Select a LoB to analyze:",
    #     options=historical_premiums["Reserving Class Code"].unique(),
    #     key="selected_lob",
    #     help="Select a Line of Business (LoB) to analyze the premiums.",
    # )
    selected_lob = st.segmented_control(
        options=historical_premiums["Reserving Class Code"].unique(),
        key="selected_lob",
        help="Select a Line of Business (LoB) to analyze the premiums.",
        label="Line of Business (LoB) to Analyze",
    )

    with st.expander("Aggregated Selectors"):
        aggregated_lob = st.segmented_control(
            options=[keys for lob in LOB for keys in lob.values()] + ["None"],
            key="aggregated_lob",
            help="Select an aggregated Line of Business (LoB) to analyze the premiums.",
            label="Aggregated Line of Business (LoB) to Analyze",
        )

    if aggregated_lob != "None":
        selected_lob = st.session_state.selected_lob
        if selected_lob not in LOB_MAPPING[aggregated_lob]:
            st.session_state.selected_lob = LOB_MAPPING[aggregated_lob][0]


with col2:
    selected_years = st.segmented_control(
        options=historical_premiums["Policy Underwriting Year"].unique(),
        key="selected_years",
        help="Select a year to analyze the premiums for the selected LoB.",
        label="Year(s) to Analyze",
        default=historical_premiums["Policy Underwriting Year"].unique()[
            historical_premiums["Policy Underwriting Year"].unique() <= current_uwy
        ],
        selection_mode="multi",
    )

filtered_data = historical_premiums[
    (historical_premiums["Reserving Class Code"] == selected_lob)
    & (
        historical_premiums["Policy Underwriting Year"].isin(
            selected_years
            if selected_years
            else historical_premiums["Policy Underwriting Year"].unique()
        )
    )
]

st.dataframe(filtered_data)
st.write("## Premiums Over Time (By Year)")

import plotly.express as px

chart_data = filtered_data.sort_values(
    ["Policy Underwriting Year", "Policy Underwriting Month"]
)

metric = st.segmented_control(
    options=["GGWP", "%"],
    key="selected_metric_control",
    help="Select whether to view absolute values (USD) or relative values (%).",
    label="Metric to Display",
)

st.session_state.selected_metric = "Expected GGWP (USD)"
if metric == "%":
    st.session_state.selected_metric = "monthly_percentage_value"

fig = px.line(
    chart_data,
    x="Policy Underwriting Month",
    y=st.session_state.selected_metric,
    color="Policy Underwriting Year",
    color_discrete_map=color_map,
    title="Expected GWP Over Time (By Year)",
    height=600,
)

st.plotly_chart(fig, use_container_width=True)

st.write("## Premiums Over Time (By Year) - Current UWY Focus")

# Build a dynamic color map
# Every year gets '#D3D3D3' (Light Grey) except the current one
years = chart_data["Policy Underwriting Year"].unique()
focus_color_map = {
    year: "#D3D3D3" if year != current_uwy else "#EF553B"  # Red/Orange for focus
    for year in years
}

# Sort data to ensure the 'Focus' line is drawn last (on top)
# Lines drawn later in the dataframe appear on top of previous lines
chart_data["is_focus"] = chart_data["Policy Underwriting Year"] == current_uwy
chart_data = chart_data.sort_values(["is_focus", "Policy Underwriting Month"])

fig2 = px.line(
    chart_data,
    x="Policy Underwriting Month",
    y="Expected GGWP (USD)",
    color="Policy Underwriting Year",
    color_discrete_map=focus_color_map,
    title=f"Expected GWP Over Time (Focus: {current_uwy})",
    height=600,
)

# Optional: Make the focus line thicker and hide the legend for grey lines
for trace in fig2.data:
    if trace.name == str(current_uwy) or trace.name == current_uwy:
        trace.line.width = 4
    else:
        trace.line.width = 1.5
        trace.opacity = 0.4  # Make grey lines slightly transparent

st.plotly_chart(fig2, use_container_width=True)
