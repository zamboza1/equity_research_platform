"""Statistics Canada total CPI via the Bank of Canada's public Valet API."""
import math
import os
from datetime import date
import requests


def canadian_cpi():
    if os.getenv('VERTIGE_OFFLINE') == '1':
        raise ValueError('Live macro data is disabled')
    try:
        response = requests.get(
            'https://www.bankofcanada.ca/valet/observations/V41690973/json',
            params={'recent': 72}, timeout=10)
        response.raise_for_status()
        rows = []
        for observation in response.json().get('observations', []):
            raw = observation.get('V41690973', {}).get('v')
            if raw in (None, ''):
                continue
            value = float(raw)
            if math.isfinite(value) and value > 0:
                rows.append({'date': date.fromisoformat(observation['d']).isoformat(), 'value': value})
        if not rows:
            raise ValueError('No CPI observations')
        return sorted(rows, key=lambda row: row['date'])
    except Exception:
        raise ValueError('Canadian CPI is unavailable from the Bank of Canada') from None
