from fastapi import APIRouter, HTTPException
from app.engine.core import ModelGraph, DependencyResolver, CalculationResult
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat
from fastapi import Query

router = APIRouter()


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    overrides: dict[str, FiniteFloat] = Field(default_factory=dict, max_length=200)


class ScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    graph: ModelGraph
    target_variable: str
    scenarios: list[Scenario] = Field(min_length=1, max_length=8)


@router.post("/scenarios")
def compare_scenarios(request: ScenarioRequest):
    try:
        baseline = DependencyResolver(request.graph).solve()
        if request.target_variable not in baseline.results:
            raise ValueError("Unknown target variable")
        names = [s.name.strip() for s in request.scenarios]
        if any(not n for n in names) or len(set(names)) != len(names):
            raise ValueError("Scenario names must be nonempty and unique")
        inputs = {n.id for n in request.graph.nodes if n.type.value in ["INPUT", "CONSTANT"]}
        rows = []
        for scenario in request.scenarios:
            if set(scenario.overrides) - inputs:
                raise ValueError(f"{scenario.name}: overrides must reference input or constant variables")
            graph = request.graph.model_copy(deep=True)
            for node in graph.nodes:
                if node.id in scenario.overrides:
                    node.value = scenario.overrides[node.id]
            try:
                result = DependencyResolver(graph).solve()
            except ValueError as error:
                raise ValueError(f"{scenario.name}: {error}") from error
            value = result.results[request.target_variable]
            rows.append({"name": scenario.name, "overrides": scenario.overrides, "value": value,
                         "change": value - baseline.results[request.target_variable], "results": result.results})
        return {"target_variable": request.target_variable, "baseline": baseline.results[request.target_variable], "scenarios": rows}
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/templates/cash_flow")
def cash_flow_template(years: int = Query(5, ge=1, le=10)):
    nodes = [
        {"id": key, "label": label, "type": "INPUT", "value": value}
        for key, label, value in [
            ("revenue_0", "Opening revenue", 100), ("tax", "Tax rate (decimal)", .25),
            ("da_ratio", "D&A / revenue (decimal)", .03), ("capex_ratio", "CapEx / revenue (decimal)", .04),
            ("nwc_ratio", "Operating NWC / revenue (decimal)", .12), ("discount", "Discount rate (decimal)", .1)]
    ]
    for year in range(1, years + 1):
        nodes.extend([
            {"id": f"growth_{year}", "label": f"Year {year} revenue growth (decimal)", "type": "INPUT", "value": .1},
            {"id": f"margin_{year}", "label": f"Year {year} EBIT margin (decimal)", "type": "INPUT", "value": .2},
        ])
        formulas = [
            ("revenue", "Revenue", f"{{revenue_{year-1}}} * (1 + {{growth_{year}}})"),
            ("ebit", "EBIT", f"{{revenue_{year}}} * {{margin_{year}}}"),
            ("nopat", "NOPAT", f"{{ebit_{year}}} - max({{ebit_{year}}}, 0) * {{tax}}"),
            ("delta_nwc", "Change in operating NWC", f"({{revenue_{year}}} - {{revenue_{year-1}}}) * {{nwc_ratio}}"),
            ("fcff", "Unlevered free cash flow", f"{{nopat_{year}}} + {{revenue_{year}}} * ({{da_ratio}} - {{capex_ratio}}) - {{delta_nwc_{year}}}"),
            ("pv_fcff", "Present value of cash flow", f"{{fcff_{year}}} / (1 + {{discount}}) ** {year}"),
        ]
        nodes.extend({"id": f"{key}_{year}", "label": f"Year {year} {label}", "type": "FORMULA", "formula": formula}
                     for key, label, formula in formulas)
    nodes.append({"id": "forecast_value", "label": "Present value of forecast cash flows", "type": "FORMULA",
                  "formula": " + ".join(f"{{pv_fcff_{year}}}" for year in range(1, years + 1))})
    return {"name": f"{years}-year operating cash flow", "nodes": nodes, "edges": [],
            "notes": "Money uses one consistent unit. Annual growth and EBIT margins are editable; D&A, CapEx and operating NWC use common revenue ratios. Cash taxes apply only to positive EBIT, with no tax-loss carryforwards. Year-end discounting. The output is the present value of explicit forecast cash flows; it excludes terminal value, net debt and other equity claims. Use Valuations for a complete DCF equity valuation."}

@router.post("/solve", response_model=CalculationResult)
async def solve_model(graph_data: ModelGraph):
    """
    Receives a graph definition (nodes + edges), solves dependencies,
    and returns the calculated values for every node.
    """
    try:
        resolver = DependencyResolver(graph_data)
        result = resolver.solve()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Calculation Error: {str(e)}")

@router.get("/templates/dcf")
async def get_dcf_template():
    return {
        "nodes": [
            {"id": "rev_y1", "label": "Revenue Y1", "type": "INPUT", "value": 100, "position": {"x": 0, "y": 0}},
            {"id": "growth_y2", "label": "Growth Y2", "type": "INPUT", "value": 0.10, "position": {"x": 0, "y": 100}},
            {"id": "rev_y2", "label": "Revenue Y2", "type": "FORMULA", "formula": "{rev_y1} * (1 + {growth_y2})", "position": {"x": 200, "y": 50}},
            {"id": "margin", "label": "EBIT Margin", "type": "CONSTANT", "value": 0.25, "position": {"x": 200, "y": 150}},
            {"id": "ebit_y2", "label": "EBIT Y2", "type": "FORMULA", "formula": "{rev_y2} * {margin}", "position": {"x": 400, "y": 100}}
        ],
        "edges": [
            {"source": "rev_y1", "target": "rev_y2"},
            {"source": "growth_y2", "target": "rev_y2"},
            {"source": "rev_y2", "target": "ebit_y2"},
            {"source": "margin", "target": "ebit_y2"}
        ]
    }

@router.get("/templates/ddm")
async def get_ddm_template():
    return {
        "nodes": [
            {"id": "div_y1", "label": "Next Div ($)", "type": "INPUT", "value": 2.50, "position": {"x": 0, "y": 0}},
            {"id": "ke", "label": "Cost of equity (decimal)", "type": "INPUT", "value": 0.08, "position": {"x": 0, "y": 100}},
            {"id": "g", "label": "Growth rate (decimal)", "type": "INPUT", "value": 0.04, "position": {"x": 0, "y": 200}},
            {"id": "ddm_val", "label": "Gordon Value", "type": "FORMULA", "formula": "{div_y1} / ({ke} - {g})", "position": {"x": 250, "y": 100}}
        ],
        "edges": [
            {"source": "div_y1", "target": "ddm_val"},
            {"source": "ke", "target": "ddm_val"},
            {"source": "g", "target": "ddm_val"}
        ]
    }

@router.get("/templates/three_statement")
async def get_three_statement_template():
    return {
        "nodes": [
            {"id": "rev", "label": "Revenue", "type": "INPUT", "value": 500, "position": {"x": 0, "y": 0}},
            {"id": "cogs_pct", "label": "COGS / revenue (decimal)", "type": "INPUT", "value": 0.60, "position": {"x": 0, "y": 100}},
            {"id": "gp", "label": "Gross Profit", "type": "FORMULA", "formula": "{rev} * (1 - {cogs_pct})", "position": {"x": 200, "y": 50}},
            {"id": "opex", "label": "OpEx", "type": "INPUT", "value": 100, "position": {"x": 200, "y": 150}},
            {"id": "ebit", "label": "EBIT", "type": "FORMULA", "formula": "{gp} - {opex}", "position": {"x": 400, "y": 100}}
        ],
        "edges": [
            {"source": "rev", "target": "gp"},
            {"source": "cogs_pct", "target": "gp"},
            {"source": "gp", "target": "ebit"},
            {"source": "opex", "target": "ebit"}
        ]
    }

from app.engine.monte_carlo import MonteCarloEngine, DistributionConfig, SimulationResult

@router.post("/simulate", response_model=SimulationResult)
async def run_monte_carlo(graph_data: ModelGraph, target_variable: str,
                          distributions: list[DistributionConfig], iterations: int = 1000, seed: int = 42):
    """
    Runs Monte Carlo simulation on the model.
    distributions: List of {"node_id": "...", "distribution": "normal", "params": {"mean": ..., "std": ...}}
    """
    try:
        engine = MonteCarloEngine(graph_data, distributions, iterations, seed)
        result = engine.run_simulation(target_variable)
        return result
    except (ValueError,KeyError,TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))

from app.engine.sensitivity import SensitivityAnalyzer, SensitivityConfig, SensitivityResult

@router.post("/sensitivity", response_model=SensitivityResult)
async def run_sensitivity_analysis(graph_data: ModelGraph, config: SensitivityConfig):
    """
    Runs 2-way sensitivity analysis (data table).
    Varies x_variable and y_variable, observes target_variable.
    """
    try:
        analyzer = SensitivityAnalyzer(graph_data)
        result = analyzer.run_2way_analysis(config)
        return result
    except (ValueError,KeyError,TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))

from app.ml.model_validator import get_model_validator

@router.post("/validate")
async def validate_model(graph_data: ModelGraph):
    """
    🤖 AI Agent validates the model for common errors and unrealistic assumptions.
    Returns errors, warnings, and suggestions.
    """
    try:
        # First solve the model to get results
        resolver = DependencyResolver(graph_data)
        result = resolver.solve()

        # Run AI validation
        validator = get_model_validator()
        validation = validator.validate(graph_data, result.results)

        return {
            "validation": validation,
            "calculation_results": result.results
        }
    except (ValueError,KeyError,TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))
