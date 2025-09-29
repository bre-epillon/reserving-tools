import numpy as np
import pandas as pd
import plotly.express as px


class Visualizer:
    def __init__(self, data):
        self.data = data

    def plot(self):
        # Placeholder for plotting logic
        pass

    def show(self):
        # Placeholder for showing the plot
        pass

    def plot_distribution(self):
        """
        Plot the distribution of the simulated IBNR values.
        Returns a histogram of the values.
        """
        simulated_ibnr_values = np.array(self.data)

        # Create a DataFrame for plotting
        df = pd.DataFrame({"Simulated IBNR Value": simulated_ibnr_values})

        # Plot using Plotly
        fig = px.histogram(
            df,
            x="Simulated IBNR Value",
            title="Distribution of Simulated IBNR Values",
            nbins=50,
            labels={"Simulated IBNR Value": "IBNR Value"},
        )
        return fig

    def plot_cumulative_distribution(self):
        """
        Calculate cumulative distribution from a list of values.
        Returns sorted values and their cumulative probabilities.
        """
        simulated_ibnr_values = np.array(self.data)

        # Sort values for cumulative distribution
        sorted_values = np.sort(simulated_ibnr_values)
        cum_probs = np.arange(1, len(sorted_values) + 1) / len(sorted_values)

        # Create a DataFrame for plotting
        df = pd.DataFrame(
            {"Simulated IBNR Value": sorted_values, "Cumulative Probability": cum_probs}
        )

        # Cut the plot at the 99% percentile
        cutoff_99 = df["Simulated IBNR Value"].quantile(0.99)
        df_cut = df[df["Simulated IBNR Value"] <= cutoff_99]

        # Find the values at 70% and 80% cumulative probability
        value_70 = np.interp(
            0.7, df_cut["Cumulative Probability"], df_cut["Simulated IBNR Value"]
        )
        value_80 = np.interp(
            0.8, df_cut["Cumulative Probability"], df_cut["Simulated IBNR Value"]
        )

        # Plot using Plotly
        fig = px.line(
            df_cut,
            x="Simulated IBNR Value",
            y="Cumulative Probability",
            title="Cumulative Distribution of Simulated IBNR Values (cut at 99%)",
        )

        # Highlight the area between 70% and 80%
        fig.add_vrect(
            x0=value_70,
            x1=value_80,
            fillcolor="LightSalmon",
            opacity=0.5,
            layer="below",
            line_width=0,
            annotation_text="Risk Appetite: 70%-80%",
            annotation_position="top right",
        )
        return fig
