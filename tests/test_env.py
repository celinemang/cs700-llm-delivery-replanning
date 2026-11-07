import networkx as nx
import numpy as np
import pandas as pd
import scipy
import statsmodels.api as sm
import yaml
from pathlib import Path


def test_config_loads():
    cfg = yaml.safe_load((Path(__file__).parent.parent / "config.yaml").read_text())
    assert cfg["environment"]["num_nodes"] >= 5
    assert cfg["environment"]["num_deliveries"] == 4
    assert cfg["environment"]["severities"] == [1, 3]


def test_libraries_work():
    g = nx.path_graph(3)
    assert nx.is_connected(g)
    assert np.isclose(scipy.stats.binom.pmf(1, 2, 0.5), 0.5)
    df = pd.DataFrame({"y": [0, 1, 0, 1, 1, 0], "x": [0, 1, 0, 1, 0, 1]})
    assert sm.Logit(df["y"], sm.add_constant(df["x"])).fit(disp=0) is not None
