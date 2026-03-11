from abc import ABC, abstractmethod
from entities.reinsurance_layer import Layer
from shared.colored_logging import debug


class LayerParsingStrategy(ABC):
    layer_parsing_strategy_name = ""

    @abstractmethod
    def create_layer(self, row):
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
        # debug(f"Row: {row}")

        return Layer(
            layer_name=row.get("layer_name", None),
            limit=row.get("limit", None),
            excess=row.get("excess", None),
            rol=row.get("rol", None),
            order=row.get("order", None),
            aad=row.get("aad", None),
            n_reinstatements=row.get("n_reinstatements", None),
            cost_reinstatements=row.get("cost_reinstatements", None),
        )


class SimpleQuotaShareStrategy(LayerParsingStrategy):
    def create_layer(self, row):
        # Perhaps Quota Shares don't have attachment points in your data
        return Layer(
            number=row.get("ID", 0),
            layer_type="Quota Share",
            attachment=0,
            limit=row["Total Capacity"],
            share=row["Retention"],
        )
