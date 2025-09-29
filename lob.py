import numpy as np
import pandas as pd

class LoB:
    def __init__(self, name, input_data, iterations=1000000, seed=1234):
        self.name = name
        self.input_data = input_data
        self.iterations = iterations
        self.seed = seed

        self.summary = self.create_summary()
        self.IBNR_stat = self.input_data["IBNR Stat"][self.name].sum()
        self.reserves_be = self.summary["GClmO"].sum() + self.summary["IBNR BE"].sum()
        self.reserves_stat = self.IBNR_stat + self.summary["GClmO"].sum()
        self.LR_mean = self.summary["GClmU"].sum() / self.summary["GEP"].sum()
        self.LR_var = self.summary["GULR"]**2 * self.summary["GEP"] / self.summary["GEP"].sum() - self.LR_mean**2

        self.mu = self.LR_mean
        self.var = self.LR_var
        self.update_distribution_params(credibility_factors=[1, 1, 1, 1, 1, 1, 1, 1]) # init

        self.simulation_completed = False
        self.lr_sim = None
        self.ibnr_sim = None
        self.reserves_sim = None
        self.reserves_sim_total = None
        self.distr_graph_fig = None

        # self.distr_graph_fig, self.distr_graph_ax = plt.subplots(figsize=(10, 6))
        # plt.close()
    

    def set_iterations(self, iterations):
        self.iterations = iterations
        self.cleanup_simulation()

    def get_summary(self):
        return self.summary
    
    
    def get_simulation_data(self):
        return self.lr_sim, self.ibnr_sim, self.reserves_sim, self.reserves_sim_total
    
    def get_distribution_graph(self):
        return self.distr_graph_fig

    def get_distribution_graph_parameters(self):
        return self.name, self.reserves_sim_total, self.reserves_be, self.reserves_stat, self.iterations


    def create_summary(self):
        df = pd.DataFrame(index=self.input_data["GEP"].index)

        for measure in ["GEP", "GClmP", "GClmO", "IBNR BE"]:
            df[measure] = self.input_data[measure][self.name]
        df["GClmI"] = df["GClmP"] + df["GClmO"]
        df["GClmU"] = df["GClmI"] + df["IBNR BE"]

        df["GULR"] = df["GClmU"] / df["GEP"]
        df.loc[df["GEP"]==0, "GULR"] = 0

        # add log-normal parameters
        df["Credibility Factor"] = 0
        df["Variance assigned"] = 0
        df["lognormal mean"] = 0
        df["lognormal var"] = 0

        return df
    

    def update_distribution_params(self, credibility_factors=None):
        if credibility_factors:
            self.summary["Credibility Factor"] = credibility_factors
    
        valid_rows = self.summary["Credibility Factor"].abs() > 0.001
        self.mu = (self.summary.loc[valid_rows, "GClmU"].sum() / self.summary.loc[valid_rows, "GEP"].sum())
        self.var = ((self.summary.loc[valid_rows, "GULR"]**2 * self.summary.loc[valid_rows, "GEP"]).sum() / 
                self.summary.loc[valid_rows, "GEP"].sum()) - self.mu**2
        
        self.summary["Variance assigned"] = np.maximum(self.var * self.summary["Credibility Factor"], 1e-6)
        self.summary["lognormal mean"] = \
            np.log(self.summary["GULR"] / np.sqrt(1 + (self.summary["Variance assigned"] / self.summary["GULR"]**2)))
        self.summary["lognormal var"] = \
            np.sqrt(np.log(1 + (self.summary["Variance assigned"] / (self.summary["GULR"]**2))))
        self.cleanup_simulation()
    

    def cleanup_simulation(self):
        self.lr_sim = pd.DataFrame(index=range(self.iterations), columns=self.summary.index)
        self.ibnr_sim = pd.DataFrame(index=range(self.iterations), columns=self.summary.index)
        self.reserves_sim = pd.DataFrame(index=range(self.iterations), columns=self.summary.index)
        self.reserves_sim_total = pd.Series(index=range(self.iterations))
        self.simulation_completed = False
    

    def run_simulation(self):
        self.cleanup_simulation() # initialize simulation dataframes or clean up previous runs
        np.random.seed(self.seed + ord(self.name[0]))
        for col in self.summary.index:
            mu = self.summary.loc[col, "lognormal mean"]
            var = self.summary.loc[col, "lognormal var"]
            gep = self.summary.loc[col, "GEP"]
            clmo = self.summary.loc[col, "GClmO"]
            clmi = self.summary.loc[col, "GClmI"]

            self.lr_sim[col] = np.random.lognormal(mean=mu, sigma=var, size=self.iterations)
            self.ibnr_sim[col] = np.maximum(gep * self.lr_sim[col] - clmi, 0)
            self.reserves_sim[col] = self.ibnr_sim[col] + clmo
            self.reserves_sim_total = self.reserves_sim.sum(axis=1)

        self.simulation_completed = True