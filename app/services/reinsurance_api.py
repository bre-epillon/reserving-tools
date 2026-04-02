import pandas as pd
from typing import Dict, Any, Union


class ReinsuranceDataAPI:
    def __init__(self, file_path: str):
        """
        Initializes the API by loading the dataset into memory.
        """
        try:
            if file_path.endswith(".csv"):
                # We use pandas to handle the large file efficiently
                self.df = pd.read_csv(file_path)
            elif file_path.endswith(".xlsx"):
                self.df = pd.read_excel(
                    file_path, engine="openpyxl", sheet_name="Total Data", skiprows=1
                )
            else:
                raise ValueError("Unsupported file format")

            # Basic cleaning: fill NaNs in numeric columns with 0
            # Adjust this based on your actual business rules

        except Exception as e:
            raise ValueError(f"Failed to load reinsurance data from {file_path}: {e}")

    def _format_response(self, data: Any, status_code: int = 200) -> Dict[str, Any]:
        """Utility method to simulate a REST API JSON response."""
        return {"status_code": status_code, "data": data}

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """GET /api/summary - Returns aggregated statistics of the portfolio."""
        summary = {
            "total_policies": len(self.df),
            "total_pipeline_premium": float(self.df["pipeline_premium"].sum()),
            "total_recoverables": float(self.df["recoverable"].sum()),
            "unique_uwys": int(self.df["uwy"].nunique()),
        }
        return self._format_response(summary)

    def get_reinsurance_data(self):
        """GET /api/policies - Returns all policies in the portfolio."""
        return self.df

    def get_policies_number(self) -> Dict[str, Any]:
        """GET /api/policies/number - Returns the number of policies in the portfolio."""
        return self._format_response({"number_of_policies": len(self.df)})

    def get_policies_by_uwy(self, uwy: int) -> Dict[str, Any]:
        """GET /api/policies?uwy={uwy} - Returns all policies for a specific Underwriting Year."""
        filtered_df = self.df[self.df["uwy"] == uwy]

        if filtered_df.empty:
            return self._format_response([], status_code=200)

        # Convert the filtered dataframe to a list of dictionaries
        return self._format_response(filtered_df.to_dict(orient="records"))

    def get_policy_details(self, policy_ref: str) -> Dict[str, Any]:
        """GET /api/policies/{policy_ref} - Returns details for a specific policy."""
        # Ensure policy_ref is treated as a string to avoid type mismatches
        policy = self.df[self.df["Policy reference"] == policy_ref]

        if policy.empty:
            return self._format_response({"error": "Policy not found"}, status_code=404)

        return self._format_response(policy.iloc[0].to_dict())

    def get_top_recoverables(self, limit: int = 5) -> Dict[str, Any]:
        """GET /api/policies/top-recoverables?limit={limit}"""
        top_df = self.df.nlargest(limit, "recoverable")
        return self._format_response(top_df.to_dict(orient="records"))

    def get_policy_premiums(self, policy_ref: str) -> Dict[str, Any]:
        """GET /api/policies/{policy_ref}/premiums - Returns premiums for a specific policy."""
        # Ensure policy_ref is treated as a string to avoid type mismatches

        policy = self.df[self.df["Policy reference"] == policy_ref]

        if policy.empty:
            return self._format_response({"error": "Policy not found"}, status_code=404)

        COLS = [
            "ADDITIONAL PREMIUM",
            "GROSS PREMIUM",
            "RETURN PREMIUM",
            "REINSTATEMENT PREMIUM",
            "BROKERAGE",
        ]

        return self._format_response(policy[COLS].to_dict(orient="records")[0])
