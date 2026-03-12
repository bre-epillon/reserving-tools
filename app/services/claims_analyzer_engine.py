from shared.colored_logging import info, debug
from entities.reinsurance_layer import Layer


class ClaimsAnalyzerEngine:
    def __init__(self, layers: list[Layer] = [], lob=None):
        # Business Rule: Sort standard layers by attachment, but Internal QS always last
        self.external_qs = [
            layer
            for layer in layers
            if not layer.layer_type == "XoL" and not layer.is_internal_qs
        ]
        self.xol_layers = sorted(
            [layer for layer in layers if layer.layer_type == "XoL"],
            key=lambda layer: layer.excess,
        )
        self.internal_qs = [layer for layer in layers if layer.is_internal_qs]

        self.Lob = lob

    def calculate_single_claim_recovery(
        self, claim_size: float, include_aad: bool = True
    ) -> tuple[float, float, dict, float]:
        total_recovery = 0
        total_reinstatement_premium = 0
        ri_structure_application_summary = {}

        # Step 1: Calculate External QS and XoL in parallel
        # Note: We use 'claim_size' for both because they don't benefit from each other
        for layer in self.external_qs + self.xol_layers:
            rec, ri_prem = layer.calculate_recovery(claim_size, include_aad=include_aad)

            total_recovery += rec
            total_reinstatement_premium += ri_prem
            ri_structure_application_summary[layer.layer_name] = {
                "Type": layer.layer_type,
                "Basis": "Gross Claim",
                "Recovery": rec,
                "RI Premium": ri_prem,
            }

        # 3. Step 2: Calculate Internal QS (Net of all previous recoveries)
        current_net_for_internal = claim_size - total_recovery
        for layer in self.internal_qs:
            rec, _ = layer.calculate_recovery(
                current_net_for_internal, include_aad=include_aad
            )

            total_recovery += rec
            ri_structure_application_summary[layer.layer_name] = {
                "Type": "Internal QS",
                "Basis": "Net of All Outwards",
                "Recovery": rec,
                "RI Premium": 0,
            }

        final_net_claim = claim_size - total_recovery + total_reinstatement_premium
        return (
            total_recovery,
            total_reinstatement_premium,
            ri_structure_application_summary,
            final_net_claim,
        )

    def calculate_multiple_claims_recovery(
        self, claim_sizes: list[float], include_aad: bool = True
    ) -> list[tuple[float, float, dict, float]]:

        results = []
        for claim_size in claim_sizes:
            result = self.calculate_single_claim_recovery(
                claim_size=claim_size, include_aad=include_aad
            )
            results.append(result)

        return results
