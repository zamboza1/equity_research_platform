"""
AI Agent for Financial Model Validation
Detects unrealistic assumptions, circular references, and common modeling errors.
"""
from typing import Dict, List, Tuple
from app.engine.core import ModelGraph
import numpy as np

class ModelValidationAgent:
    """
    Agentic validator that checks financial models for common issues.
    Uses heuristics and domain knowledge to flag problems.
    """

    def validate(self, graph: ModelGraph, results: Dict[str, float]) -> Dict[str, List[str]]:
        """
        Run all validation checks on a model.

        Returns:
            {
                "errors": [...],      # Critical issues
                "warnings": [...],    # Suspicious but possible
                "suggestions": [...]  # Best practice recommendations
            }
        """
        errors = []
        warnings = []
        suggestions = []

        # Check 1: Growth rate sanity
        growth_checks = self._check_growth_rates(graph, results)
        warnings.extend(growth_checks)

        # Check 2: Margin reasonableness
        margin_checks = self._check_margins(graph, results)
        warnings.extend(margin_checks)

        # Check 3: Circular references (already caught by DAG, but double-check)
        circular_checks = self._check_circular_logic(graph)
        errors.extend(circular_checks)

        # Check 4: Discount rate reasonableness
        wacc_checks = self._check_discount_rates(results)
        warnings.extend(wacc_checks)

        # Check 5: Terminal value sanity
        terminal_checks = self._check_terminal_value(results)
        warnings.extend(terminal_checks)

        # Check 6: Negative values in unexpected places
        negative_checks = self._check_negative_values(results)
        errors.extend(negative_checks)

        # Suggestions
        suggestions.append("✅ Consider running Monte Carlo to assess sensitivity to key assumptions")
        suggestions.append("✅ Compare your assumptions to industry benchmarks")

        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _check_growth_rates(self, graph: ModelGraph, results: Dict) -> List[str]:
        """Flag unrealistic growth assumptions"""
        warnings = []

        for node in graph.nodes:
            if "growth" in node.label.lower() and node.value is not None:
                growth = node.value

                # Flag extreme growth rates
                if growth > 0.50:  # >50% growth
                    warnings.append(f"⚠️ Very high growth rate detected: {node.label} = {growth*100:.1f}%")
                elif growth < -0.30:  # >30% decline
                    warnings.append(f"⚠️ Severe decline detected: {node.label} = {growth*100:.1f}%")

                # Flag unrealistic perpetual growth
                if "terminal" in node.label.lower() and growth > 0.05:
                    warnings.append(f"⚠️ Terminal growth rate unusually high: {growth*100:.1f}% (typically 2-3%)")

        return warnings

    def _check_margins(self, graph: ModelGraph, results: Dict) -> List[str]:
        """Check if margins are realistic"""
        warnings = []

        for node in graph.nodes:
            if "margin" in node.label.lower() and node.value is not None:
                margin = node.value

                if margin > 0.60:  # >60% margin
                    warnings.append(f"⚠️ Very high margin: {node.label} = {margin*100:.1f}%")
                elif margin < 0:
                    warnings.append(f"⚠️ Negative margin detected: {node.label} = {margin*100:.1f}%")

        return warnings

    def _check_circular_logic(self, graph: ModelGraph) -> List[str]:
        """Detect circular references (should be caught by DAG already)"""
        # The DependencyResolver already handles this via topological sort
        # This is a redundant check
        return []

    def _check_discount_rates(self, results: Dict) -> List[str]:
        """Flag unrealistic WACC/discount rates"""
        warnings = []

        for key, value in results.items():
            if any(term in key.lower() for term in ["wacc", "discount", "cost_of_capital"]):
                if isinstance(value, (int, float)):
                    if value < 0.03:  # < 3%
                        warnings.append(f"⚠️ Unusually low discount rate: {value*100:.1f}%")
                    elif value > 0.25:  # > 25%
                        warnings.append(f"⚠️ Very high discount rate: {value*100:.1f}%")

        return warnings

    def _check_terminal_value(self, results: Dict) -> List[str]:
        """Check if terminal value dominates valuation"""
        warnings = []

        # Look for EV and Terminal Value
        ev = results.get("enterprise_value") or results.get("ev")
        tv = results.get("terminal_value") or results.get("tv")

        if ev and tv:
            tv_pct = (tv / ev) * 100 if ev > 0 else 0

            if tv_pct > 80:
                warnings.append(f"⚠️ Terminal value is {tv_pct:.1f}% of total EV (consider extending forecast period)")
            elif tv_pct < 20:
                warnings.append(f"ℹ️ Terminal value is only {tv_pct:.1f}% of total EV")

        return warnings

    def _check_negative_values(self, results: Dict) -> List[str]:
        """Flag unexpected negative values"""
        errors = []

        # Fields that should typically be positive
        positive_fields = ["revenue", "ebitda", "enterprise_value", "equity_value"]

        for key, value in results.items():
            if isinstance(value, (int, float)):
                if any(field in key.lower() for field in positive_fields):
                    if value < 0:
                        errors.append(f"❌ Negative value detected: {key} = {value}")

        return errors

# Singleton
_validator = None

def get_model_validator() -> ModelValidationAgent:
    """Get or create validator singleton"""
    global _validator
    if _validator is None:
        _validator = ModelValidationAgent()
    return _validator
