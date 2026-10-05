"""
Monte Carlo Simulation Engine
Runs probabilistic simulations on the Model Graph to assess risk and uncertainty.
"""
from app.engine.core import ModelGraph, DependencyResolver, Node, NodeType
import numpy as np
import math
from typing import Dict, List
from pydantic import BaseModel

class DistributionConfig(BaseModel):
    """Configuration for a probabilistic input"""
    node_id: str
    distribution: str  # "normal", "uniform", "triangular"
    params: Dict[str, float]  # e.g., {"mean": 0.05, "std": 0.01} for normal

class SimulationResult(BaseModel):
    """Results from Monte Carlo simulation"""
    target_variable: str
    iterations: int
    seed: int
    mean: float
    median: float
    std: float
    percentile_5: float
    percentile_95: float
    percentile_10: float
    percentile_90: float
    histogram: Dict[str, List[float]]  # {"bins": [...], "counts": [...]}

class MonteCarloEngine:
    """Run Monte Carlo simulations on a model graph"""

    def __init__(self, base_graph: ModelGraph, distributions: List[DistributionConfig], iterations: int = 10000, seed: int = 42):
        self.base_graph = base_graph
        self.distributions = distributions
        if not 10 <= iterations <= 10000: raise ValueError("Iterations must be from 10 to 10000")
        if iterations * len(base_graph.nodes) > 200000: raise ValueError("Reduce iterations: a simulation is limited to 200,000 node evaluations")
        if not 0 <= seed <= 4294967295: raise ValueError("Seed must be from 0 to 4294967295")
        if not distributions: raise ValueError("Choose at least one input distribution")
        inputs={n.id for n in base_graph.nodes if n.type in [NodeType.INPUT,NodeType.CONSTANT]}
        if any(d.node_id not in inputs for d in distributions): raise ValueError("Distributions must reference input nodes")
        if len({d.node_id for d in distributions})!=len(distributions): raise ValueError("Duplicate input distributions")
        for distribution in distributions:
            p = distribution.params
            expected = {"normal": {"mean", "std"}, "uniform": {"low", "high"}, "triangular": {"low", "mode", "high"}}.get(distribution.distribution)
            if not expected or set(p) != expected or any(not math.isfinite(v) for v in p.values()):
                raise ValueError("Provide finite parameters for a normal, uniform or triangular distribution")
            if distribution.distribution == "normal" and p["std"] < 0:
                raise ValueError("Standard deviation cannot be negative")
            if distribution.distribution in ["uniform", "triangular"] and p["low"] >= p["high"]:
                raise ValueError("Distribution low must be less than high")
            if distribution.distribution == "triangular" and not p["low"] <= p["mode"] <= p["high"]:
                raise ValueError("Triangular mode must lie between low and high")
        self.iterations = iterations
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def _sample_distribution(self, dist_config: DistributionConfig) -> float:
        """Sample a value from the configured distribution"""
        if dist_config.distribution == "normal":
            return self.rng.normal(
                dist_config.params["mean"],
                dist_config.params["std"]
            )
        elif dist_config.distribution == "uniform":
            return self.rng.uniform(
                dist_config.params["low"],
                dist_config.params["high"]
            )
        elif dist_config.distribution == "triangular":
            return self.rng.triangular(
                dist_config.params["low"],
                dist_config.params["mode"],
                dist_config.params["high"]
            )
        else:
            raise ValueError(f"Unknown distribution: {dist_config.distribution}")

    def run_simulation(self, target_variable: str) -> SimulationResult:
        """
        Run Monte Carlo simulation.

        Args:
            target_variable: The node_id to track across simulations

        Returns:
            SimulationResult with statistics
        """
        if target_variable not in {n.id for n in self.base_graph.nodes}: raise ValueError("Unknown target variable")
        results = []

        for _ in range(self.iterations):
            # Create a copy of the graph with sampled values
            modified_nodes = []

            for node in self.base_graph.nodes:
                # Check if this node has a distribution config
                dist_config = next((d for d in self.distributions if d.node_id == node.id), None)

                if dist_config:
                    # Sample a new value
                    sampled_value = self._sample_distribution(dist_config)
                    modified_node = node.model_copy()
                    modified_node.value = sampled_value
                    modified_nodes.append(modified_node)
                else:
                    modified_nodes.append(node)

            # Solve the graph with the sampled values
            modified_graph = ModelGraph(nodes=modified_nodes, edges=self.base_graph.edges)
            resolver = DependencyResolver(modified_graph)
            calc_result = resolver.solve()

            # Extract the target variable result
            if target_variable in calc_result.results:
                results.append(calc_result.results[target_variable])

        # Calculate statistics
        results_array = np.array(results)

        # Generate histogram
        counts, bins = np.histogram(results_array, bins=30)

        return SimulationResult(
            target_variable=target_variable,
            iterations=self.iterations,
            seed=self.seed,
            mean=float(np.mean(results_array)),
            median=float(np.median(results_array)),
            std=float(np.std(results_array)),
            percentile_5=float(np.percentile(results_array, 5)),
            percentile_95=float(np.percentile(results_array, 95)),
            percentile_10=float(np.percentile(results_array, 10)),
            percentile_90=float(np.percentile(results_array, 90)),
            histogram={
                "bins": [float(b) for b in bins],
                "counts": [int(c) for c in counts]
            }
        )
