from fastapi import APIRouter,HTTPException,Query
import yfinance as yf
import numpy as np
import pandas as pd
import os
from datetime import datetime,timezone
from app.routers.market_data import ticker_symbol
router=APIRouter()

def calculate_metrics(close,risk_free_rate=.04):
    if close.isna().any(): raise ValueError("Price history has missing observations; a daily-return estimate would bridge the gap")
    if not close.index.is_unique or not close.index.is_monotonic_increasing:
        raise ValueError("Price history dates must be unique and increasing")
    if not np.isfinite(close.to_numpy()).all(): raise ValueError("Price history contains nonfinite values")
    if len(close)<3 or (close<=0).any():raise ValueError('At least three positive closing prices are required')
    returns=close.pct_change(fill_method=None).dropna()
    if not np.isfinite(returns.to_numpy()).all():raise ValueError('Returns contain invalid observations')
    vol=float(returns.std(ddof=1)*np.sqrt(252));annual_return=float(returns.mean()*252)
    daily_rf=(1+risk_free_rate)**(1/252)-1
    excess=returns-daily_rf
    downside=float(np.sqrt(np.mean(np.minimum(excess,0)**2))*np.sqrt(252))
    cumulative=np.concatenate(([1.0],np.cumprod(1+returns.to_numpy())))
    peak=np.maximum.accumulate(cumulative);drawdown=cumulative/peak-1
    counts,bins=np.histogram(returns,bins=min(20,len(returns)))
    rolling = returns.rolling(21, min_periods=21).std(ddof=1) * np.sqrt(252)
    return {'annualized_volatility':vol,'annualized_return':annual_return,
        'sharpe_ratio':float(excess.mean()*252/vol) if vol>1e-12 else None,
        'sortino_ratio':float(excess.mean()*252/downside) if downside>1e-12 else None,
        'value_at_risk_95':float(np.percentile(returns,5)),'max_drawdown':float(drawdown.min()),
        'risk_free_rate':risk_free_rate,'observations':len(returns),
        'total_return':float(cumulative[-1]-1), 'prices':close.astype(float).tolist(),
        'daily_returns':returns.tolist(), 'return_dates':[str(d.date()) for d in returns.index],
        'drawdown':drawdown.tolist(), 'rolling_volatility_21d':[None if pd.isna(v) else float(v) for v in rolling],
        'returns_histogram':{'bins':bins.tolist(),'counts':counts.tolist()},
        'cumulative_performance':cumulative.tolist(),'dates':[str(d.date()) for d in close.index],
        'methodology':'Adjusted daily closes; 252 trading days; arithmetic annual return; sample volatility; downside deviation of daily excess returns; historical 5th-percentile daily return.'}


def compare_benchmark(asset, benchmark):
    # Compute each series' returns before matching dates, so the join cannot
    # invent a multi-session return by dropping an intermediate price first.
    calculate_metrics(benchmark)
    left = asset.copy(); right = benchmark.copy()
    left.index = pd.to_datetime([d.date() for d in left.index])
    right.index = pd.to_datetime([d.date() for d in right.index])
    matched = pd.concat([left.pct_change(fill_method=None).rename('asset'), right.pct_change(fill_method=None).rename('benchmark'),
                         pd.Series(left.index, index=left.index).shift(1).rename('asset_start'),
                         pd.Series(right.index, index=right.index).shift(1).rename('benchmark_start')], axis=1).dropna()
    matched = matched[matched['asset_start'] == matched['benchmark_start']]
    if len(matched) < 3:
        raise ValueError('At least three overlapping daily returns are required for a benchmark comparison')
    a, b = matched['asset'], matched['benchmark']
    active = a - b
    variance = float(b.var(ddof=1)); tracking_error = float(active.std(ddof=1) * np.sqrt(252))
    return {'observations':len(matched), 'start':str(matched.index[0].date()), 'end':str(matched.index[-1].date()),
            'beta':float(a.cov(b)/variance) if variance > 1e-16 else None,
            'correlation':float(a.corr(b)) if a.std(ddof=1) > 1e-12 and b.std(ddof=1) > 1e-12 else None,
            'annualized_active_return':float(active.mean()*252), 'tracking_error':tracking_error,
            'information_ratio':float(active.mean()*252/tracking_error) if tracking_error > 1e-12 else None,
            'dates':[str(d.date()) for d in matched.index], 'asset_returns':a.tolist(), 'benchmark_returns':b.tolist(),
            'methodology':'Simple returns computed independently, then matched on both interval start and end dates. Unmatched market sessions are excluded. Sample covariance/variance beta; sample annualized active-return volatility. Native-currency returns; no FX conversion.'}

@router.get('/metrics/{ticker}')
def get_stats(ticker:str,period:str='1y',risk_free_rate:float=Query(default=.04,ge=0,le=1),benchmark:str|None=None):
    if os.getenv('VERTIGE_OFFLINE')=='1':raise HTTPException(503,'Live price history is disabled')
    if period not in ['3mo','6mo','1y','2y','5y','10y']:raise HTTPException(422,'Unsupported lookback period')
    try:
        hist=yf.Ticker(ticker_symbol(ticker)).history(period=period,auto_adjust=True,timeout=12)
        if hist.empty:raise HTTPException(502,'Price history unavailable')
        result = calculate_metrics(hist['Close'],risk_free_rate)|{'ticker':ticker.upper(), 'period':period,
            'source':'Yahoo Finance via yfinance','fetched_at':datetime.now(timezone.utc).isoformat()}
        if benchmark:
            symbol = ticker_symbol(benchmark)
            try:
                benchmark_history = yf.Ticker(symbol).history(period=period, auto_adjust=True, timeout=12)
                result['benchmark'] = compare_benchmark(hist['Close'], benchmark_history['Close']) | {'ticker':symbol}
            except Exception:
                result['benchmark_error'] = f'Benchmark {symbol} has no usable overlapping price history. Asset results remain available.'
        return result
    except HTTPException:raise
    except ValueError as e:raise HTTPException(422,str(e)) from e
    except Exception as e:raise HTTPException(502,'Unable to load price history') from e
