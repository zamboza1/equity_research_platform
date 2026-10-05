"""
LBO Model Components
Advanced components for Leveraged Buyout modeling with full customization.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class DebtType(str, Enum):
    REVOLVER = "Revolver"
    TERM_LOAN_A = "Term Loan A"
    TERM_LOAN_B = "Term Loan B"
    MEZZANINE = "Mezzanine"
    SELLER_NOTE = "Seller Note"
    HIGH_YIELD_BOND = "High Yield Bond"

class InterestType(str, Enum):
    FIXED = "Fixed"
    FLOATING = "Floating"
    PIK = "PIK"  # Payment-in-Kind
    CASH_PIK_TOGGLE = "Cash/PIK Toggle"

class DebtTranche(BaseModel):
    """Represents a debt instrument in the capital structure"""
    name: str
    debt_type: DebtType
    principal_amount: float  # millions
    interest_rate: float  # as decimal (e.g., 0.05 = 5%)
    interest_type: InterestType
    spread: Optional[float] = None  # for floating rate (e.g., SOFR + 3.5%)
    amortization_pct: float = 0.0  # % of principal paid annually
    maturity_years: int
    prepayment_penalty: float = 0.0
    commitment_fee: float = 0.0  # for revolvers

class EquityLayer(BaseModel):
    """Represents an equity investment layer"""
    name: str
    amount: float
    ownership_pct: float
    preferred_return: Optional[float] = None  # hurdle rate

class CapitalStructure(BaseModel):
    """Complete capital stack for LBO"""
    debt_tranches: List[DebtTranche]
    equity_layers: List[EquityLayer]
    transaction_fees_pct: float = 0.02  # % of total sources

class OperationalAssumptions(BaseModel):
    """Value creation levers"""
    # Revenue assumptions
    revenue_growth_rates: List[float]  # year-by-year
    price_increase_pct: float = 0.0
    volume_growth_pct: float = 0.0

    # Cost improvements
    headcount_reduction_pct: float = 0.0
    headcount_reduction_year: int = 1
    severance_cost: float = 0.0

    sga_reduction_pct: float = 0.0
    cogs_improvement_pct: float = 0.0

    # Working capital
    dso_reduction_days: int = 0
    dpo_extension_days: int = 0

    # CapEx
    maintenance_capex_pct: float = 0.03  # % of revenue
    growth_capex: float = 0.0

class ExitScenario(BaseModel):
    """Exit valuation assumptions"""
    exit_year: int
    exit_multiple_ebitda: float
    transaction_costs_pct: float = 0.02
    management_bonus_pct: float = 0.0

class ReturnsCalculator:
    """Calculate LBO returns metrics"""

    @staticmethod
    def calculate_irr(cash_flows: List[float], years: List[int]) -> float:
        """
        Calculate Internal Rate of Return using Newton-Raphson method.
        cash_flows: negative for investment, positive for distributions/exit
        """
        # Simplified IRR calculation
        # In production, use numpy.irr or scipy.optimize

        def npv(rate: float) -> float:
            return sum(cf / ((1 + rate) ** year) for cf, year in zip(cash_flows, years))

        # Newton-Raphson iteration
        rate = 0.1  # Initial guess
        for _ in range(100):
            npv_val = npv(rate)
            npv_derivative = sum(-year * cf / ((1 + rate) ** (year + 1))
                               for cf, year in zip(cash_flows, years))
            if abs(npv_derivative) < 1e-10:
                break
            rate = rate - npv_val / npv_derivative
            if abs(npv_val) < 1e-6:
                break

        return rate

    @staticmethod
    def calculate_moic(invested_capital: float, exit_proceeds: float) -> float:
        """Multiple on Invested Capital"""
        return exit_proceeds / invested_capital if invested_capital > 0 else 0

    @staticmethod
    def calculate_waterfall(exit_proceeds: float,
                           debt_remaining: float,
                           equity_layers: List[EquityLayer]) -> Dict[str, float]:
        """
        Calculate cash distribution waterfall
        """
        waterfall = {}
        remaining = exit_proceeds

        # 1. Repay debt
        debt_repayment = min(remaining, debt_remaining)
        waterfall['debt_repayment'] = debt_repayment
        remaining -= debt_repayment

        # 2. Return equity
        total_equity = sum(e.amount for e in equity_layers)
        equity_return = min(remaining, total_equity)
        waterfall['equity_return'] = equity_return
        remaining -= equity_return

        # 3. Preferred returns (simplified)
        # In reality, this would compound year-by-year
        waterfall['preferred_returns'] = 0

        # 4. Remaining split by ownership
        waterfall['residual'] = remaining

        return waterfall

class CovenantTracker(BaseModel):
    """Track financial covenants"""
    max_leverage_ratio: float  # Total Debt / EBITDA
    min_interest_coverage: float  # EBITDA / Interest
    max_capex: Optional[float] = None

    def check_compliance(self, ebitda: float, total_debt: float,
                        interest_expense: float, capex: float) -> Dict[str, bool]:
        """Returns compliance status for each covenant"""
        leverage = total_debt / ebitda if ebitda > 0 else 999
        coverage = ebitda / interest_expense if interest_expense > 0 else 999

        return {
            'leverage_compliant': leverage <= self.max_leverage_ratio,
            'coverage_compliant': coverage >= self.min_interest_coverage,
            'capex_compliant': capex <= self.max_capex if self.max_capex else True,
            'leverage_ratio': leverage,
            'coverage_ratio': coverage
        }
