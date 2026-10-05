from fastapi import APIRouter, HTTPException
import yfinance as yf
from typing import List, Dict
from typing import Literal
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field, ConfigDict, FiniteFloat
import numpy as np

router = APIRouter()

# Ticker lists for discovery (Not mock data, but a directory of supported/tracked stocks)
SECTOR_TICKERS = {
    "Technology": ["MSFT", "AAPL", "GOOGL", "NVDA", "ORCL", "CRM", "AMD", "ADBE", "CSCO", "INTC"],
    "Real Estate": ["PLD", "AMT", "EQIX", "WELL", "PSA", "DLR", "O", "VICI", "SBAC", "CCI"],
    "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "AXP", "C", "BLK", "V", "MA"],
    "Healthcare": ["UNH", "LLY", "JNJ", "ABBV", "MRK", "TMO", "PFE", "ABT", "DHR", "AMGN"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HES"],
    "Consumer": ["AMZN", "TSLA", "WMT", "HD", "PG", "COST", "KO", "PEP", "NKE", "MCD"]
}

from app.routers.market_data import provider_info, provenance, ticker_symbol
import math


class PeerRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tickers: list[str] = Field(min_length=1, max_length=12)


@router.post('/table')
def peer_table(request: PeerRequest):
    tickers = list(dict.fromkeys(ticker_symbol(t.strip()) for t in request.tickers))
    def load(ticker):
        try:
            info = provider_info(ticker)
            if not info.get('shortName'):
                raise HTTPException(502, 'Company identity unavailable')
            return {'ticker': ticker, 'name': info['shortName'], 'sector': info.get('sector'),
                    'forward_pe': metric(info, 'forwardPE'), 'trailing_pe': metric(info, 'trailingPE'),
                    'ev_ebitda': metric(info, 'enterpriseToEbitda'), 'price_book': metric(info, 'priceToBook'),
                    'market_cap': metric(info, 'marketCap', 1e-9), 'revenue_growth': metric(info, 'revenueGrowth', 100),
                    'profit_margin': metric(info, 'profitMargins', 100), 'provenance': provenance(ticker, info)}
        except HTTPException as error:
            return {'ticker': ticker, 'error': str(error.detail)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(load, tickers))
    return {'requested': tickers, 'companies': [r for r in results if 'error' not in r],
            'unavailable': [r for r in results if 'error' in r],
            'methodology': 'User-selected peers. Forward and trailing earnings multiples remain separate. Missing and nonpositive multiples are excluded from valuation; market capitalizations retain their native currencies.'}


class RelativeValueRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    metric: Literal['forward_pe', 'trailing_pe', 'ev_ebitda', 'price_book']
    multiples: list[FiniteFloat] = Field(min_length=1, max_length=12)
    target_metric: FiniteFloat = Field(gt=0)
    net_debt_m: FiniteFloat = 0
    shares_m: FiniteFloat = Field(default=1, gt=0)


@router.post('/value')
def relative_value(request: RelativeValueRequest):
    if any(value <= 0 for value in request.multiples):
        raise HTTPException(422, 'Peer valuation multiples must be positive')
    multiples = np.percentile(request.multiples, [25, 50, 75]).tolist()
    def value(multiple):
        total = multiple * request.target_metric
        return (total - request.net_debt_m) / request.shares_m if request.metric == 'ev_ebitda' else total
    prices = [value(multiple) for multiple in multiples]
    if not all(math.isfinite(price) for price in prices):
        raise HTTPException(422, 'Valuation exceeds the numeric range')
    return {'metric': request.metric, 'peer_count': len(request.multiples),
            'multiples': dict(zip(['p25', 'median', 'p75'], multiples)),
            'prices': dict(zip(['p25', 'median', 'p75'], prices)),
            'methodology': 'Unweighted peer percentiles with linear interpolation. Range describes peer dispersion, not forecast uncertainty. EV/EBITDA assumes net debt is the only non-common-equity claim; include other claims in that adjustment if applicable.'}

@router.get('/peers/{ticker}')
def peers(ticker:str):
    info=provider_info(ticker);sector=info.get('sector')
    mapping={'Financial Services':'Financials','Consumer Cyclical':'Consumer','Consumer Defensive':'Consumer'}
    group=mapping.get(sector,sector)
    return {'ticker':ticker.upper(),'sector':sector,'peers':[t for t in SECTOR_TICKERS.get(group,[]) if t!=ticker.upper()][:5],
        'method':'Curated sector directory; peers are not ranked by comparability','provenance':provenance(ticker,info)}

def metric(info,key,scale=1):
    value=info.get(key)
    return value*scale if isinstance(value,(int,float)) and math.isfinite(value) else None

@router.get('/screener')
def screener(sector:str='Technology'):
    if sector!='All' and sector not in SECTOR_TICKERS:raise HTTPException(422,'Unknown sector')
    tickers=SECTOR_TICKERS.get(sector) if sector!='All' else [x for values in SECTOR_TICKERS.values() for x in values[:2]]
    rows=[]
    for ticker in tickers:
        try:
            info=provider_info(ticker)
            if not info.get('shortName'):continue
            growth=metric(info,'revenueGrowth',100);margin=metric(info,'profitMargins',100)
            growth_score=min(100,max(0,growth*5)) if growth is not None else None
            profit_score=min(100,max(0,margin*5)) if margin is not None else None
            rows.append({'ticker':ticker,'name':info['shortName'],'sector':info.get('sector'),
                'pe_ratio':metric(info,'forwardPE') if info.get('forwardPE') is not None else metric(info,'trailingPE'),
                'ev_ebitda':metric(info,'enterpriseToEbitda'),'market_cap':metric(info,'marketCap',1e-9),
                'revenue_growth':growth,'profit_margin':margin,'roe':metric(info,'returnOnEquity',100),
                'growth_score':growth_score,'profitability_score':profit_score,
                'overall_score':(growth_score+profit_score)/2 if growth_score is not None and profit_score is not None else None,
                'provenance':provenance(ticker,info)})
        except HTTPException as e:
            if e.status_code==503:raise
            continue
    if not rows:raise HTTPException(502,'No company metrics are available from the provider')
    return rows
