import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import create_pivot_table, get_quarter, get_sidebar, get_year
import pandas as pd

st.set_page_config(
    page_title="Reinsurance Structure Analyzer", page_icon="📈", layout="wide"
)

initialize_session_state()

DEBUG_DISABLED = True

st.title("Reinsurance Structure Analyzer")
get_sidebar()

st.write(
    "This page provides a ..."
)

reinsurance_structure = pd.read_excel("inputs/ri_outward.xlsx", engine="openpyxl", sheet_name="Energy")

st.dataframe(reinsurance_structure)

from abc import ABC, abstractmethod

class LayerParsingStrategy(ABC):
    layer_parsing_strategy_name = ""
    @abstractmethod
    def create_layer(self, row):
        pass

class StandardLayerStrategy(LayerParsingStrategy):
    def create_layer(self, row):
        # Specific logic for standard outward RI structures
        return Layer(
            number=row["Layer Number"],
            layer_type=row["Layer Type"],
            attachment=row["Attachment Point"],
            limit=row["Limit"],
            share=row["Reinsurance Share"]
        )

class EnergyLayerStrategy(LayerParsingStrategy):
    layer_parsing_strategy_name = "Energy"
    def create_layer(self, row):
        # Specific logic for standard outward RI structures
        debug(f"Row: {row}")

        return Layer(
            layer_name = row.get("layer_name",None),
            limit = row.get("limit",None),
            excess = row.get("excess",None),
            rol = row.get("rol",None),
            order = row.get("order",None),
            aad = row.get("aad",None),
            n_reinstatements = row.get("n_reinstatements",None),
            cost_reinstatements = row.get("cost_reinstatements",None),
        )
    
class SimpleQuotaShareStrategy(LayerParsingStrategy):
    def create_layer(self, row):
        # Perhaps Quota Shares don't have attachment points in your data
        return Layer(
            number=row.get("ID", 0),
            layer_type="Quota Share",
            attachment=0,
            limit=row["Total Capacity"],
            share=row["Retention"]
        )
    
class Layer:
    """A clean data object (POPO - Plain Old Python Object)."""
    def __init__(self, layer_name, limit, excess, rol, order, aad=0, n_reinstatements=0, cost_reinstatements=0, **kwargs):
        self.layer_name = layer_name
        self.limit = limit
        self.excess = excess
        self.rol = rol
        self.order = order # reinsurance share
        self.aad = 0 if pd.isna(aad) else aad
        self.n_reinstatements = n_reinstatements
        self.cost_reinstatements = cost_reinstatements
        self.validate_layer()

    def validate_layer(self):
        if self.limit <= 0:
            raise ValueError("Limit must be greater than 0")
        if self.order <= 0:
            raise ValueError("Reinsurance Share must be greater than 0")
        if self.order > 1:
            raise ValueError("Reinsurance Share must be less than or equal to 1")
        if self.rol < 0:
            raise ValueError("RoL must be greater than or equal to 0")
        if self.aad < 0:
            raise ValueError("AAD must be greater than or equal to 0")
        if self.n_reinstatements < 0:
            raise ValueError("Number of reinstatements must be greater than or equal to 0")
        if self.cost_reinstatements < 0:
            raise ValueError("Cost of reinstatements must be greater than or equal to 0")
        info("Layer {} validated successfully.".format(self.layer_name))
    
    def calculate_recovery(self, gross_claim:float):
        # Effective attachment point shifts if AAD is active
        effective_attachment = self.excess + self.aad

        debug(f"Effective attachment: {effective_attachment} with excess: {self.excess} and AAD: {self.aad}")
        self.aad = max(0, self.aad - max(0, gross_claim - self.excess))
        
        # Standard Excess of Loss logic: Min(limit, Max(0, Claim - Attachment))
        impacted_amount = max(0, min(self.limit, gross_claim - effective_attachment))
        debug(f"Impacted amount: {impacted_amount}, given that limit: {self.limit}, gross claim: {gross_claim}, and effective attachment: {effective_attachment}")
        recovery = impacted_amount * self.order
        
        # Reinstatement Premium = Recovery * RoE
        reinstatement_premium = recovery * self.rol
        
        return recovery, reinstatement_premium
    
class ReinsuranceStructureAnalyzer:
    def __init__(self, ri_outward, strategy: LayerParsingStrategy):
        self.ri_outward = ri_outward
        self.strategy = strategy  # Strategy is injected

    def parse_layers(self):
        # The loop remains the same, but the logic is delegated
        return [self.strategy.create_layer(row) for _, row in self.ri_outward.iterrows()]

class ClaimsAnalyzer:
    def __init__(self, claim:float=0, layers:list[Layer]=[],lob=None):
        self.claim = claim
        self.reinsurance_layers = layers
        self.Lob = lob
        info(f"Claim: {claim}")
        info(f"Layers: {[layer.layer_name for layer in self.reinsurance_layers]}")
        info("Claims Analyzer initialized.")

    @staticmethod
    def calculate_recovery(layers, claim_size:float) -> tuple[float, float, dict]:
       
        info("Calculating recovery and reinstatement premium for a claim of {}.".format(claim_size))
        total_recovery = 0
        total_reinstatement_premium = 0
        ri_structure_application_summary = {}
        for layer in layers:
            debug(f"Calculating recovery for layer {layer.layer_name}")
            recovery, reinstatement_premium = layer.calculate_recovery(claim_size)
            total_recovery += recovery
            total_reinstatement_premium += reinstatement_premium
            ri_structure_application_summary[layer.layer_name] = {
                **layer.__dict__,
                "Recovery": recovery,
                "Reinstatement Premium": reinstatement_premium
            }
            # debug(f"Layer: {layer.number}, Recovery: {recovery}, Reinstatement Premium: {reinstatement_premium}")

        return total_recovery, total_reinstatement_premium, ri_structure_application_summary

df = reinsurance_structure
analyzer = ReinsuranceStructureAnalyzer(df, strategy=EnergyLayerStrategy())
layers = analyzer.parse_layers()


st.markdown("### Layers")
import numpy as np
claims_list = np.linspace(1000000, 90000000, 100).tolist()

data = []
for claim in claims_list:
    claims_analyzer = ClaimsAnalyzer()
    recovery, reinstatement_premium, _ = claims_analyzer.calculate_recovery(layers=layers, claim_size=claim)
    # st.write(f"Claim: {claim}, Recovery: {recovery}, Reinstatement Premium: {reinstatement_premium}")
    data.append({"claim_amount": claim, "recovery": recovery, "reinstatement_premium": reinstatement_premium, "net":claim - recovery+reinstatement_premium})

import plotly.express as px

df = pd.DataFrame(data)

fig = px.line(df, x="claim_amount", y=["recovery", "reinstatement_premium", "net"], title="Recovery vs. Reinstatement Premium")

st.plotly_chart(fig)

# st.write([layer.__dict__ for layer in layers]) 

st.slider("Claim", key="selected_claim_size", min_value=1000000, max_value=90000000, value=54000000, step=10000, format="%f")

# st.write(f"Selected claim size: {st.session_state.get('selected_claim_size', 0).format('%.2f')}")




claim_analyzer = ClaimsAnalyzer(claim=st.session_state.get("selected_claim_size", 0), layers=layers)
total_recovery, total_reinstatement_premium, ri_structure_application_summary = claim_analyzer.calculate_recovery(layers=layers, claim_size=st.session_state.get("selected_claim_size", 0))

st.write(f"Total Recovery: {total_recovery}")
st.write(f"Total Reinstatement Premium: {total_reinstatement_premium}")

pd.DataFrame(ri_structure_application_summary).T