import math
import os
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / '.env')

def year_over_year(series):
    if not series:
        raise ValueError('CPI history is unavailable')
    latest = series[-1]
    date = datetime.strptime(latest['date'], '%Y-%m-%d')
    prior_month = f'{date.year-1:04d}-{date.month:02d}'
    prior = next((p['value'] for p in reversed(series[:-1]) if p['date'][:7] == prior_month), None)
    if prior is None or prior <= 0:
        raise ValueError('No matching year-ago CPI observation')
    return round((latest['value']/prior-1)*100, 2)

class FredClient:
    BASE_URL = 'https://api.stlouisfed.org/fred/series/observations'
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('FRED_API_KEY')

    def get_series_data(self, series_id, limit=18):
        if os.getenv('VERTIGE_OFFLINE') == '1':
            raise ValueError('Live macro data is disabled')
        if not self.api_key:
            raise ValueError('FRED_API_KEY is required for macro data')
        try:
            response = requests.get(self.BASE_URL, params={'series_id':series_id,
                'api_key':self.api_key,'file_type':'json','sort_order':'desc','limit':limit}, timeout=10)
            response.raise_for_status()
            observations = response.json().get('observations', [])
            result = []
            for obs in sorted(observations, key=lambda x:x['date']):
                if obs['value'] == '.': continue
                value = float(obs['value'])
                if math.isfinite(value): result.append({'date':obs['date'],'value':value})
            if not result: raise ValueError('No valid observations')
            return result
        except Exception:
            # Provider exceptions can contain a request URL with the API key.
            raise ValueError(f'FRED series {series_id} is unavailable') from None

    def get_cpi(self, limit=18): return self.get_series_data('CPIAUCSL', limit)
    def get_fed_funds(self, limit=18): return self.get_series_data('FEDFUNDS', limit)
    def get_unemployment(self, limit=18): return self.get_series_data('UNRATE', limit)
    def get_cpi_yoy(self): return year_over_year(self.get_cpi(limit=24))
