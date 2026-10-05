from datetime import datetime, timezone
import math
import os
from fastapi import APIRouter, HTTPException
import yfinance as yf
from app.data_ingestion.fred import FredClient, year_over_year
from app.data_ingestion.bank_of_canada import canadian_cpi
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()

def live_client():
    if os.getenv('VERTIGE_OFFLINE') == '1':
        raise HTTPException(503, 'Live macro data is disabled')
    client = FredClient()
    if not client.api_key:
        raise HTTPException(503, 'FRED_API_KEY is required for macro data')
    return client

def provenance(series):
    return {'source':'FRED','series':series,'fetched_at':datetime.now(timezone.utc).isoformat()}


@router.get('/treasury-curve')
def treasury_curve():
    fred = live_client()
    series = {'3M':'DGS3MO', '2Y':'DGS2', '5Y':'DGS5', '10Y':'DGS10', '30Y':'DGS30'}
    def load(item):
        tenor, identifier = item
        try:
            return tenor, {row['date']:row['value'] for row in fred.get_series_data(identifier, 20)}, None
        except ValueError as error:
            return tenor, {}, str(error)
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(load, series.items()))
    available = [set(values) for _, values, _ in results if values]
    common = set.intersection(*available) if available else set()
    if not common:
        raise HTTPException(502, 'No common observation date is available for the Treasury curve')
    date = max(common)
    points = [{'tenor':tenor, 'value':values.get(date), 'series':series[tenor]} for tenor, values, _ in results]
    by_tenor = {p['tenor']:p['value'] for p in points}
    spread = (by_tenor['10Y']-by_tenor['2Y'])*100 if by_tenor['10Y'] is not None and by_tenor['2Y'] is not None else None
    return {'date':date, 'points':points, 'spread_10y_2y_bps':spread,
            'unavailable':[{'tenor':tenor, 'error':error} for tenor, _, error in results if error],
            'provenance':provenance(list(series.values())),
            'methodology':'Treasury constant-maturity yields quoted on an investment basis, percent per annum. Latest common observation date across available tenors. These are benchmark yields, not a bootstrapped spot curve.'}

@router.get('/yield-curve')
def get_yield_curve():
    if os.getenv('VERTIGE_OFFLINE') == '1':
        raise HTTPException(503, 'Live macro data is disabled')
    tickers = {'3M':'^IRX','5Y':'^FVX','10Y':'^TNX','30Y':'^TYX'}
    try:
        data = yf.download(list(tickers.values()),period='5d',progress=False,timeout=10)
        curve = []
        for tenor,ticker in tickers.items():
            series = data['Close'][ticker].dropna()
            value = float(series.iloc[-1]) if len(series) else None
            curve.append({'tenor':tenor,'value':value if value is not None and math.isfinite(value) else None,
                          'date':str(series.index[-1].date()) if len(series) else None,'source':'Yahoo Finance'})
        if not any(p['value'] is not None for p in curve): raise ValueError()
        return curve
    except Exception:
        raise HTTPException(502,'Yield curve unavailable') from None

@router.get('/us')
def get_us_macro():
    fred = live_client()
    cpi = fred.get_cpi(72)
    unemployment = fred.get_unemployment(60)
    rates = fred.get_fed_funds(60)
    spread = fred.get_series_data('T10Y2Y',10)
    return {'cpi_yoy':year_over_year(cpi),'cpi':cpi,'unemployment':unemployment,
            'fed_funds':rates[-1]['value'],'fed_funds_history':rates,
            'spread_10y_2y':spread[-1]['value'],'spread_date':spread[-1]['date'],
            'provenance':provenance(['CPIAUCSL','UNRATE','FEDFUNDS','T10Y2Y'])}

@router.get('/canada')
def get_canada_macro():
    fred = live_client()
    cpi = canadian_cpi()
    unemployment = fred.get_series_data('LRUNTTTTCAM156S',60)
    rates = fred.get_series_data('IRLTLT01CAM156N',60)
    return {'cpi_yoy':year_over_year(cpi),'cpi':cpi,'unemployment':unemployment,'interest_rate':rates,
            'provenance':{**provenance(['V41690973','LRUNTTTTCAM156S','IRLTLT01CAM156N']),
                'source':'Bank of Canada / Statistics Canada (CPI); FRED (unemployment and bond yield)',
                'cpi_url':'https://www.bankofcanada.ca/rates/price-indexes/cpi/',
                'cpi_units':'Index 2002=100, not seasonally adjusted'}}
