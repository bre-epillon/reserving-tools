import pandas as pd
from shared.colored_logging import info, warning, error, debug, success


class TransactionsImporter:
    def __init__(self, transactions_data):
        self.data = transactions_data
        self._sanity_checks()
        self._clean_transactions_data()
        debug(
            f"Transactions data shape: {self.data.shape}, columns: {self.data.columns}"
        )

    def _sanity_checks(self) -> None:
        COLS = [
            "LOB",
            "ClaimReference",
            "PolicyReference",
            "UWY",
            "CutOffDate",
            "Measure",
            "value",
        ]
        assert set(COLS).issubset(set(self.data.columns))

    def _clean_transactions_data(self) -> None:
        df = self.data.copy()

        df.drop(columns=["LOB"], inplace=True)
        df.rename(columns={"Final LOB": "LOB"}, inplace=True)

        df["date"] = pd.to_datetime(df["CutOffDate"])

        debug(f"Latest entry found in the data: {df['date'].max()}")
        self.data = df

    def get_last_transaction_date(self):
        # self._clean_transactions_data()
        return self.data["CutOffDate"].max()

    def get_last_quarter(self) -> str:
        return str(self.data["date"].max().to_period("Q"))

    def get_cutoff_date(self):
        # self._clean_transactions_data()
        return self.data["CutOffDate"].min()

    def get_filtered_transactions(self, cutoff_date: str, final_date: str = None):
        if final_date is None:
            final_date = self.get_last_transaction_date()
        pass

    def get_transactions(self):
        # self._clean_transactions_data()
        return self.data

    def get_last_quarter_data(self):
        last_quarter = self.get_last_quarter()
        last_quarter_mask = self.data["date"].dt.to_period("Q") == last_quarter
        return self.data[last_quarter_mask]
