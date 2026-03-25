from shared.colored_logging import info, debug, warning
import pandas as pd


class Layer:
    """A clean data object (POPO - Plain Old Python Object)."""

    def __init__(
        self,
        layer_name,
        limit,
        excess,
        rol,
        order,
        aad=0,
        n_reinstatements=0,
        cost_reinstatements=0,
        is_internal_qs=False,
        layer_type="XoL",
        **kwargs,
    ):
        self.layer_name = layer_name
        self.limit = limit
        self.excess = excess
        self.rol = rol
        self.order = order  # reinsurance share
        self.aad = 0 if pd.isna(aad) else aad
        self.n_reinstatements = n_reinstatements
        self.cost_reinstatements = cost_reinstatements
        self.layer_type = layer_type
        self.is_internal_qs = is_internal_qs
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
            raise ValueError(
                "Number of reinstatements must be greater than or equal to 0"
            )
        if self.cost_reinstatements < 0:
            raise ValueError(
                "Cost of reinstatements must be greater than or equal to 0"
            )
        info("Layer {} validated successfully.".format(self.layer_name))

    def calculate_recovery(
        self, gross_claim: float, include_aad: bool = True
    ) -> tuple[float, float]:
        if gross_claim <= 0:
            warning(
                f"Gross claim is {gross_claim}. No recovery or reinstatement premium will be calculated for layer {self.layer_name}."
            )
            return 0, 0

        if self.layer_type == "Proportional":
            # Quota Share: Recovery is a straight % of the remaining claim
            recovery = gross_claim * self.order
            return recovery, 0  # No reinstatement on QS

        effective_aad = self.aad if include_aad else 0
        # XoL logic with AAD consideration

        if effective_aad > 0:
            info(f"AAD of {effective_aad} is being applied to layer {self.layer_name}.")
        else:
            info(f"No AAD is being applied to layer {self.layer_name}.")
        info(
            f"Calculating recovery for layer {self.layer_name} with gross claim {gross_claim}, excess {self.excess}, limit {self.limit}, and order {self.order}."
        )
        # debug(
        #     f"Effective attachment: {effective_attachment} with excess: {self.excess} and AAD: {self.aad}"
        # )
        if include_aad:
            self.aad = max(0, self.aad - max(0, gross_claim - self.excess))

        impacted_amount = min(
            self.limit - effective_aad, max(0, gross_claim - self.excess)
        )
        debug(
            f"Impacted amount: {impacted_amount}, given that claim: {gross_claim}, limit: {self.limit}, and excess: {self.excess} with AAD: {effective_aad}"
        )
        recovery = impacted_amount * self.order

        # Reinstatement Premium = Recovery * RoE
        reinstatement_premium = recovery * self.rol

        return recovery, reinstatement_premium


class EmptyLayer(Layer):
    def __init__(self):
        super().__init__(
            layer_name="Empty Layer",
            limit=0,
            excess=0,
            rol=0,
            order=0,
            aad=0,
            n_reinstatements=0,
            cost_reinstatements=0,
            is_internal_qs=False,
            layer_type="Empty",
        )
