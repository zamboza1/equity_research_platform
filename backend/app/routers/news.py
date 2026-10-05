from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
import hashlib
import os
import requests
import feedparser
from app.ml.sentiment_analyzer import get_sentiment_analyzer
from app.routers.market_data import provider_info
router=APIRouter()

@router.get('/latest')
def get_market_news(limit:int=Query(default=15,ge=1,le=50),sector:str|None=None):
    if os.getenv('VERTIGE_OFFLINE')=='1':raise HTTPException(503,'Live news is disabled')
    url='https://finance.yahoo.com/news/rssindex'
    try:
        response=requests.get(url,timeout=10);response.raise_for_status()
        entries=feedparser.parse(response.content).entries
    except Exception as e:raise HTTPException(502,'News provider unavailable') from e
    if not entries:raise HTTPException(502,'News provider returned no articles')
    analyzer=get_sentiment_analyzer();news=[]
    for entry in entries:
        title=entry.get('title','Untitled');link=entry.get('link','')
        if sector and sector.lower()!='all':
            keywords={'technology':['tech','software','chip','apple','microsoft'],'real estate':['property','real estate','reit'],'financials':['bank','finance','fed'],'healthcare':['health','drug','pharma']}
            if not any(k in title.lower() for k in keywords.get(sector.lower(),[sector.lower()])):continue
        sentiment=analyzer.analyze(title)
        news.append({'id':hashlib.sha256(link.encode()).hexdigest()[:16],'title':title,
            'summary':entry.get('summary','').split('<')[0][:300], 'source':'Yahoo Finance RSS',
            'published_at':entry.get('published'),'url':link,'sentiment':sentiment['sentiment'],
            'sentiment_method':sentiment['method'],'relevance_score':None,'tickers':[],
            'fetched_at':datetime.now(timezone.utc).isoformat()})
        if len(news)>=limit:break
    return news

@router.get('/snapshot')
def snapshot():
    items=[]
    for name,ticker in [('S&P 500','^GSPC'),('Nasdaq','^IXIC'),('10Y Treasury','^TNX')]:
        try:
            data=provider_info(ticker);price=data.get('regularMarketPrice');prev=data.get('previousClose')
            if price is not None and prev and prev>0:
                items.append({'symbol':name,'price':price,'change':(price/prev-1)*100,
                    'sector':'Rates' if ticker=='^TNX' else 'Index','source':'Yahoo Finance','fetched_at':data['_fetched_at']})
        except HTTPException:continue
    if not items:raise HTTPException(503,'Market snapshot unavailable')
    return items
