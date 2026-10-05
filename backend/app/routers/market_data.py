"""Public provider adapter; unavailable values are never replaced with zero."""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import yfinance as yf
import math
import os
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError

router = APIRouter()
_cache = {}
_pool = ThreadPoolExecutor(max_workers=4)
_slots = threading.BoundedSemaphore(4)

def ticker_symbol(ticker):
    if not re.fullmatch(r'[A-Za-z0-9.^=\-]{1,25}',ticker): raise HTTPException(422,'Invalid ticker')
    return ticker.upper()

def provider_info(ticker):
    ticker=ticker_symbol(ticker)
    if os.getenv('VERTIGE_OFFLINE')=='1': raise HTTPException(503,'Live data is disabled. Enter verified assumptions manually.')
    cached=_cache.get(ticker)
    if cached and time.monotonic()-cached[0]<300: return cached[1]
    if not _slots.acquire(blocking=False): raise HTTPException(503,'Data provider is busy. Please retry.')
    future=_pool.submit(lambda:yf.Ticker(ticker).get_info())
    future.add_done_callback(lambda _: _slots.release())
    try:
        info=future.result(timeout=12)
        if not isinstance(info,dict) or not info: raise ValueError('Empty provider response')
    except (TimeoutError,Exception) as e:
        raise HTTPException(502,'Market data unavailable. Retry or enter verified values manually.') from e
    info={k:(v if not isinstance(v,float) or math.isfinite(v) else None) for k,v in info.items()}
    info['_fetched_at']=datetime.now(timezone.utc).isoformat()
    if len(_cache)>500: _cache.clear()
    _cache[ticker]=(time.monotonic(),info)
    return info

def provenance(ticker, data):
    return {'source':'Yahoo Finance via yfinance','ticker':ticker.upper(),'fetched_at':data.get('_fetched_at'),
        'price_as_of':data.get('regularMarketTime'),'financial_period_end':data.get('mostRecentQuarter'),
        'currency':data.get('currency'),'financial_currency':data.get('financialCurrency'),
        'cache_seconds':300,'note':'Provider fundamentals may lag filings. Verify dates, dilution and units before use.'}

def number(info,key,positive=False):
    v=info.get(key)
    if not isinstance(v,(int,float)) or not math.isfinite(v) or (positive and v<=0):
        raise HTTPException(502,f'Provider field {key} is unavailable or invalid. Enter verified values manually.')
    return v

@router.get('/{ticker}')
def get_market_data(ticker:str):
    info=provider_info(ticker)
    if not info.get('currency') or not info.get('financialCurrency'):
        raise HTTPException(502,'Provider did not identify both price and financial currencies')
    if info['currency']!=info['financialCurrency']:
        raise HTTPException(422,'Price and financial currencies differ. Convert all assumptions to one currency manually.')
    price=number(info,'currentPrice' if info.get('currentPrice') is not None else 'regularMarketPrice',True)
    return {'ticker':ticker.upper(),'company_name':info.get('shortName') or ticker.upper(),'current_price':price,'shares_outstanding_m':number(info,'sharesOutstanding',True)/1e6,
        'net_debt_m':(number(info,'totalDebt')-number(info,'totalCash'))/1e6,
        'start_revenue_m':number(info,'totalRevenue',True)/1e6,'currency':info['currency'],
        'market_cap':info.get('marketCap'),'volume':info.get('volume'),'provenance':provenance(ticker,info),
        'warnings':['Shares are provider shares outstanding, not a verified fully diluted share count.']}

@router.get('/quote/{ticker}')
def get_quote(ticker:str):
    info=provider_info(ticker)
    return {'symbol':ticker.upper(),'price':number(info,'currentPrice' if info.get('currentPrice') is not None else 'regularMarketPrice',True),
        'previous_close':info.get('previousClose'),'open':info.get('open'),'day_high':info.get('dayHigh'),
        'day_low':info.get('dayLow'),'volume':info.get('volume'),'avg_volume':info.get('averageVolume'),
        'market_cap':info.get('marketCap'),'currency':info.get('currency'),'provenance':provenance(ticker,info)}

@router.get('/profile/{ticker}')
def get_profile(ticker:str):
    info=provider_info(ticker)
    return {k:v for k,v in info.items() if not k.startswith('_')} | {'provenance':provenance(ticker,info)}

@router.get('/price/{ticker}')
def get_price_history(ticker:str,period:str='1y',interval:str='1d'):
    if os.getenv('VERTIGE_OFFLINE')=='1': raise HTTPException(503,'Live data is disabled')
    if period not in ['1mo','3mo','6mo','1y','2y','5y','10y'] or interval not in ['1d','1wk','1mo']:
        raise HTTPException(422,'Unsupported period or interval')
    hist=yf.Ticker(ticker_symbol(ticker)).history(period=period,interval=interval,timeout=12)
    if hist.empty: raise HTTPException(502,'No price history available')
    return [{'date':d.strftime('%Y-%m-%d'),**{k.lower():float(r[k]) for k in ['Open','High','Low','Close','Volume']}}
            for d,r in hist.dropna().iterrows()]
