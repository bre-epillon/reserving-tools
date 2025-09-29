import numpy as np
import pandas as pd


class PivotDf:
    def __init__(self, df):
        self.df = df

    def _get_index(self, lob):
        return [(i, j) for (i, j) in self.df.columns if j == lob][0]

    def __call__(self, lob, year):
        return float(self.df[self._get_index(lob)].loc[year])


class SubclassUWY:
    def __init__(
        self,
        lob,
        year,
        ultimate_lr_attr,
        ultimate_lr_large_attr,
        incurred_lr_attr,
        incurred_lr_large,
        variance_weighted_credibility=1,
    ):
        self.lob = lob
        self.year = year
        self.ultimate_lr_attr = ultimate_lr_attr
        self.ultimate_lr_large = ultimate_lr_large_attr
        self.incurred_lr_attr = incurred_lr_attr
        self.incurred_lr_large = incurred_lr_large
        self.credibity_factor = variance_weighted_credibility

        self.lr_attr = max(0, self.ultimate_lr_attr - self.incurred_lr_attr)
        self.lr_large = max(
            0, self.ultimate_lr_large - self.incurred_lr_large - self.incurred_lr_attr
        )

        self.mu_log = self.calculate_mu_log()
        self.sigma_log = self.calculate_sigma_log()

        self.simulated_ratios = None  # Placeholder for the generated loss ratios; calculate using self.run_montecarlo()

    def calculate_mu_log(self):
        try:
            mu_log = np.log(
                self.lr_large
                / np.sqrt(1 + self.credibity_factor / (self.lr_large) ** 2)
            )
        except Exception as e:
            print(
                f"Error in calculating mu_log for lob: {self.lob}, year: {self.year}, setting to 0: {e}"
            )
            mu_log = 0
        return mu_log

    def calculate_sigma_log(self):
        try:
            sigma_log = np.sqrt(
                np.log(1 + self.credibity_factor / (self.lr_large) ** 2)
            )
        except Exception as e:
            print(
                f"Error in calculating sigma_log for lob: {self.lob}, year: {self.year}, setting to 0: {e}"
            )
            sigma_log = 0
        return sigma_log

    def run_montecarlo(self, n_samples=10000):
        """Run Monte Carlo simulation to generate samples based on the log-normal distribution."""
        # Ensure mu_log and sigma_log are not zero to avoid division by zero errors
        mu = self.mu_log
        sigma = self.sigma_log

        if mu == sigma == 0:
            print(
                f"Warning: mu_log or sigma_log is zero for {self.lob} in {self.year}. Returning empty samples."
            )
            return np.array([])

        # Generate samples from a log-normal distribution
        simulated_lr_large = np.random.lognormal(mean=mu, sigma=sigma, size=n_samples)
        simulated_lr_attr = np.zeros(
            n_samples
        )  # Assuming attritional LR is zero for simplicity
        try:
            simulated_lr_attr = simulated_lr_large * self.lr_attr / self.lr_large
        except Exception as e:
            print(
                f"Error in calculating simulated attritional LR for {self.lob} in {self.year}: {e}; Returning empty samples."
            )
        self.simulated_ratios = {
            "attr_large": simulated_lr_large,
            "attr": simulated_lr_attr,
        }
        pass

    def __dict__(self):
        return {
            "lob": self.lob,
            "year": self.year,
            "ultimate_lr_attr": self.ultimate_lr_attr,
            "ultimate_lr_large": self.ultimate_lr_large,
            "incurred_lr_attr": self.incurred_lr_attr,
            "incurred_lr_large": self.incurred_lr_large,
            "credibity_factor": self.credibity_factor,
            "lr_attr": self.lr_attr,
            "lr_large": self.lr_large,
            "mu_log": self.mu_log,
            "sigma_log": self.sigma_log,
        }


class SubclassUWYFactory:
    def __init__(
        self,
        premiums_ultimate_df,
        incurred_attr_df: PivotDf,
        incurred_large_df: PivotDf,
        ultimate_lr_data: pd.DataFrame,
        unearned_lr_data: pd.DataFrame,
    ):
        self._years = premiums_ultimate_df.index.tolist()
        self._lobs = premiums_ultimate_df.columns.tolist()

        self.premiums_ultimate_df = premiums_ultimate_df
        self.incurred_attr_df = incurred_attr_df
        self.incurred_large_df = incurred_large_df
        self.ultimate_lr_data = ultimate_lr_data
        self.unearned_lr_data = unearned_lr_data

        self.incurred_lr_attr = self.calculate_incurred_lr_attr()
        self.incurred_lr_large = self.calculate_incurred_lr_large()

    def calculate_incurred_lr_attr(self) -> dict:
        # self.incurred_lr_attr.loc[("ENOFF", 2019)].values[0]
        loss_ratios = []
        for year in self._years:
            for lob in self._lobs:
                # Calculate the incurred loss ratio for each LOB and year
                incurred_attr = self.incurred_attr_df(lob, year)
                premiums_ultimate = self.premiums_ultimate_df.loc[year, lob]

                if premiums_ultimate != 0:
                    incurred_lr_attr = incurred_attr / premiums_ultimate
                else:
                    incurred_lr_attr = np.nan
                loss_ratios.append(
                    {"LOB": lob, "UWY": year, "Incurred LR Attr": incurred_lr_attr}
                )
        return pd.DataFrame(loss_ratios).set_index(["LOB", "UWY"])

    def calculate_incurred_lr_large(self):
        # self.incurred_lr_attr.loc[("ENOFF", 2019)].values[0]
        loss_ratios = []
        for year in self._years:
            for lob in self._lobs:
                # Calculate the incurred loss ratio for each LOB and year
                incurred = self.incurred_large_df(lob, year)
                premiums_ultimate = self.premiums_ultimate_df.loc[year, lob]

                if premiums_ultimate != 0:
                    incurred_lr = incurred / premiums_ultimate
                else:
                    incurred_lr = np.nan
                loss_ratios.append(
                    {"LOB": lob, "UWY": year, "Incurred LR Large": incurred_lr}
                )
        return pd.DataFrame(loss_ratios).set_index(["LOB", "UWY"])

    def create_subclass_uwy(self) -> list[SubclassUWY]:
        subclasses = []
        for lob in self._lobs:
            for year in self._years:
                ultimate_lr_attr = self.ultimate_lr_data.loc[
                    (self.ultimate_lr_data["LOB"] == lob)
                    & (self.ultimate_lr_data["UWY"] == year),
                    "BE LR Attr",
                ].values[0]
                ultimate_lr_large_attr = self.ultimate_lr_data.loc[
                    (self.ultimate_lr_data["LOB"] == lob)
                    & (self.ultimate_lr_data["UWY"] == year),
                    "BE LR Attr+Large",
                ].values[0]
                unearned_std_deviation = self.unearned_lr_data[
                    (self.unearned_lr_data["LOB"] == lob)
                ]["Standard Deviation"].values[0]
                unearned_mean = self.unearned_lr_data[
                    (self.unearned_lr_data["LOB"] == lob)
                ]["Mean"].values[0]
                variance_weighted_credibility = (
                    ultimate_lr_large_attr * unearned_std_deviation / unearned_mean
                ) ** 2
                subclasses.append(
                    SubclassUWY(
                        lob=lob,
                        year=year,
                        ultimate_lr_attr=ultimate_lr_attr,
                        ultimate_lr_large_attr=ultimate_lr_large_attr,
                        incurred_lr_attr=self.incurred_lr_attr.loc[(lob, year)].values[
                            0
                        ],
                        incurred_lr_large=self.incurred_lr_large.loc[
                            (lob, year)
                        ].values[0],
                        variance_weighted_credibility=variance_weighted_credibility,
                    )
                )
        return subclasses
