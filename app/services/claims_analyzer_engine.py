from shared.colored_logging import info, debug
from entities.reinsurance_layer import Layer


class ClaimsAnalyzerEngine:
    def __init__(self, layers: list[Layer] = [], lob=None):
        self.reinsurance_layers = layers
        self.Lob = lob
        # info(f"Claim: {claim}")
        # info(f"Layers: {[layer.layer_name for layer in self.reinsurance_layers]}")
        # info("Claims Analyzer initialized.")

    def calculate_single_claim_recovery(
        self, claim_size: float, include_aad: bool = True
    ) -> tuple[float, float, dict]:

        # info(
        #     "Calculating recovery and reinstatement premium for a claim of {}.".format(
        #         claim_size
        #     )
        # )
        total_recovery = 0
        total_reinstatement_premium = 0
        ri_structure_application_summary = {}
        for layer in self.reinsurance_layers:
            # debug(f"Calculating recovery for layer {layer.layer_name}")
            recovery, reinstatement_premium = layer.calculate_recovery(
                claim_size, include_aad=include_aad
            )
            total_recovery += recovery
            total_reinstatement_premium += reinstatement_premium
            ri_structure_application_summary[layer.layer_name] = {
                **layer.__dict__,
                "Recovery": recovery,
                "Reinstatement Premium": reinstatement_premium,
            }
            # debug(f"Layer: {layer.number}, Recovery: {recovery}, Reinstatement Premium: {reinstatement_premium}")

        return (
            total_recovery,
            total_reinstatement_premium,
            ri_structure_application_summary,
        )

    def calculate_multiple_claims_recovery(
        self, claim_sizes: list[float], include_aad: bool = True
    ) -> list[tuple[float, float, dict]]:

        results = []
        for claim_size in claim_sizes:
            result = self.calculate_single_claim_recovery(
                claim_size=claim_size, include_aad=include_aad
            )
            results.append(result)

        return results
