from dataclasses import dataclass
import pandas as pd
from typing import Iterator
from entity_lob.subLoB import SubclassUWY


@dataclass
class IBNR_BE_earned:
    year: int
    lob: str
    gep: float
    incurred: float

    _type: str

    def __post_init__(self):
        if self._type not in ("attr", "large"):
            raise ValueError(f"_type must be 'attr' or 'large', got {self._type}")

    def calculate_ibnr(self, loss_ratio: float) -> float:
        """Calculate the IBNR based on the incurred amount and loss ratio."""
        if loss_ratio <= 0:
            raise ValueError("Loss ratio must be greater than zero")
        return self.incurred * loss_ratio


class IBNR_BE_earned_Fabric:
    def __init__(
        self,
        ibnr_data: pd.DataFrame,
        loss_ratios: dict[str, list[float]],
    ):
        self.ibnr_data = ibnr_data
        self.loss_ratios = loss_ratios

        self._be = (
            ibnr_data.pivot_table(
                index=["New LOB", "UWY"],
                values=["gep", "ClmI Attr", "ClmI Large", "SIBNR"],
                aggfunc="sum",
            )
            .reset_index()
            .rename(
                columns={
                    "New LOB": "lob",
                    "ClmI Attr": "ClmI_Attr",
                    "ClmI Large": "ClmI_Large",
                },
            )
        )

        self._years = self.ibnr_data["UWY"].unique()
        self._lobs = self.ibnr_data["New LOB"].unique()

        # self._run_sanity_checks()

    def _run_sanity_checks(self):
        if not isinstance(self.ibnr_data, pd.DataFrame):
            raise TypeError("ibnr_data must be a pandas DataFrame")
        if not isinstance(self.loss_ratios, list):
            raise TypeError("loss_ratios must be a list of SubclassUWY objects")
        if not all(isinstance(lr, SubclassUWY) for lr in self.loss_ratios):
            raise TypeError("All items in loss_ratios must be SubclassUWY instances")
        if not all(year in self._years for year in self.ibnr_data["UWY"].unique()):
            raise ValueError("Years in ibnr_data do not match the expected years")
        if not all(lob in self._lobs for lob in self.ibnr_data["New LOB"].unique()):
            raise ValueError("LOBs in ibnr_data do not match the expected LOBs")
        if not len(self.pol_ref) == len(self.ibnr_data.shape[0]):
            raise ValueError("Policy references in ibnr_data are not unique")

    def get_lr_simulation_n(self, simulation_n: int) -> tuple[dict, dict]:
        """Get the loss ratios for a specific simulation number."""
        attr_large_lr = {
            f"{lob_year}": item["attr_large"][simulation_n]
            for lob_year, item in self.loss_ratios.items()
        }
        attr_lr = {
            f"{lob_year}": item["attr"][simulation_n]
            for lob_year, item in self.loss_ratios.items()
        }
        return (attr_lr, attr_large_lr)

    def calculate_total_ibnr_be(self, simulation_n: int = 0) -> list[IBNR_BE_earned]:
        """Calculate the total IBNR for a specific simulation number."""
        if simulation_n < 0 or simulation_n >= len(
            self.loss_ratios["ENOFF_2024"]["attr_large"]
        ):  # Assuming all classes have the same number of samples as `ENOFF_2024`
            raise ValueError(
                f"Simulation number must be between 0 and {len(self.loss_ratios[0].samples) - 1}, got {simulation_n}"
            )

        attr_lr, attr_large_lr = self.get_lr_simulation_n(simulation_n)
        df = self._be

        df["loss_ratio_large"] = df.apply(
            lambda row: attr_large_lr.get(f"{row['lob']}_{int(row['UWY'])}", 0),
            axis=1,
        ).fillna(0)
        df["loss_ratio_attr"] = df.apply(
            lambda row: attr_lr.get(f"{row['lob']}_{int(row['UWY'])}", 0),
            axis=1,
        ).fillna(0)
        df["ibnr_large"] = df.apply(
            lambda row: max(
                0,
                row["gep"] * (row["loss_ratio_large"] - row["loss_ratio_attr"])
                - row["ClmI_Large"],
            ),
            axis=1,
        )
        df["ibnr_attr"] = df.apply(
            lambda row: max(0, row["gep"] * row["loss_ratio_attr"] - row["ClmI_Attr"]),
            axis=1,
        )
        df["final_ibnr"] = df.apply(
            lambda row: row["ibnr_attr"] + row["ibnr_large"] + row["SIBNR"], axis=1
        )
        return df

    def get_total_ibnr_be_by_simulation(self, simulation_n: int = 0) -> float:
        """Get the total IBNR for a specific simulation number."""
        df = self.calculate_total_ibnr_be(simulation_n)
        return df["final_ibnr"].sum()

    def iter_all_simulated_ibnr_be(self, simulation_n: int = 10) -> Iterator[float]:
        """Get all simulated IBNR BE data."""
        for i in range(simulation_n):
            yield self.get_total_ibnr_be_by_simulation(simulation_n=i)

    def get_all_simulated_ibnr_be_by_lob(self, simulation_n: int = 10) -> pd.DataFrame:
        """Get all simulated IBNR BE data as a pandas DataFrame with the LoB_year as index."""
        dfs = []
        for i in range(simulation_n):
            df = self.calculate_total_ibnr_be(simulation_n=i)
            df = df[["lob", "UWY", "final_ibnr"]].groupby(["lob", "UWY"]).agg(list)
            df = df.rename(columns={"final_ibnr": f"sim_{i}"})
            dfs.append(df)
        return pd.concat(dfs, axis=1).reset_index().set_index(["lob", "UWY"])
