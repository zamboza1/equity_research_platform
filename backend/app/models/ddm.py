"""
Dividend Discount Model (DDM) Implementation
Gordon Growth Model for dividend-paying stocks
"""
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional

class DDMInputs(BaseModel):
    """Inputs for Dividend Discount Model"""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    ticker: str
    current_price: float = Field(gt=0)
    current_dividend: float = Field(ge=0)  # Annual dividend per share
    dividend_growth_rate: float = Field(gt=-1, le=.25) #  # Perpetual growth rate
    required_return: float = Field(gt=0, le=1) #  # Cost of equity / discount rate

    # Optional: Multi-stage growth
    high_growth_years: Optional[int] = Field(default=None, ge=1, le=30)
    high_growth_rate: Optional[float] = Field(default=None, gt=-1, le=5)

    @model_validator(mode="after")
    def validate_growth(self):
        if self.required_return <= self.dividend_growth_rate:
            raise ValueError("Required return must exceed stable dividend growth")
        return self

class DDMResult(BaseModel):
    """DDM valuation results"""
    ticker: str
    intrinsic_value_per_share: float
    current_price: float
    upside_downside_pct: float
    dividend_yield: float
    model_type: str  # "gordon_growth" or "multi_stage"

    # Breakdown
    pv_dividends_growth_phase: Optional[float] = None
    terminal_value: float
    assumptions_used: dict

def calculate_ddm_gordon(inputs: DDMInputs) -> DDMResult:
    """
    Gordon Growth Model: V0 = D1 / (r - g)
    where D1 = next year's expected dividend
    """

    # Next year's dividend
    d1 = inputs.current_dividend * (1 + inputs.dividend_growth_rate)

    # Intrinsic value
    if inputs.required_return <= inputs.dividend_growth_rate:
        raise ValueError("Required return must be greater than growth rate")

    intrinsic_value = d1 / (inputs.required_return - inputs.dividend_growth_rate)

    # Upside/downside
    upside_pct = ((intrinsic_value - inputs.current_price) / inputs.current_price) * 100

    # Dividend yield
    div_yield = (inputs.current_dividend / inputs.current_price) * 100

    return DDMResult(
        ticker=inputs.ticker,
        intrinsic_value_per_share=round(intrinsic_value, 2),
        current_price=inputs.current_price,
        upside_downside_pct=round(upside_pct, 2),
        dividend_yield=round(div_yield, 2),
        model_type="gordon_growth",
        terminal_value=round(intrinsic_value, 2),
        assumptions_used={
            "current_dividend": inputs.current_dividend,
            "growth_rate": inputs.dividend_growth_rate,
            "required_return": inputs.required_return,
            "next_year_dividend": round(d1, 2)
        }
    )

def calculate_ddm_multi_stage(inputs: DDMInputs) -> DDMResult:
    """
    Multi-stage DDM: High growth phase → Stable growth phase
    """
    if inputs.high_growth_years is None or inputs.high_growth_rate is None:
        raise ValueError("Multi-stage model requires high_growth_years and high_growth_rate")

    pv_high_growth = 0
    dividend = inputs.current_dividend

    # Phase 1: High growth dividends
    for year in range(1, inputs.high_growth_years + 1):
        dividend = dividend * (1 + inputs.high_growth_rate)
        pv = dividend / ((1 + inputs.required_return) ** year)
        pv_high_growth += pv

    # Phase 2: Terminal value with stable growth
    terminal_dividend = dividend * (1 + inputs.dividend_growth_rate)
    terminal_value = terminal_dividend / (inputs.required_return - inputs.dividend_growth_rate)
    pv_terminal = terminal_value / ((1 + inputs.required_return) ** inputs.high_growth_years)

    intrinsic_value = pv_high_growth + pv_terminal
    upside_pct = ((intrinsic_value - inputs.current_price) / inputs.current_price) * 100
    div_yield = (inputs.current_dividend / inputs.current_price) * 100

    return DDMResult(
        ticker=inputs.ticker,
        intrinsic_value_per_share=round(intrinsic_value, 2),
        current_price=inputs.current_price,
        upside_downside_pct=round(upside_pct, 2),
        dividend_yield=round(div_yield, 2),
        model_type="multi_stage",
        pv_dividends_growth_phase=round(pv_high_growth, 2),
        terminal_value=round(pv_terminal, 2),
        assumptions_used={
            "current_dividend": inputs.current_dividend,
            "high_growth_rate": inputs.high_growth_rate,
            "high_growth_years": inputs.high_growth_years,
            "stable_growth_rate": inputs.dividend_growth_rate,
            "required_return": inputs.required_return
        }
    )
