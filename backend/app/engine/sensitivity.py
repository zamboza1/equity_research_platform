"""
Sensitivity Analysis Engine
Performs 2-way data table analysis (vary two inputs, observe output).
"""
from app.engine.core import ModelGraph, DependencyResolver
from typing import List, Dict
from pydantic import BaseModel
import numpy as np

class SensitivityConfig(BaseModel):
    """Configuration for sensitivity analysis"""
    x_variable: str  # Node ID to vary on X axis
    x_values: List[float]
    y_variable: str  # Node ID to vary on Y axis
    y_values: List[float]
    target_variable: str  # Node ID to observe

class SensitivityResult(BaseModel):
    """2-way sensitivity table results"""
    x_variable: str
    y_variable: str
    target_variable: str
    x_values: List[float]
    y_values: List[float]
    results_matrix: List[List[float]]  # 2D array: results[y_index][x_index]

class SensitivityAnalyzer:
    """Perform sensitivity analysis on model graphs"""

    def __init__(self, base_graph: ModelGraph):
        self.base_graph = base_graph

    def run_2way_analysis(self, config: SensitivityConfig) -> SensitivityResult:
        """
        Run 2-way sensitivity analysis.
        Varies x_variable and y_variable across their ranges,
        observes impact on target_variable.
        """
        ids={n.id for n in self.base_graph.nodes}
        inputs={n.id for n in self.base_graph.nodes if n.type.value in ['INPUT','CONSTANT']}
        if config.target_variable not in ids or config.x_variable not in inputs or config.y_variable not in inputs:
            raise ValueError('Unknown target or non-input sensitivity variable')
        if config.x_variable==config.y_variable: raise ValueError('Sensitivity axes must differ')
        if not 1<=len(config.x_values)<=30 or not 1<=len(config.y_values)<=30: raise ValueError('Sensitivity axes require 1 to 30 values')
        results_matrix = []

        for y_val in config.y_values:
            row = []
            for x_val in config.x_values:
                # Create modified graph with both variables set
                modified_nodes = []
                for node in self.base_graph.nodes:
                    modified_node = node.model_copy()
                    if node.id == config.x_variable:
                        modified_node.value = x_val
                    elif node.id == config.y_variable:
                        modified_node.value = y_val
                    modified_nodes.append(modified_node)

                # Solve
                modified_graph = ModelGraph(nodes=modified_nodes, edges=self.base_graph.edges)
                resolver = DependencyResolver(modified_graph)
                result = resolver.solve()

                # Extract target
                target_value = result.results.get(config.target_variable, 0)
                row.append(target_value)

            results_matrix.append(row)

        return SensitivityResult(
            x_variable=config.x_variable,
            y_variable=config.y_variable,
            target_variable=config.target_variable,
            x_values=config.x_values,
            y_values=config.y_values,
            results_matrix=results_matrix
        )
