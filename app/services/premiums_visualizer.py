from shared.constants import LOB, LOB_MAPPING, SUBLOBS, YEARS, formats
import pandas as pd
import plotly.express as px


class PremiumsVisualizer:
    _color_map = {
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

    def __init__(self, data):
        self.data = data
        # self.macro_lob = "Energy"
        # self.display_mode = "standard"

    def get_figure(
        self,
        macro_lob: str,
        display_mode: str = "standard",
        color_map_style: str = "standard",
        current_uwy: int = 2026,
    ):
        if macro_lob:
            filtered_data = self.data[
                (self.data["Reserving Class Code"].isin(LOB_MAPPING[macro_lob]))
            ]
        else:
            filtered_data = self.data

        chart_data = (
            filtered_data.groupby(
                ["Policy Underwriting Year", "Policy Underwriting Month"]
            )["Expected GGWP (USD)"]
            .sum()
            .reset_index()
            .sort_values(["Policy Underwriting Year", "Policy Underwriting Month"])
        )

        # calculate cumulative premiums
        chart_data["Cumulative Premiums"] = 0
        for year in chart_data["Policy Underwriting Year"].unique():
            chart_data["Cumulative Premiums"][
                chart_data["Policy Underwriting Year"] == year
            ] = (
                chart_data["Expected GGWP (USD)"][
                    chart_data["Policy Underwriting Year"] == year
                ]
            ).cumsum()

        if display_mode == "cumulative":
            metric = "Cumulative Premiums"
        else:
            metric = "Expected GGWP (USD)"

        if color_map_style == "focus":
            years = chart_data["Policy Underwriting Year"].unique()
            color_map = {
                year: "#D3D3D3"
                if year != current_uwy
                else "#EF553B"  # Red/Orange for focus
                for year in years
            }

            # Sort data to ensure the 'Focus' line is drawn last (on top)
            # Lines drawn later in the dataframe appear on top of previous lines
            chart_data["is_focus"] = (
                chart_data["Policy Underwriting Year"] == current_uwy
            )
            chart_data = chart_data.sort_values(
                ["is_focus", "Policy Underwriting Month"]
            )
        else:
            color_map = self._color_map

        fig = px.line(
            chart_data,
            x="Policy Underwriting Month",
            y=metric,
            color="Policy Underwriting Year",
            color_discrete_map=color_map,
            title="Expected GWP Over Time (By Year)",
            height=600,
        )

        if color_map_style == "focus":
            # Make the focus line thicker and hide the legend for grey lines
            for trace in fig.data:
                if trace.name == str(current_uwy) or trace.name == current_uwy:
                    trace.line.width = 4
                else:
                    trace.line.width = 1.5
                    trace.opacity = 0.4  # Make grey lines slightly transparent

        return fig
