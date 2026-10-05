from decimal import Decimal
import pandas as pd
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.routers.stats import calculate_metrics, compare_benchmark

client = TestClient(app)


def test_relative_earnings_value_and_enterprise_bridge():
    base = {'metric':'forward_pe', 'multiples':[10,20,30], 'target_metric':4}
    response = client.post('/api/comparables/value', json=base)
    assert response.status_code == 200
    assert response.json()['prices'] == {'p25':60, 'median':80, 'p75':100}
    response = client.post('/api/comparables/value', json={'metric':'ev_ebitda', 'multiples':[5,10,15], 'target_metric':20, 'net_debt_m':50, 'shares_m':10})
    assert response.json()['prices'] == {'p25':10, 'median':15, 'p75':20}
    assert client.post('/api/comparables/value', json=base | {'multiples':[-1,20]}).status_code == 422
    assert client.post('/api/comparables/value', json=base | {'target_metric':0}).status_code == 422


def test_peer_table_preserves_missing_metrics_and_partial_failure(monkeypatch):
    from app.routers import comparables
    def info(ticker):
        if ticker == 'BAD': raise HTTPException(502, 'Provider failed')
        return {'shortName':ticker, 'forwardPE':None, 'trailingPE':20, 'currency':'USD', 'financialCurrency':'USD', '_fetched_at':'2026-10-05T00:00:00Z'}
    monkeypatch.setattr(comparables, 'provider_info', info)
    response = client.post('/api/comparables/table', json={'tickers':['AAA','AAA','BAD']})
    assert response.status_code == 200
    data = response.json()
    assert len(data['companies']) == 1 and len(data['unavailable']) == 1
    assert data['companies'][0]['forward_pe'] is None
    assert data['companies'][0]['trailing_pe'] == 20
    assert data['companies'][0]['market_cap'] is None
    assert client.post('/api/comparables/table', json={'tickers':['bad/ticker']}).status_code == 422


def test_benchmark_beta_matches_independent_double_return_reference():
    dates = pd.date_range('2026-01-01', periods=4)
    asset = pd.Series([100,110,99,108.9], index=dates)
    benchmark = pd.Series([100,105,99.75,104.7375], index=dates)
    data = compare_benchmark(asset, benchmark)
    assert data['observations'] == 3
    assert data['beta'] == pytest.approx(2)
    assert data['correlation'] == pytest.approx(1)
    assert data['annualized_active_return'] == pytest.approx(4.2)
    assert data['tracking_error'] == pytest.approx(float((Decimal(1)/Decimal(300)*252).sqrt()))


def test_benchmark_join_does_not_bridge_missing_sessions():
    dates = pd.date_range('2026-01-01', periods=7)
    asset = pd.Series([100 * 1.1**i for i in range(7)], index=dates)
    benchmark = pd.Series([100 * 1.05**i for i in range(7)], index=dates).drop(dates[2])
    data = compare_benchmark(asset, benchmark)
    assert data['observations'] == 4
    assert data['asset_returns'] == pytest.approx([.1]*4)
    assert data['benchmark_returns'] == pytest.approx([.05]*4)
    assert str(dates[3].date()) not in data['dates']


def test_rolling_risk_has_full_window_and_drawdown_retains_opening_price():
    dates = pd.date_range('2026-01-01', periods=23)
    prices = [100.0]
    returns = [.01 if i % 2 else -.01 for i in range(22)]
    for r in returns: prices.append(prices[-1]*(1+r))
    result = calculate_metrics(pd.Series(prices, index=dates), 0)
    assert result['rolling_volatility_21d'][:20] == [None]*20
    first = [Decimal(str(r)) for r in returns[:21]]
    mean = sum(first)/len(first)
    expected = (sum((r-mean)**2 for r in first)/20*252).sqrt()
    assert result['rolling_volatility_21d'][20] == pytest.approx(float(expected))
    assert result['drawdown'][0] == 0
    assert result['drawdown'][1] == pytest.approx(-.01)
    assert result['total_return'] == pytest.approx(prices[-1]/100-1)


def test_stats_api_keeps_asset_results_when_benchmark_unavailable(monkeypatch):
    from app.routers import stats
    monkeypatch.setenv('VERTIGE_OFFLINE', '0')
    class Ticker:
        def __init__(self, symbol): self.symbol = symbol
        def history(self, **kwargs):
            if self.symbol == 'BAD': return pd.DataFrame()
            return pd.DataFrame({'Close':[100,110,99,108.9]}, index=pd.date_range('2026-01-01', periods=4))
    monkeypatch.setattr(stats.yf, 'Ticker', Ticker)
    response = client.get('/api/stats/metrics/AAA?benchmark=BAD&period=3mo')
    assert response.status_code == 200
    assert response.json()['period'] == '3mo' and response.json()['observations'] == 3
    assert response.json()['benchmark_error']


def test_treasury_curve_uses_common_date_and_converts_spread_to_basis_points(monkeypatch):
    from app.routers import macro
    class Fred:
        def get_series_data(self, identifier, limit):
            if identifier == 'DGS30': raise ValueError('Unavailable')
            values = {'DGS3MO':4.2,'DGS2':4.5,'DGS5':4.6,'DGS10':4.8}
            rows = [{'date':'2026-10-01','value':values[identifier]}]
            if identifier != 'DGS2': rows.append({'date':'2026-10-02','value':values[identifier]+.1})
            return rows
    monkeypatch.setattr(macro, 'live_client', lambda: Fred())
    response = client.get('/api/macro/treasury-curve')
    assert response.status_code == 200
    data = response.json()
    assert data['date'] == '2026-10-01'
    assert data['spread_10y_2y_bps'] == pytest.approx(30)
    assert data['points'][-1]['value'] is None
    assert data['unavailable'][0]['tenor'] == '30Y'


def test_dcf_zero_dispersion_matches_deterministic_value():
    from tests.test_integration import assumptions
    request = assumptions(run_monte_carlo=True, iterations=20, simulation_wacc_sd=0, simulation_growth_sd=0)
    response = client.post('/api/valuation/dcf', json=request)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['mean_price'] == pytest.approx(data['implied_price'])
    assert data['confidence_interval'] == pytest.approx([data['implied_price']]*2)
    assert data['simulation_accepted'] == 20 and data['simulation_rejected'] == 0
    assert client.post('/api/valuation/dcf', json=request | {'simulation_wacc_sd':-1}).status_code == 422
