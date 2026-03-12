import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import create_pivot_table, get_quarter, get_sidebar, get_year
from abc import ABC, abstractmethod
from entities.reinsurance_layer import Layer
import plotly.express as px
from services.claims_analyzer_engine import ClaimsAnalyzerEngine as ClaimsAnalyzer
from services.layer_parsing_strategy import (
    LayerParsingStrategy,
    EnergyLayerStrategy,
    SimpleQuotaShareStrategy,
    StandardLayerStrategy,
)
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Reinsurance Structure Analyzer", page_icon="📈", layout="wide"
)

initialize_session_state()

DEBUG_DISABLED = True

st.title("Reinsurance Structure Analyzer")
get_sidebar()

st.write(
    "This page provides a minimalistic view on the reinsurance structure under consideration, allowing to analyze the impact of different claim sizes on the recovery and reinstatement premiums across the layers of the structure. The structure is currently hardcoded to be the Energy sheet of the outward RI excel file, but can be easily extended to other sheets or even other data sources by implementing new parsing strategies (see code below)."
)

reinsurance_structure = pd.read_excel(
    "inputs/ri_outward.xlsx", engine="openpyxl", sheet_name="Energy"
)

st.dataframe(reinsurance_structure)


class ReinsuranceStructureAnalyzer:
    def __init__(self, ri_outward, strategy: LayerParsingStrategy):
        self.ri_outward = ri_outward
        self.strategy = strategy  # Strategy is injected

    def parse_layers(self) -> list[Layer]:
        # The loop remains the same, but the logic is delegated
        if self.ri_outward.empty:
            warning(
                "The reinsurance structure data is empty. Please check the input file."
            )
            return []
        return [
            layer
            for layer in (
                self.strategy.create_layer(row) for _, row in self.ri_outward.iterrows()
            )
            if layer is not None
        ]


df = reinsurance_structure
analyzer = ReinsuranceStructureAnalyzer(df, strategy=EnergyLayerStrategy())
layers = analyzer.parse_layers()


st.markdown("### Layers")

st.markdown("## Gross vs. Net Claim Size Analysis")
st.markdown(
    "Below is an analysis of the recovery and reinstatement premiums across the layers for different claim sizes."
)

st.checkbox("With AAD", key="include_aad", value=True)

claims_list = np.linspace(1000000, 90000000, 100).tolist()

data = []
for claim in claims_list:
    claims_analyzer = ClaimsAnalyzer(layers=layers)
    (
        total_recovery,
        total_reinstatement_premium,
        ri_structure_application_summary,
        final_net_claim,
    ) = claims_analyzer.calculate_single_claim_recovery(
        claim_size=claim,
        include_aad=st.session_state.get("include_aad", True),
    )

    net_before_int_qs = final_net_claim + ri_structure_application_summary.get(
        "internal_qs", {}
    ).get("Recovery", 0)
    # st.write(f"Claim: {claim}, Recovery: {recovery}, Reinstatement Premium: {reinstatement_premium}")
    data.append(
        {
            "claim_amount": claim,
            "recovery": total_recovery,
            "reinstatement_premium": total_reinstatement_premium,
            "net_before_int_qs": net_before_int_qs,
            "net": final_net_claim,
        }
    )

df = pd.DataFrame(data)

fig = px.line(
    df,
    x="claim_amount",
    y=["recovery", "reinstatement_premium", "net_before_int_qs", "net"],
    title="Recovery vs. Reinstatement Premium",
)

st.plotly_chart(fig)

# st.write([layer.__dict__ for layer in layers])

st.slider(
    "Claim",
    key="selected_claim_size",
    min_value=1000000.0,
    max_value=90000000.0,
    value=54000000.0,
    step=10000.0,
    format="%f",
)

# st.write(f"Selected claim size: {st.session_state.get('selected_claim_size', 0).format('%.2f')}")


claim_analyzer = ClaimsAnalyzer(layers=layers)
(
    total_recovery,
    total_reinstatement_premium,
    ri_structure_application_summary,
    final_net_claim,
) = claim_analyzer.calculate_single_claim_recovery(
    claim_size=st.session_state.get("selected_claim_size", 0),
    include_aad=st.session_state.get("include_aad", True),
)


st.write(
    f"Selected Claim Size: {st.session_state.get('selected_claim_size', 0) / 1000000:.1f}m"
)
st.write(f"Total Recovery: {total_recovery / 1000000:.1f}m")
st.write(f"Total Reinstatement Premium: {total_reinstatement_premium / 1000000:.1f}m")

pd.DataFrame(ri_structure_application_summary).T
