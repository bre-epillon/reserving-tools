from dataclasses import dataclass
from functools import cached_property
from typing import Dict, Optional


@dataclass
class Policy:
    policy_reference: str = None
    gep: float = None
    paid: float = None
    new_lob: str = None

    clm_inc_attr: float = None
    clm_inc_large: float = None
    sibnr: float = None

    @cached_property
    def be_lr_attr(self) -> Optional[float]:
        # Your calculation logic here
        if self.gep and self.paid:
            return self.paid / self.gep
        return None

    @cached_property
    def be_lr_attr_large(self) -> Optional[float]:
        # Your calculation logic here
        if self.clm_inc_large and self.gep:
            return self.clm_inc_large / self.gep
        return None

    @cached_property
    def ibnr_be_large(self) -> Dict[str, Optional[float]]:
        return {
            "initial_ibnr": self._calc_initial_ibnr_large(),
            "negative_ibnr_by_uwy_lob": self._calc_negative_ibnr_large(),
            "weights_for_non_negatives": self._calc_weights_large(),
            "allocation_of_negative_ibnr": self._calc_allocation_large(),
            "final_ibnr": self._calc_final_ibnr_large(),
        }

    @cached_property
    def ibnr_be_attr(self) -> Dict[str, Optional[float]]:
        return {
            "initial_ibnr": self._calc_initial_ibnr_attr(),
            "negative_ibnr_by_uwy_lob": self._calc_negative_ibnr_attr(),
            "weights_for_non_negatives": self._calc_weights_attr(),
            "allocation_of_negative_ibnr": self._calc_allocation_attr(),
            "final_ibnr": self._calc_final_ibnr_attr(),
        }

    # Your calculation helper methods
    def _calc_initial_ibnr_large(self) -> Optional[float]:
        # Complex calculation logic
        return None

    def _calc_initial_ibnr_attr(self) -> Optional[float]:
        # Complex calculation logic
        return None
