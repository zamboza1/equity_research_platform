"""
3-Statement Financial Model Engine
Handles Income Statement, Balance Sheet, and Cash Flow Statement
with circular reference resolution and working capital drivers.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel as PydanticBaseModel, ConfigDict
import math

class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
from decimal import Decimal, getcontext
import logging

# Set decimal precision for financial calculations
getcontext().prec = 28

logger = logging.getLogger(__name__)

class WorkingCapitalDrivers(BaseModel):
    """Working capital assumptions (now as % of revenue/COGS)"""
    ar_pct_revenue: float = 0.12  # Accounts Receivable as % of Revenue
    inventory_pct_cogs: float = 0.15 # Inventory as % of COGS
    ap_pct_cogs: float = 0.10 # Accounts Payable as % of COGS
    accrued_liabilities_pct_revenue: float = 0.05
    days_sales_outstanding: float | None = None
    days_inventory_outstanding: float | None = None
    days_payable_outstanding: float | None = None
    minimum_cash_balance: float = 50000

class OperatingAssumptions(BaseModel):
    """Operating assumptions for projections"""
    revenue_growth_rates: List[float]  # Annual growth rates
    cogs_percent_revenue: List[float]  # COGS as % of revenue
    opex_fixed: float = 0  # Fixed operating expenses
    opex_variable_pct: float = 0.15  # Variable opex as % of revenue
    tax_rate: float = 0.21

class CapexAssumptions(BaseModel):
    """Capital expenditure assumptions"""
    maintenance_capex_pct: float = 0.03  # % of revenue
    growth_capex: List[float] = []  # Discretionary capex by year
    depreciation_method: str = "straight_line" # "straight_line", "double_declining", "units_of_production"
    asset_life_years: int = 10
    salvage_value_pct: float = 0.05

class FinancingAssumptions(BaseModel):
    """Financing assumptions with debt schedule basics"""
    debt_interest_rate: float = 0.05
    amortization_pct: float = 0.05 # Annual mandatory repayment
    target_cash_balance: float = 100000
    dividend_payout_ratio: float = 0.30
    revolver_capacity: float = 500000
    covenant_min_interest_coverage: float = 3.0

class HistoricalPeriod(BaseModel):
    """Historical financial data for one period"""
    period: str
    revenue: float
    cogs: float
    operating_expenses: float
    depreciation: float
    interest_expense: float
    tax_expense: float
    net_income: float

    # Balance Sheet
    cash: float
    accounts_receivable: float
    inventory: float
    ppe_net: float
    accrued_liabilities: float = 0
    total_assets: float

    accounts_payable: float
    short_term_debt: float
    long_term_debt: float
    total_liabilities: float
    retained_earnings: float
    total_equity: float

    # Cash Flow
    operating_cash_flow: float
    capex: float
    financing_cash_flow: float

class ProjectedPeriod(BaseModel):
    """Projected financials for one period"""
    period: str

    # Income Statement
    revenue: Decimal
    cogs: Decimal
    gross_profit: Decimal
    operating_expenses: Decimal
    ebitda: Decimal
    depreciation: Decimal
    ebit: Decimal
    interest_expense: Decimal
    ebt: Decimal
    tax_expense: Decimal
    net_income: Decimal

    # Balance Sheet
    cash: Decimal
    accounts_receivable: Decimal
    inventory: Decimal
    current_assets: Decimal
    ppe_gross: Decimal
    accumulated_depreciation: Decimal
    ppe_net: Decimal
    total_assets: Decimal

    accounts_payable: Decimal
    short_term_debt: Decimal
    current_liabilities: Decimal
    long_term_debt: Decimal
    total_liabilities: Decimal
    common_stock: Decimal
    retained_earnings: Decimal
    total_equity: Decimal

    # Cash Flow
    net_income_cf: Decimal
    depreciation_cf: Decimal
    change_in_ar: Decimal
    change_in_inventory: Decimal
    change_in_ap: Decimal
    operating_cash_flow: Decimal
    capex: Decimal
    investing_cash_flow: Decimal
    debt_issuance: Decimal
    debt_repayment: Decimal
    dividends: Decimal
    financing_cash_flow: Decimal
    net_cash_change: Decimal
    beginning_cash: Decimal
    accrued_liabilities: Decimal
    change_in_accrued: Decimal
    other_assets: Decimal
    other_liabilities: Decimal
    unlevered_fcf: Decimal


def D(value):
    return Decimal(str(value))

class ThreeStatementModel:
    """Annual projection with average-debt interest and a bounded revolver.

    Opening net PP&E is treated as the remaining depreciable cost over the
    specified life. New capex uses a half-year depreciation convention.
    Residual opening assets and liabilities are carried without growth.
    """
    def __init__(self, historical_base, operating_assumptions, wc_drivers,
                 capex_assumptions, financing_assumptions, projection_years=5):
        self.base, self.op, self.wc = historical_base, operating_assumptions, wc_drivers
        self.cap, self.fin, self.years = capex_assumptions, financing_assumptions, projection_years
        if not 1 <= self.years <= 30: raise ValueError("Projection years must be between 1 and 30")
        if len(self.op.revenue_growth_rates) != self.years or len(self.op.cogs_percent_revenue) != self.years:
            raise ValueError("Growth and COGS arrays must match projection years")
        if any(g <= -1 for g in self.op.revenue_growth_rates): raise ValueError("Growth must exceed -100%")
        percentages = [*self.op.cogs_percent_revenue, self.op.opex_variable_pct, self.op.tax_rate,
            self.wc.ar_pct_revenue, self.wc.inventory_pct_cogs, self.wc.ap_pct_cogs,
            self.wc.accrued_liabilities_pct_revenue, self.cap.maintenance_capex_pct,
            self.cap.salvage_value_pct, self.fin.amortization_pct, self.fin.dividend_payout_ratio,
            self.fin.debt_interest_rate]
        if any(not 0 <= p <= 1 for p in percentages): raise ValueError("Ratios must be between zero and one")
        if self.cap.depreciation_method not in ("straight_line", "double_declining"):
            raise ValueError("Supported depreciation methods: straight_line, double_declining")
        if not 1 <= self.cap.asset_life_years <= 100: raise ValueError("Asset life must be from 1 to 100 years")
        if self.cap.growth_capex and len(self.cap.growth_capex) != self.years:
            raise ValueError("Growth capex must be empty or match projection years")
        nonnegative = [self.op.opex_fixed, self.wc.minimum_cash_balance, self.fin.target_cash_balance,
            self.fin.revolver_capacity, *self.cap.growth_capex]
        if any(v < 0 for v in nonnegative): raise ValueError("Cash balances, expenses, capex and capacity cannot be negative")
        for days in [self.wc.days_sales_outstanding, self.wc.days_inventory_outstanding, self.wc.days_payable_outstanding]:
            if days is not None and not 0 <= days <= 730: raise ValueError("Working capital days must be from zero to 730")
        if abs(self.base.total_assets-self.base.total_liabilities-self.base.total_equity) > .01:
            raise ValueError("Opening balance sheet does not balance")
        for key in ['revenue','cash','accounts_receivable','inventory','ppe_net','accounts_payable','short_term_debt','long_term_debt','accrued_liabilities']:
            if getattr(self.base,key) < 0: raise ValueError(f"Opening {key} cannot be negative")
        self.other_assets = D(self.base.total_assets)-sum(map(D,[self.base.cash,self.base.accounts_receivable,self.base.inventory,self.base.ppe_net]))
        self.other_liabilities = D(self.base.total_liabilities)-sum(map(D,[self.base.accounts_payable,self.base.short_term_debt,self.base.long_term_debt,self.base.accrued_liabilities]))
        if min(self.other_assets,self.other_liabilities) < D('-.01'):
            raise ValueError("Opening component balances exceed reported totals")
        if self.base.short_term_debt > self.fin.revolver_capacity:
            raise ValueError("Opening short-term debt exceeds revolver capacity")

    def project_financials(self):
        projections = []
        previous = None
        for index in range(self.years):
            interest = D(self.base.short_term_debt+self.base.long_term_debt)*D(self.fin.debt_interest_rate)
            for _ in range(200):
                period, recalculated = self._period(index,previous,interest)
                if abs(recalculated-interest) < D('0.0000001'): break
                interest = (interest+recalculated)/2
            else: raise ValueError("Average-debt interest did not converge")
            if not all(self.validate_statements(period).values()):
                raise ValueError("Projected statements do not reconcile")
            projections.append(period)
            previous = period
        return projections

    def _period(self, index, previous, interest):
        base = previous or self.base
        revenue = D(base.revenue)*(1+D(self.op.revenue_growth_rates[index]))
        cogs = revenue*D(self.op.cogs_percent_revenue[index])
        opex = revenue*D(self.op.opex_variable_pct)+D(self.op.opex_fixed)
        capex = revenue*D(self.cap.maintenance_capex_pct)+(D(self.cap.growth_capex[index]) if self.cap.growth_capex else D(0))
        gross_open = previous.ppe_gross if previous else D(self.base.ppe_net)
        acc_open = previous.accumulated_depreciation if previous else D(0)
        available = D(base.ppe_net)+capex
        salvage = (gross_open+capex)*D(self.cap.salvage_value_pct)
        if self.cap.depreciation_method == "straight_line":
            depreciation = (gross_open+capex/2)*(1-D(self.cap.salvage_value_pct))/D(self.cap.asset_life_years)
        else:
            depreciation = (D(base.ppe_net)+capex/2)*2/D(self.cap.asset_life_years)
        depreciation = max(D(0),min(depreciation,available-salvage))
        ebitda = revenue-cogs-opex
        ebit = ebitda-depreciation
        ebt = ebit-interest
        tax = max(D(0),ebt)*D(self.op.tax_rate)
        income = ebt-tax
        ar = revenue*D(self.wc.days_sales_outstanding/365 if self.wc.days_sales_outstanding is not None else self.wc.ar_pct_revenue)
        inv = cogs*D(self.wc.days_inventory_outstanding/365 if self.wc.days_inventory_outstanding is not None else self.wc.inventory_pct_cogs)
        ap = cogs*D(self.wc.days_payable_outstanding/365 if self.wc.days_payable_outstanding is not None else self.wc.ap_pct_cogs)
        accrued = revenue*D(self.wc.accrued_liabilities_pct_revenue)
        dar,dinv,dap,dacc = D(base.accounts_receivable)-ar,D(base.inventory)-inv,ap-D(base.accounts_payable),accrued-D(base.accrued_liabilities)
        cfo = income+depreciation+dar+dinv+dap+dacc
        dividend = -max(D(0),income)*D(self.fin.dividend_payout_ratio)
        repayment = D(base.long_term_debt)*D(self.fin.amortization_pct)
        long_debt = D(base.long_term_debt)-repayment
        cash_before = D(base.cash)+cfo-capex+dividend-repayment
        target = D(max(self.fin.target_cash_balance,self.wc.minimum_cash_balance))
        draw = max(D(0),target-cash_before)
        revolver_repay = min(D(base.short_term_debt),max(D(0),cash_before-target))
        short_debt = D(base.short_term_debt)+draw-revolver_repay
        if short_debt > D(self.fin.revolver_capacity)+D('.01'):
            raise ValueError(f"Revolver capacity exceeded in year {index+1}; funding shortfall {float(short_debt-D(self.fin.revolver_capacity)):.2f}")
        financing = draw-repayment-revolver_repay+dividend
        change_cash = cfo-capex+financing
        cash = D(base.cash)+change_cash
        ppe = available-depreciation
        assets = cash+ar+inv+ppe+self.other_assets
        liabilities = ap+accrued+short_debt+long_debt+self.other_liabilities
        common = D(self.base.total_equity)-D(self.base.retained_earnings)
        retained = D(base.retained_earnings)+income+dividend
        unlevered = ebit-max(D(0),ebit)*D(self.op.tax_rate)+depreciation-capex+dar+dinv+dap+dacc
        period = ProjectedPeriod(period=f"Year_{index+1}", revenue=revenue,cogs=cogs,gross_profit=revenue-cogs,
            operating_expenses=opex,ebitda=ebitda,depreciation=depreciation,ebit=ebit,interest_expense=interest,
            ebt=ebt,tax_expense=tax,net_income=income,cash=cash,accounts_receivable=ar,inventory=inv,
            current_assets=cash+ar+inv,ppe_gross=gross_open+capex,accumulated_depreciation=acc_open+depreciation,
            ppe_net=ppe,total_assets=assets,accounts_payable=ap,short_term_debt=short_debt,
            current_liabilities=ap+accrued+short_debt,long_term_debt=long_debt,total_liabilities=liabilities,
            common_stock=common,retained_earnings=retained,total_equity=common+retained,
            net_income_cf=income,depreciation_cf=depreciation,change_in_ar=dar,change_in_inventory=dinv,
            change_in_ap=dap,operating_cash_flow=cfo,capex=-capex,investing_cash_flow=-capex,
            debt_issuance=draw,debt_repayment=-repayment-revolver_repay,dividends=dividend,
            financing_cash_flow=financing,net_cash_change=change_cash,beginning_cash=D(base.cash),
            accrued_liabilities=accrued,change_in_accrued=dacc,other_assets=self.other_assets,
            other_liabilities=self.other_liabilities,unlevered_fcf=unlevered)
        return period,(D(base.short_term_debt)+D(base.long_term_debt)+short_debt+long_debt)/2*D(self.fin.debt_interest_rate)

    def validate_statements(self, p):
        tolerance = D('.01')
        return {"balance_sheet_balances":abs(p.total_assets-p.total_liabilities-p.total_equity)<tolerance,
            "cash_flow_reconciles":abs(p.cash-p.beginning_cash-p.net_cash_change)<tolerance,
            "income_statement_reconciles":abs(p.ebit-p.interest_expense-p.tax_expense-p.net_income)<tolerance}

    def extract_free_cash_flows(self, projections):
        return [float(p.unlevered_fcf) for p in projections]
