from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, ConfigDict, Field
from app.engine.dcf_engine import AdvancedDCFEngine, AdvancedDCFRequest, AdvancedDCFResponse
from app.models.ddm import DDMInputs, calculate_ddm_gordon, calculate_ddm_multi_stage
from app.engine.nav_engine import NAVEngine, RealEstateNAVInputs, ResourceNAVInputs
from app.engine.three_statement_model import (ThreeStatementModel, HistoricalPeriod, OperatingAssumptions,
    WorkingCapitalDrivers, CapexAssumptions, FinancingAssumptions)
import io
import pandas as pd

router = APIRouter()

@router.post('/dcf', response_model=AdvancedDCFResponse)
@router.post('/dcf/advanced', response_model=AdvancedDCFResponse)
def calculate_dcf(request: AdvancedDCFRequest):
    engine = AdvancedDCFEngine(request)
    result = engine.calculate()
    if request.run_monte_carlo:
        sim = engine.run_simulation()
        result.simulation_accepted = sim['accepted']
        result.simulation_rejected = sim['rejected']
        result.mean_price = sim['mean']
        result.confidence_interval = [sim['p5'],sim['p95']]
        result.warnings.append('Monte Carlo percentiles describe assumed scenarios, not a statistical confidence interval.')
    return result

@router.post('/dcf/simulate')
def simulate_dcf(request: AdvancedDCFRequest):
    return AdvancedDCFEngine(request).run_simulation()

class SensitivityRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    assumptions: AdvancedDCFRequest
    wacc_values: list[float] = Field(min_length=1, max_length=15)
    growth_values: list[float] = Field(min_length=1, max_length=15)

@router.post('/dcf/sensitivity')
def sensitivity(request: SensitivityRequest):
    if request.assumptions.terminal_method != 'GORDON':
        raise ValueError('WACC and perpetual-growth sensitivity requires Gordon terminal value')
    rows = []
    for g in request.growth_values:
        row = []
        for w in request.wacc_values:
            if w <= g or w <= 0 or w > 1 or not -1 < g <= .25:
                row.append(None)
                continue
            values = request.assumptions.model_dump() | {'wacc':w,'terminal_growth':g,'run_monte_carlo':False}
            row.append(AdvancedDCFEngine(AdvancedDCFRequest(**values)).calculate().implied_price)
        rows.append(row)
    return {'wacc_values':request.wacc_values,'growth_values':request.growth_values,'prices':rows,
            'units':'currency per share','invalid_cell':None}

@router.post('/ddm/gordon')
def ddm_gordon(inputs: DDMInputs): return calculate_ddm_gordon(inputs)

@router.post('/ddm/multi-stage')
def ddm_multi(inputs: DDMInputs): return calculate_ddm_multi_stage(inputs)

@router.get('/ddm/fetch-dividend-data/{ticker}')
def dividend_data(ticker: str):
    from app.routers.market_data import provider_info, provenance
    data = provider_info(ticker)
    price = data.get('currentPrice') or data.get('regularMarketPrice')
    dividend = data.get('trailingAnnualDividendRate')
    if price is None or dividend is None:
        raise HTTPException(502,'Annual dividend or price unavailable; enter verified values manually')
    return {'ticker':ticker.upper(),'current_price':price,'current_dividend':dividend,
            'dividend_growth_rate':None,'provenance':provenance(ticker,data),
            'note':'Trailing annual dividend; future growth must be supplied by the analyst'}

@router.post('/nav/real-estate')
def re_nav(inputs: RealEstateNAVInputs): return NAVEngine.calculate_real_estate(inputs)

@router.post('/nav/resource')
def resource_nav(inputs: ResourceNAVInputs): return NAVEngine.calculate_resource(inputs)

@router.post('/nav')
def nav(ticker:str, assets:float, liabilities:float, shares_out:float, current_price:float):
    import math
    if not all(math.isfinite(x) for x in [assets,liabilities,shares_out,current_price]) or min(assets,liabilities)<0 or min(shares_out,current_price)<=0:
        raise ValueError('Use finite nonnegative assets/liabilities and positive shares/price')
    equity=assets-liabilities
    return {'ticker':ticker,'nav':equity,'nav_per_share':equity/shares_out,'current_price':current_price,
        'upside':(equity/shares_out/current_price-1)*100}

class ProjectionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    historical_base: HistoricalPeriod
    operating_assumptions: OperatingAssumptions
    wc_drivers: WorkingCapitalDrivers
    capex_assumptions: CapexAssumptions
    financing_assumptions: FinancingAssumptions
    projection_years: int = Field(default=5, ge=1, le=30)

@router.get('/three-statement/sample-data')
def sample_data():
    return dict(period='Illustrative opening year',revenue=1000000,cogs=400000,operating_expenses=150000,
        depreciation=40000,interest_expense=15000,tax_expense=82950,net_income=312050,
        cash=100000,accounts_receivable=120000,inventory=60000,ppe_net=400000,total_assets=680000,
        accounts_payable=40000,accrued_liabilities=50000,short_term_debt=0,long_term_debt=300000,
        total_liabilities=390000,retained_earnings=90000,total_equity=290000,
        operating_cash_flow=352050,capex=30000,financing_cash_flow=0)

@router.post('/three-statement/project')
def project(request: ProjectionRequest):
    model = ThreeStatementModel(**{k:getattr(request,k) for k in type(request).model_fields})
    projections = model.project_financials()
    validations = {key:all(model.validate_statements(p)[key] for p in projections) for key in model.validate_statements(projections[0])}
    warnings = [f'{p.period}: interest coverage below covenant' for p in projections
        if p.interest_expense>0 and p.ebit/p.interest_expense<request.financing_assumptions.covenant_min_interest_coverage]
    return {'projections':[p.model_dump(mode='json') for p in projections], 'validations':validations,
        'free_cash_flows':model.extract_free_cash_flows(projections),'warnings':warnings,
        'units':'Same currency units as historical inputs; no automatic scaling',
        'conventions':'Average opening/closing debt interest; half-year new capex depreciation; no tax-loss carryforwards'}

@router.post('/three-statement/upload-excel')
async def upload_history(file: UploadFile = File(...)):
    content = await file.read(2_000_001)
    if len(content)>2_000_000: raise HTTPException(413,'Upload must be at most 2 MB')
    suffix = (file.filename or '').lower()
    try:
        if suffix.endswith('.csv'): frame=pd.read_csv(io.BytesIO(content))
        elif suffix.endswith('.xlsx'): frame=pd.read_excel(io.BytesIO(content))
        else: raise ValueError('Use a CSV or XLSX file with one historical period per row')
        if frame.empty or frame.isna().any().any(): raise ValueError('Historical rows must not contain missing values')
        base = HistoricalPeriod(**frame.iloc[-1].to_dict())
        if abs(base.total_assets-base.total_liabilities-base.total_equity)>.01:
            raise ValueError('Historical balance sheet does not balance')
        return base
    except (ValueError,TypeError) as e: raise HTTPException(422,str(e))
