from decimal import Decimal
import io, math
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.engine.dcf_engine import AdvancedDCFRequest, AdvancedDCFEngine
from app.engine.three_statement_model import ThreeStatementModel
from app.routers.valuation import ProjectionRequest, sample_data
from app.routers import market_data
client=TestClient(app)

def test_missing_sector_never_returns_unrelated_reit_notes():
    for sector in ['healthcare', 'financials', 'unknown']:
        response=client.get(f'/api/industries/sectors/{sector}/profile')
        assert response.status_code==404
        assert 'not available' in response.json()['detail']
    assert client.get('/api/industries/sectors/technology/profile').json()['sector']=='Technology & Software'

def assumptions(**kw):
    return dict(ticker='TEST',current_price=10,shares_outstanding_m=10,net_debt_m=20,start_revenue_m=100,
        growth_rates=[.1],ebit_margins=[.2],years=1,tax_rate=.25,da_pct=.03,capex_pct=.04,nwc_pct=.12,nwc_treatment="balance_ratio",wacc=.1,terminal_growth=.02)|kw

def projection(**kw):
    return dict(historical_base=sample_data(),operating_assumptions={'revenue_growth_rates':[.1,.05,.03],'cogs_percent_revenue':[.4]*3},
        wc_drivers={'days_sales_outstanding':45,'days_inventory_outstanding':60,'days_payable_outstanding':40},
        capex_assumptions={'growth_capex':[10000,0,0]},financing_assumptions={'revolver_capacity':500000},projection_years=3)|kw

def test_health_and_routes():
    assert client.get('/health').json()['status']=='ok'
    for p in ['/api/valuation/dcf','/api/valuation/dcf/advanced','/api/valuation/ddm/gordon','/api/valuation/ddm/multi-stage','/api/valuation/nav/real-estate','/api/valuation/three-statement/project']:
        assert p in app.openapi()['paths']

def test_status_exposes_configuration_without_secret(monkeypatch):
    monkeypatch.setenv('FRED_API_KEY', 'private-test-key')
    data = client.get('/api/status').json()
    assert data['data_mode'] == 'offline' and data['fred_key_configured'] is True
    assert 'private-test-key' not in str(data)
    monkeypatch.delenv('FRED_API_KEY')
    monkeypatch.setenv('VERTIGE_OFFLINE', '0')
    data = client.get('/api/status').json()
    assert data['data_mode'] == 'provider' and data['fred_key_configured'] is False

def test_canadian_macro_uses_index_not_growth_series(monkeypatch):
    from app.routers import macro
    requested = []
    class FixtureFred:
        def get_series_data(self, series_id, limit):
            requested.append(series_id)
            return [{'date': '2024-03-01', 'value': 100}, {'date': '2025-03-01', 'value': 102}]
    monkeypatch.setattr(macro, 'live_client', lambda: FixtureFred())
    monkeypatch.setattr(macro, 'canadian_cpi', lambda: [{'date': '2024-03-01', 'value': 100}, {'date': '2025-03-01', 'value': 102}])
    response = client.get('/api/macro/canada')
    assert response.status_code == 200
    assert requested == ['LRUNTTTTCAM156S', 'IRLTLT01CAM156N']
    assert response.json()['cpi_yoy'] == 2

def test_canadian_cpi_orders_observations_and_ignores_missing(monkeypatch):
    from app.data_ingestion import bank_of_canada
    from app.data_ingestion.fred import year_over_year
    monkeypatch.setenv('VERTIGE_OFFLINE', '0')
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {'observations': [{'d': '2026-08-01', 'V41690973': {'v': '103'}},
                {'d': '2026-07-01', 'V41690973': {'v': ''}},
                {'d': '2025-08-01', 'V41690973': {'v': '100'}}]}
    monkeypatch.setattr(bank_of_canada.requests, 'get', lambda *a, **kw: Response())
    rows = bank_of_canada.canadian_cpi()
    assert [row['date'] for row in rows] == ['2025-08-01', '2026-08-01']
    assert year_over_year(rows) == 3

def test_dcf_independent_reference():
    # FCFF=22*.75+3.3-4.4-(13.2-12)=14.2. Terminal FCFF=22.44*.75+3.366-4.488-.264=15.444.
    ev=Decimal('14.2')/Decimal('1.1')+Decimal('15.444')/Decimal('.08')/Decimal('1.1')
    r=client.post('/api/valuation/dcf',json=assumptions());assert r.status_code==200,r.text
    d=r.json();assert d['forecast'][0]['change_nwc']==pytest.approx(1.2)
    assert d['forecast'][0]['fcff']==pytest.approx(14.2)
    assert d['terminal_fcff']==pytest.approx(15.444)
    assert d['enterprise_value']==pytest.approx(float(ev),rel=1e-12)
    assert d['implied_price']==pytest.approx(float((ev-20)/10),rel=1e-12)

def test_perpetuity_and_bridge():
    d=AdvancedDCFEngine(AdvancedDCFRequest(**assumptions(growth_rates=[0]*5,ebit_margins=[.2]*5,years=5,net_debt_m=-10,tax_rate=0,da_pct=0,capex_pct=0,nwc_pct=0,terminal_growth=0,minority_interest_m=5,preferred_equity_m=2,nonoperating_assets_m=3))).calculate()
    assert d.enterprise_value==pytest.approx(200);assert d.equity_value==pytest.approx(206);assert d.implied_price==pytest.approx(20.6)

def test_midyear_timing():
    end=client.post('/api/valuation/dcf',json=assumptions()).json()
    mid=client.post('/api/valuation/dcf',json=assumptions(discount_timing='mid_year')).json()
    assert mid['pv_terminal_value']==pytest.approx(end['pv_terminal_value'])
    assert mid['forecast'][0]['pv_fcff']==pytest.approx(14.2/math.sqrt(1.1))

@pytest.mark.parametrize('field,value',[('wacc',.02),('wacc',0),('shares_outstanding_m',0),('current_price',0),('years',0),('growth_rates',[]),('growth_rates',[-1]),('ebit_margins',[.2,.3]),('tax_rate',1.1),('capex_pct',-.1),('misspelled_rate',.1)])
def test_invalid_dcf(field,value):
    assert client.post('/api/valuation/dcf',json=assumptions(**{field:value})).status_code==422

def test_exit_multiple():
    a=assumptions(terminal_method='EXIT_MULTIPLE',exit_multiple=10)
    assert client.post('/api/valuation/dcf',json=a).json()['terminal_value']==pytest.approx(220)
    assert client.post('/api/valuation/dcf',json=a|{'exit_multiple_basis':'EBITDA'}).json()['terminal_value']==pytest.approx(253)

def test_stage_compatibility():
    a=assumptions();[a.pop(k) for k in ['growth_rates','ebit_margins','years']]
    a.update(stage_1_years=2,stage_2_years=2,stage_1_growth=.1,stage_2_growth_start=.1,stage_2_growth_end=.02,ebit_margin=.2)
    r=client.post('/api/valuation/dcf/advanced',json=a);assert r.status_code==200,r.text
    assert [x['revenue_growth'] for x in r.json()['forecast']]==pytest.approx([10,10,6,2])

def test_sensitivity():
    base=client.post('/api/valuation/dcf',json=assumptions()).json()['implied_price']
    d=client.post('/api/valuation/dcf/sensitivity',json={'assumptions':assumptions(),'wacc_values':[.02,.08,.1,.12],'growth_values':[.02,.03]}).json()['prices']
    assert d[0][0] is None;assert d[0][2]==pytest.approx(base);assert d[0][1]>d[0][2]>d[0][3];assert d[1][2]>d[0][2]

def test_simulation_reproducible():
    a=assumptions(iterations=100,simulation_seed=3)
    d=client.post('/api/valuation/dcf/simulate',json=a).json()
    assert d==client.post('/api/valuation/dcf/simulate',json=a).json();assert d['accepted']+d['rejected']==100

@pytest.mark.parametrize('multi',[False,True])
def test_ddm(multi):
    a=dict(ticker='TEST',current_price=50,current_dividend=2,dividend_growth_rate=.04,required_return=.1)
    if multi:a.update(high_growth_years=2,high_growth_rate=0)
    path='/api/valuation/ddm/'+('multi-stage' if multi else 'gordon')
    d=client.post(path,json=a);assert d.status_code==200,d.text
    expected=2*1.04/.06 if not multi else 2/1.1+2/1.1**2+(2*1.04/.06)/1.1**2
    assert d.json()['intrinsic_value_per_share']==pytest.approx(round(expected,2))
    a['required_return']=.04;assert client.post(path,json=a).status_code==422

def test_nav():
    a=dict(noi=200,cap_rate=.1,other_assets=100,total_debt=500,minority_interest=50,preferred_equity=100,shares_outstanding=10)
    assert client.post('/api/valuation/nav/real-estate',json=a).json()['nav_per_share']==145
    for k in ['cap_rate','shares_outstanding']:assert client.post('/api/valuation/nav/real-estate',json=a|{k:0}).status_code==422
    a=dict(reserves=100,value_per_unit=50,production_cost_per_unit=20,exploration_upside=100,liabilities=1000,shares_outstanding=10)
    assert client.post('/api/valuation/nav/resource',json=a).json()['nav_per_share']==210

def test_statement_identities_and_fcf():
    r=client.post('/api/valuation/three-statement/project',json=projection());assert r.status_code==200,r.text
    prev=sample_data()
    for row in r.json()['projections']:
        p={k:(float(v) if k!='period' else v) for k,v in row.items()}
        assert p['total_assets']==pytest.approx(p['total_liabilities']+p['total_equity'],abs=.01)
        assert p['cash']-prev['cash']==pytest.approx(p['operating_cash_flow']+p['investing_cash_flow']+p['financing_cash_flow'],abs=.01)
        assert p['ebit']-p['interest_expense']-p['tax_expense']==pytest.approx(p['net_income'],abs=.01)
        assert p['accounts_receivable']==pytest.approx(p['revenue']*45/365)
        dnwc=p['accounts_receivable']-prev['accounts_receivable']+p['inventory']-prev['inventory']-p['accounts_payable']+prev['accounts_payable']-p['accrued_liabilities']+prev['accrued_liabilities']
        assert p['unlevered_fcf']==pytest.approx(p['ebit']*.79+p['depreciation']+p['capex']-dnwc,abs=.01)
        interest=(prev['short_term_debt']+prev['long_term_debt']+p['short_term_debt']+p['long_term_debt'])/2*.05
        assert p['interest_expense']==pytest.approx(interest,abs=.01)
        prev=p
    assert all(r.json()['validations'].values())

def test_repeat_and_unbalanced_base():
    request=ProjectionRequest(**projection());model=ThreeStatementModel(**{k:getattr(request,k) for k in type(request).model_fields})
    assert model.project_financials()==model.project_financials()
    a=projection();a['historical_base']['total_assets']+=100
    assert client.post('/api/valuation/three-statement/project',json=a).status_code==422

def test_funding_and_losses():
    a=projection();a['capex_assumptions']['growth_capex']=[2000000,0,0];a['financing_assumptions']['revolver_capacity']=0
    r=client.post('/api/valuation/three-statement/project',json=a);assert r.status_code==422 and 'capacity' in r.text
    a=projection();a['operating_assumptions']['cogs_percent_revenue']=[.95]*3;a['financing_assumptions']['revolver_capacity']=5000000
    r=client.post('/api/valuation/three-statement/project',json=a);assert r.status_code==200,r.text
    assert all(float(p['dividends'])==0 for p in r.json()['projections'])

def test_missing_data_and_currency(monkeypatch):
    info=dict(currentPrice=10,sharesOutstanding=10000000,totalRevenue=100000000,totalDebt=0,totalCash=0,currency='USD',financialCurrency='USD')
    monkeypatch.setattr(market_data,'provider_info',lambda t:info)
    assert client.get('/api/market/TEST').status_code==200
    del info['totalDebt'];assert client.get('/api/market/TEST').status_code==502
    info.update(totalDebt=0,financialCurrency='CAD');assert client.get('/api/market/TEST').status_code==422

def test_offline_provider():assert client.get('/api/market/AAPL').status_code==503

def test_builder():
    t=client.get('/api/builder/templates/dcf').json()
    assert client.post('/api/builder/solve',json=t).json()['results']['ebit_y2']==pytest.approx(27.5)
    t['nodes'][2]['formula']='().__class__.__base__.__subclasses__()'
    assert client.post('/api/builder/solve',json=t).status_code==400
    t=client.get('/api/builder/templates/dcf').json();t['edges'].append({'source':'ebit_y2','target':'rev_y1'})
    assert client.post('/api/builder/solve',json=t).status_code==400

def test_exports():
    from openpyxl import load_workbook
    data={'model_type':'DCF','ticker':'TEST','data':[{'year':1,'fcff':14.2,'note':'=1+1'}]}
    r=client.post('/api/export/excel',json=data);assert r.status_code==200,r.text
    assert load_workbook(io.BytesIO(r.content)).active['C2'].data_type!='f'
    r=client.post('/api/export/pdf',json=data);assert r.status_code==200 and r.content.startswith(b'%PDF')

def test_csv_import():
    import pandas as pd
    body=pd.DataFrame([sample_data()]).to_csv(index=False).encode()
    r=client.post('/api/valuation/three-statement/upload-excel',files={'file':('base.csv',body,'text/csv')})
    assert r.status_code==200,r.text;assert r.json()['total_assets']==680000
    assert client.post('/api/valuation/three-statement/upload-excel',files={'file':('base.csv',b'revenue\n100','text/csv')}).status_code==422


def test_statistics_include_opening_peak_and_undefined_ratios():
    import pandas as pd
    from app.routers.stats import calculate_metrics
    dates = pd.date_range('2026-01-01', periods=4)
    result = calculate_metrics(pd.Series([100.,80.,90.,110.], index=dates), 0)
    assert result['max_drawdown'] == pytest.approx(-.2)
    assert result['cumulative_performance'] == pytest.approx([1,.8,.9,1.1])
    assert len(result['dates']) == len(result['cumulative_performance'])
    flat = calculate_metrics(pd.Series([100.,100.,100.,100.], index=dates), 0)
    assert flat['sharpe_ratio'] is None
    assert flat['sortino_ratio'] is None
    with pytest.raises(ValueError):
        calculate_metrics(pd.Series([100.,0.,110.,120.],index=dates))



def test_cpi_requires_same_month_last_year():
    from app.data_ingestion.fred import year_over_year
    assert year_over_year([{'date':'2025-07-01','value':100},{'date':'2026-07-01','value':103}]) == 3
    with pytest.raises(ValueError,match='year-ago'):
        year_over_year([{'date':'2025-06-01','value':100},{'date':'2026-07-01','value':103}])


@pytest.mark.parametrize('path', ['/api/stats/metrics/AAPL','/api/news/latest','/api/news/snapshot','/api/macro/us','/api/macro/canada','/api/macro/yield-curve'])
def test_live_routes_report_offline(path):
    response=client.get(path)
    assert response.status_code == 503, response.text


def test_monte_carlo_draw_guard_and_counts():
    request=AdvancedDCFRequest(**assumptions(growth_rates=[-.999],run_monte_carlo=True,iterations=100))
    with pytest.raises(ValueError,match='Simulation growth'):
        AdvancedDCFEngine(request).calculate(custom_g1=-.5)
    response=client.post('/api/valuation/dcf',json=request.model_dump()).json()
    assert response['simulation_accepted'] + response['simulation_rejected'] == 100
    assert response['simulation_rejected'] > 0


def test_legacy_working_capital_investment_ratio_remains_supported():
    legacy=assumptions(nwc_treatment='annual_investment_ratio')
    del legacy['nwc_treatment']
    result=AdvancedDCFEngine(AdvancedDCFRequest(**legacy)).calculate()
    assert result.forecast[0].change_nwc == pytest.approx(13.2)
    assert result.forecast[0].fcff == pytest.approx(2.2)
    assert result.terminal_fcff == pytest.approx(2.244)
    assert result.implied_price == pytest.approx(.75)


def test_statistics_reject_gaps_and_duplicate_dates():
    import pandas as pd
    from app.routers.stats import calculate_metrics
    dates=pd.date_range('2026-01-01',periods=4)
    with pytest.raises(ValueError,match='missing observations'):
        calculate_metrics(pd.Series([100.,float('nan'),121.,133.1],index=dates))
    with pytest.raises(ValueError,match='unique'):
        calculate_metrics(pd.Series([100.,110.,120.,130.],index=[dates[0],dates[0],dates[2],dates[3]]))
