from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import networkx as nx
import math
import ast
import operator
import re

class NodeType(str, Enum):
    INPUT = "INPUT"         # User provides a value (e.g. Revenue Year 1 = 100)
    CONSTANT = "CONSTANT"   # Fixed value (e.g. Tax Rate = 0.21)
    FORMULA = "FORMULA"     # Calculated (e.g. Revenue * Tax Rate)
    SERIES = "SERIES"       # Time-series array

class Node(BaseModel):
    id: str
    label: str
    type: NodeType
    value: Union[float, List[float], None] = None
    formula: Optional[str] = None # e.g. "{Revenue} * {Margin}"
    description: Optional[str] = None
    position: Optional[Dict[str, float]] = None # For UI Canvas (x, y)

class Edge(BaseModel):
    source: str
    target: str

class ModelGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class CalculationResult(BaseModel):
    results: Dict[str, Any]
    steps: List[str] # Execution order logs

class DependencyResolver:
    def __init__(self, graph_data: ModelGraph):
        if not 1 <= len(graph_data.nodes) <= 200 or len(graph_data.edges)>1000:
            raise ValueError("Model must contain 1 to 200 nodes and at most 1000 edges")
        self.nodes = {n.id: n for n in graph_data.nodes}
        if len(self.nodes)!=len(graph_data.nodes): raise ValueError("Duplicate node IDs")
        for edge in graph_data.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes: raise ValueError("Edge references an unknown node")
        for node in graph_data.nodes:
            if node.type == NodeType.FORMULA and not node.formula: raise ValueError("Formula is required")
            if node.type in [NodeType.INPUT,NodeType.CONSTANT] and (not isinstance(node.value,(float,int)) or not math.isfinite(node.value)):
                raise ValueError("Inputs must be finite numbers")
            if node.type == NodeType.SERIES: raise ValueError("Series nodes are not supported; use scalar inputs")
        self.graph = nx.DiGraph()

        # Build NetworkX graph
        for node in graph_data.nodes:
            self.graph.add_node(node.id)

        for edge in graph_data.edges:
            self.graph.add_edge(edge.source, edge.target)
        # Formula references define real dependencies, independent of input order
        # or whether the caller also supplied drawing edges.
        for node in graph_data.nodes:
            if node.type != NodeType.FORMULA:
                continue
            for reference in re.findall(r"\{([^}]+)\}", node.formula or ""):
                if reference not in self.nodes:
                    raise ValueError(f"{node.id}: unknown input {reference}")
                self.graph.add_edge(reference, node.id)

    def _evaluate_formula(self, formula: str, context: Dict[str, Any]) -> Any:
        """
        Safely evaluates a formula string using values from context.
        Supports basic math and numpy-like operations.
        Formula format: "{Revenue} * 1.05"
        """
        if len(formula)>500: raise ValueError("Formula is too long")
        expression = re.sub(r"\{([^}]+)\}", lambda m: repr(context[m.group(1)]) if m.group(1) in context else (_ for _ in ()).throw(ValueError("Unknown input "+m.group(1))), formula)
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError:
            raise ValueError("Invalid formula syntax") from None
        ops = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul, ast.Div:operator.truediv, ast.Pow:operator.pow}
        functions = {"min":min,"max":max,"sum":sum,"abs":abs,"pow":pow,"round":round,
                     "sqrt":math.sqrt,"log":math.log,"exp":math.exp}
        def evaluate(node):
            if isinstance(node,ast.Constant) and type(node.value) in (int,float):
                value = float(node.value)
                if not math.isfinite(value): raise ValueError("Formula must use finite numbers")
                return value
            if isinstance(node,ast.List): return [evaluate(x) for x in node.elts]
            if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
                return evaluate(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
            if isinstance(node,ast.BinOp) and type(node.op) in ops:
                left,right=evaluate(node.left),evaluate(node.right)
                if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                    raise ValueError("Arithmetic operands must be scalar numbers")
                if isinstance(node.op,ast.Pow) and abs(right)>16: raise ValueError("Exponent exceeds limit")
                return ops[type(node.op)](left,right)
            if isinstance(node,ast.Call) and not node.keywords:
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=="math" else None
                if name in functions:
                    args=[evaluate(x) for x in node.args]
                    if name=="pow" and (len(args)!=2 or abs(args[1])>16): raise ValueError("Invalid exponent")
                    # round's second argument is an integer precision, although
                    # formula literals otherwise use bounded floating-point math.
                    if name == "round" and len(args) == 2:
                        if not isinstance(args[1], (int, float)) or not math.isfinite(args[1]) or args[1] != int(args[1]) or abs(args[1]) > 308:
                            raise ValueError("Rounding precision must be an integer between -308 and 308")
                        args[1] = int(args[1])
                    return functions[name](*args)
            raise ValueError("Only arithmetic and approved numeric functions are supported")
        try:
            result=evaluate(tree.body)
            if not isinstance(result,(int,float)) or not math.isfinite(result): raise ValueError("Formula must return a finite number")
            return result
        except (ArithmeticError,TypeError,KeyError,OverflowError) as e:
            raise ValueError("Invalid numeric formula") from e

    def solve(self) -> CalculationResult:
        """
        Topological sort to find calculation order, then evaluate.
        """
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Circular reference detected in model.")

        execution_order = list(nx.topological_sort(self.graph))
        results = {}
        logs = []

        for node_id in execution_order:
            node = self.nodes[node_id]

            if node.type in [NodeType.INPUT, NodeType.CONSTANT]:
                # Just use the provided value
                val = node.value
                results[node_id] = val
                logs.append(f"Set {node.label} = {val}")

            elif node.type == NodeType.FORMULA:
                val = self._evaluate_formula(node.formula, results)
                results[node_id] = val
                logs.append(f"Calc {node.label} = {val}")

        return CalculationResult(results=results, steps=logs)
