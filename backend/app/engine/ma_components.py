"""
M&A (Mergers & Acquisitions) Components
Advanced components for M&A modeling with synergy tracking and accretion/dilution analysis.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class SynergyType(str, Enum):
    REVENUE = "Revenue"
    COST = "Cost"
    FINANCIAL = "Financial"

class Synergy(BaseModel):
    """Represents a synergy opportunity"""
    name: str
    synergy_type: SynergyType
    annual_value: float  # millions
    realization_year: int  # Year when fully realized
    ramp_up_years: int = 1  # Years to reach full run-rate
    one_time_cost: float = 0.0  # Cost to achieve
    probability: float = 1.0  # 0-1, for risk-adjusted scenarios

class PurchasePriceAllocation(BaseModel):
    """Purchase accounting allocation"""
    enterprise_value: float
    tangible_assets_fmv: float
    intangible_assets: Dict[str, float]  # {"customer_relationships": 50, "technology": 30}
    goodwill: float  # Calculated residual
    deferred_tax_liability: float = 0.0

    @classmethod
    def calculate(cls, enterprise_value: float,
                  tangible_assets_fmv: float,
                  intangible_assets: Dict[str, float],
                  tax_rate: float = 0.21):
        """Auto-calculate goodwill and DTL"""
        total_intangibles = sum(intangible_assets.values())

        # Deferred tax liability on intangibles (simplified)
        dtl = total_intangibles * tax_rate

        # Goodwill = EV - Tangible - Intangible + DTL
        goodwill = enterprise_value - tangible_assets_fmv - total_intangibles + dtl

        return cls(
            enterprise_value=enterprise_value,
            tangible_assets_fmv=tangible_assets_fmv,
            intangible_assets=intangible_assets,
            goodwill=goodwill,
            deferred_tax_liability=dtl
        )

class AccretionDilutionAnalysis(BaseModel):
    """EPS accretion/dilution calculator"""
    acquirer_eps_standalone: float
    target_earnings: float
    synergies_realized: float  # First year synergies
    one_time_costs: float
    interest_expense_increase: float  # From new debt
    amortization_expense: float  # From intangibles
    additional_shares_issued: float = 0  # For stock deals
    acquirer_shares_outstanding: float

    def calculate_pro_forma_eps(self) -> Dict[str, float]:
        """Calculate combined EPS"""
        # Pro forma earnings
        pro_forma_earnings = (
            (self.acquirer_eps_standalone * self.acquirer_shares_outstanding)  # Acquirer earnings
            + self.target_earnings
            + self.synergies_realized
            - self.one_time_costs
            - self.interest_expense_increase
            - self.amortization_expense
        )

        # Pro forma shares
        pro_forma_shares = self.acquirer_shares_outstanding + self.additional_shares_issued

        # Pro forma EPS
        pro_forma_eps = pro_forma_earnings / pro_forma_shares if pro_forma_shares > 0 else 0

        # Accretion/Dilution
        accretion_pct = ((pro_forma_eps - self.acquirer_eps_standalone) /
                        self.acquirer_eps_standalone * 100) if self.acquirer_eps_standalone > 0 else 0

        return {
            "pro_forma_earnings": pro_forma_earnings,
            "pro_forma_shares": pro_forma_shares,
            "pro_forma_eps": pro_forma_eps,
            "accretion_pct": accretion_pct,
            "is_accretive": accretion_pct > 0
        }

class SynergySchedule(BaseModel):
    """Track synergy realization over time"""
    synergies: List[Synergy]

    def get_annual_synergy_value(self, year: int) -> Dict[str, float]:
        """Calculate synergy value for a given year"""
        revenue_synergies = 0
        cost_synergies = 0
        financial_synergies = 0
        one_time_costs = 0

        for synergy in self.synergies:
            if year <= synergy.realization_year:
                # Ramp-up logic
                ramp_factor = min(1.0, (year - 1) / synergy.ramp_up_years) if synergy.ramp_up_years > 0 else 1.0
                realized_value = synergy.annual_value * ramp_factor * synergy.probability

                if synergy.synergy_type == SynergyType.REVENUE:
                    revenue_synergies += realized_value
                elif synergy.synergy_type == SynergyType.COST:
                    cost_synergies += realized_value
                elif synergy.synergy_type == SynergyType.FINANCIAL:
                    financial_synergies += realized_value

                # One-time costs in realization year
                if year == synergy.realization_year:
                    one_time_costs += synergy.one_time_cost

        return {
            "revenue_synergies": revenue_synergies,
            "cost_synergies": cost_synergies,
            "financial_synergies": financial_synergies,
            "total_synergies": revenue_synergies + cost_synergies + financial_synergies,
            "one_time_costs": one_time_costs
        }

class MADealStructure(BaseModel):
    """Complete M&A deal structure"""
    enterprise_value: float
    cash_consideration: float
    stock_consideration: float
    new_debt: float
    net_debt_assumed: float

    purchase_price_allocation: PurchasePriceAllocation
    synergy_schedule: SynergySchedule

    def calculate_sources_and_uses(self) -> Dict[str, Dict[str, float]]:
        """Generate sources & uses table"""
        sources = {
            "Cash": self.cash_consideration,
            "Stock": self.stock_consideration,
            "New Debt": self.new_debt,
            "Total Sources": self.cash_consideration + self.stock_consideration + self.new_debt
        }

        uses = {
            "Equity Purchase": self.enterprise_value - self.net_debt_assumed,
            "Refinance Target Debt": self.net_debt_assumed,
            "Transaction Fees": self.enterprise_value * 0.02,  # Assume 2%
            "Total Uses": self.enterprise_value + (self.enterprise_value * 0.02)
        }

        return {"sources": sources, "uses": uses}
