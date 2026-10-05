"""FCFF valuation. Monetary values and diluted shares use millions.

Cash flows occur at year end unless mid-year discounting is selected. The
terminal value is always measured at the final year end. No tax credit is
assumed for operating losses. NWC treatment is explicit. Legacy API inputs treat the ratio as annual cash
investment; the UI uses an operating balance ratio and deducts its change.
"""
from typing import Literal
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

class AdvancedDCFRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    ticker: str = Field(min_length=1, max_length=30)
    current_price: float = Field(gt=0)
    shares_outstanding_m: float = Field(gt=0)
    net_debt_m: float
    start_revenue_m: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    growth_rates: list[float] | None = None
    ebit_margins: list[float] | None = None
    years: int | None = Field(default=None, ge=1, le=30)
    stage_1_years: int = Field(default=5, ge=1, le=20)
    stage_2_years: int = Field(default=5, ge=0, le=20)
    stage_1_growth: float = Field(default=.05, gt=-1, le=5)
    stage_2_growth_start: float = Field(default=.05, gt=-1, le=5)
    stage_2_growth_end: float = Field(default=.02, gt=-1, le=5)
    ebit_margin: float = Field(default=.2, ge=-1, le=1)
    tax_rate: float = Field(ge=0, le=1)
    da_pct: float = Field(ge=0, le=1)
    capex_pct: float = Field(ge=0, le=1)
    nwc_pct: float = Field(ge=-1, le=1)
    nwc_treatment: Literal["balance_ratio", "annual_investment_ratio"] = "annual_investment_ratio"
    start_nwc_m: float | None = None
    wacc: float = Field(gt=0, le=1)
    terminal_growth: float = Field(gt=-1, le=.25)
    terminal_method: Literal["GORDON", "EXIT_MULTIPLE"] = "GORDON"
    exit_multiple: float | None = Field(default=None, gt=0, le=100)
    exit_multiple_basis: Literal["EBIT", "EBITDA"] = "EBIT"
    discount_timing: Literal["year_end", "mid_year"] = "year_end"
    minority_interest_m: float = Field(default=0, ge=0)
    preferred_equity_m: float = Field(default=0, ge=0)
    nonoperating_assets_m: float = Field(default=0, ge=0)
    run_monte_carlo: bool = False
    iterations: int = Field(default=1000, ge=10, le=10000)
    simulation_seed: int | None = Field(default=42, ge=0)
    simulation_wacc_sd: float = Field(default=.005, ge=0, le=1)
    simulation_growth_sd: float = Field(default=.01, ge=0, le=1)

    @model_validator(mode="after")
    def consistent(self):
        if (self.growth_rates is None) != (self.ebit_margins is None):
            raise ValueError("Provide both annual growth rates and EBIT margins")
        if self.growth_rates is not None:
            count = len(self.growth_rates)
            if not 1 <= count <= 30 or len(self.ebit_margins) != count:
                raise ValueError("Annual growth and margin arrays must have the same length, from 1 to 30")
            if self.years is not None and self.years != count:
                raise ValueError("Projection years must match the annual assumptions")
            if any(g <= -1 or g > 5 for g in self.growth_rates):
                raise ValueError("Annual growth must be greater than -100% and at most 500%")
            if any(m < -1 or m > 1 for m in self.ebit_margins):
                raise ValueError("EBIT margins must be between -100% and 100%")
        elif self.stage_1_years + self.stage_2_years > 30:
            raise ValueError("Total forecast cannot exceed 30 years")
        if self.nwc_treatment == "annual_investment_ratio" and self.start_nwc_m is not None:
            raise ValueError("An opening NWC balance requires balance_ratio treatment")
        if self.terminal_method == "GORDON" and self.wacc <= self.terminal_growth:
            raise ValueError("WACC must exceed terminal growth")
        if self.terminal_method == "EXIT_MULTIPLE" and self.exit_multiple is None:
            raise ValueError("Exit multiple is required")
        return self

class DCFYearResult(BaseModel):
    year: int
    revenue: float
    revenue_growth: float
    ebit: float
    nopat: float
    depreciation: float
    capex: float
    nwc: float | None
    change_nwc: float
    fcff: float
    discount_period: float
    pv_fcff: float

class AdvancedDCFResponse(BaseModel):
    forecast: list[DCFYearResult]
    enterprise_value: float
    equity_value: float
    implied_price: float
    current_price: float
    upside: float
    terminal_value: float
    terminal_fcff: float | None
    pv_terminal_value: float
    terminal_value_share_pct: float | None
    method_used: str
    currency: str
    units: str = "Currency millions; shares in millions; per-share values in currency units"
    bridge: dict[str, float]
    warnings: list[str]
    mean_price: float | None = None
    confidence_interval: list[float] | None = None
    simulation_accepted: int | None = None
    simulation_rejected: int | None = None

class AdvancedDCFEngine:
    def __init__(self, request: AdvancedDCFRequest):
        self.req = request

    def calculate(self, custom_wacc=None, custom_g1=None) -> AdvancedDCFResponse:
        req = self.req
        wacc = req.wacc if custom_wacc is None else custom_wacc
        if wacc <= 0 or (req.terminal_method == "GORDON" and wacc <= req.terminal_growth):
            raise ValueError("Discount rate must be positive and exceed perpetual growth")
        if req.growth_rates is not None:
            growth = list(req.growth_rates)
            if custom_g1 is not None:
                growth = [g + custom_g1 - req.stage_1_growth for g in growth]
            margins = req.ebit_margins
        else:
            growth = [req.stage_1_growth if custom_g1 is None else custom_g1] * req.stage_1_years
            growth += [req.stage_2_growth_start + (req.stage_2_growth_end - req.stage_2_growth_start) * (i + 1) / req.stage_2_years for i in range(req.stage_2_years)]
            margins = [req.ebit_margin] * len(growth)
        if any(not np.isfinite(g) or g <= -1 or g > 5 for g in growth):
            raise ValueError("Simulation growth must remain above -100% and at most 500%")
        revenue = req.start_revenue_m
        nwc = req.start_nwc_m if req.start_nwc_m is not None else revenue * req.nwc_pct
        forecast = []
        for year, (g, margin) in enumerate(zip(growth, margins), 1):
            revenue *= 1 + g
            ebit = revenue * margin
            nopat = ebit - max(ebit, 0) * req.tax_rate
            da, capex, new_nwc = revenue * req.da_pct, revenue * req.capex_pct, revenue * req.nwc_pct
            delta_nwc = new_nwc - nwc if req.nwc_treatment == "balance_ratio" else revenue * req.nwc_pct
            fcff = nopat + da - capex - delta_nwc
            timing = year - (.5 if req.discount_timing == "mid_year" else 0)
            forecast.append(DCFYearResult(year=year, revenue=revenue, revenue_growth=g * 100,
                ebit=ebit, nopat=nopat, depreciation=da, capex=capex, nwc=new_nwc if req.nwc_treatment == "balance_ratio" else None,
                change_nwc=delta_nwc, fcff=fcff, discount_period=timing, pv_fcff=fcff / (1+wacc)**timing))
            nwc = new_nwc
        terminal_fcff = None
        if req.terminal_method == "GORDON":
            terminal_revenue = revenue * (1 + req.terminal_growth)
            terminal_ebit = terminal_revenue * margins[-1]
            terminal_nwc_investment = terminal_revenue*req.nwc_pct-nwc if req.nwc_treatment == "balance_ratio" else terminal_revenue*req.nwc_pct
            terminal_fcff = terminal_ebit - max(terminal_ebit, 0)*req.tax_rate + terminal_revenue*(req.da_pct-req.capex_pct) - terminal_nwc_investment
            terminal_value = terminal_fcff / (wacc-req.terminal_growth)
        else:
            metric = forecast[-1].ebit + (forecast[-1].depreciation if req.exit_multiple_basis == "EBITDA" else 0)
            if metric <= 0:
                raise ValueError("Exit multiple requires positive terminal EBIT or EBITDA")
            terminal_value = metric * req.exit_multiple
        pv_terminal = terminal_value / (1+wacc)**len(forecast)
        ev = sum(f.pv_fcff for f in forecast) + pv_terminal
        equity = ev - req.net_debt_m - req.minority_interest_m - req.preferred_equity_m + req.nonoperating_assets_m
        price = equity / req.shares_outstanding_m
        warnings = []
        if terminal_fcff is not None and terminal_fcff <= 0:
            warnings.append("Terminal FCFF is nonpositive; reassess steady-state operating assumptions.")
        share = pv_terminal / ev * 100 if ev else None
        if share is not None and share > 80:
            warnings.append("More than 80% of enterprise value comes from the terminal value.")
        if equity < 0:
            warnings.append("Enterprise value does not cover the claims deducted in the equity bridge.")
        return AdvancedDCFResponse(forecast=forecast, enterprise_value=ev, equity_value=equity,
            implied_price=price, current_price=req.current_price, upside=(price/req.current_price-1)*100,
            terminal_value=terminal_value, terminal_fcff=terminal_fcff, pv_terminal_value=pv_terminal,
            terminal_value_share_pct=share, method_used=req.terminal_method, currency=req.currency,
            bridge={"enterprise_value":ev,"net_debt":-req.net_debt_m,"minority_interest":-req.minority_interest_m,
                    "preferred_equity":-req.preferred_equity_m,"nonoperating_assets":req.nonoperating_assets_m,"equity_value":equity},
            warnings=warnings)

    def run_simulation(self):
        rng = np.random.default_rng(self.req.simulation_seed)
        prices = []
        for _ in range(self.req.iterations):
            try:
                r = self.calculate(custom_wacc=self.req.wacc + rng.normal(0,self.req.simulation_wacc_sd), custom_g1=self.req.stage_1_growth + rng.normal(0,self.req.simulation_growth_sd))
                if np.isfinite(r.implied_price): prices.append(r.implied_price)
            except ValueError:
                continue
        if not prices: raise ValueError("No valid simulation draws; review WACC and growth")
        return {"mean":float(np.mean(prices)),"std":float(np.std(prices)),"p5":float(np.percentile(prices,5)),
                "p95":float(np.percentile(prices,95)),"accepted":len(prices),"rejected":self.req.iterations-len(prices),
                "seed":self.req.simulation_seed,"description":"Scenario distribution, not a statistical confidence interval"}
