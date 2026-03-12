from abc import ABC, abstractmethod
from entities.reinsurance_layer import Layer, EmptyLayer
from shared.colored_logging import debug, info


class LayerParsingStrategy(ABC):
    layer_parsing_strategy_name = ""

    @abstractmethod
    def create_layer(self, row) -> Layer:
        pass


class StandardLayerStrategy(LayerParsingStrategy):
    def create_layer(self, row):
        # Specific logic for standard outward RI structures
        return Layer(
            layer_name=row["Layer Number"],
            limit=row["Limit"],
            excess=row["Attachment Point"],
            rol=row["RoL"],
            order=row["Reinsurance Share"],
        )


class EnergyLayerStrategy(LayerParsingStrategy):
    layer_parsing_strategy_name = "Energy"

    def create_layer(self, row):
        # Specific logic for standard outward RI structures
        layer_name = row.get("layer_name", None)

        if layer_name is None:
            debug("Missing 'layer_name' in row, skipping layer creation.")
            return EmptyLayer()

        layer_name = "_".join(
            layer_name.strip().lower().split(" ")
        )  # Normalize layer name
        info(f"Layer name: {layer_name}")
        is_internal_qs = layer_name == "internal_qs"
        if is_internal_qs:
            debug(f"Identified Internal QS layer: {layer_name}")

        return Layer(
            layer_name=layer_name,
            limit=row.get("limit", None),
            excess=row.get("excess", None),
            rol=row.get("rol", None),
            order=row.get("order", None),
            aad=row.get("aad", None),
            n_reinstatements=row.get("n_reinstatements", None),
            cost_reinstatements=row.get("cost_reinstatements", None),
            is_internal_qs=is_internal_qs,
            layer_type=row.get("layer_type", None),
        )


class SimpleQuotaShareStrategy(LayerParsingStrategy):
    def create_layer(self, row):
        # Perhaps Quota Shares don't have attachment points in your data
        return EmptyLayer()
