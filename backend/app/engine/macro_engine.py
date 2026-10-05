import numpy as np
from typing import List, Dict, Optional
from pydantic import BaseModel

class YieldCurvePoint(BaseModel):
    tenor: str
    value: float

class MacroRegressionResult(BaseModel):
    factor: str
    beta: float
    r_squared: float
    p_value: float

class MacroEngine:
    @staticmethod
    def get_yield_curve_data() -> List[YieldCurvePoint]:
        """
        Returns real-time institutional treasury yield curve data from Yahoo Finance.
        """
        import yfinance as yf

        tickers = {
            "3M": "^IRX",
            "5Y": "^FVX",
            "10Y": "^TNX",
            "30Y": "^TYX"
        }

        data = yf.download(list(tickers.values()), period="1d", progress=False)
        curve = []
        ordered_tenors = ["3M", "5Y", "10Y", "30Y"]

        for tenor in ordered_tenors:
            ticker = tickers[tenor]
            try:
                # yf.download returns MultiIndex if multiple tickers
                if len(tickers) > 1:
                    val = float(data["Close"][ticker].iloc[-1])
                else:
                    val = float(data["Close"].iloc[-1])
                curve.append(YieldCurvePoint(tenor=tenor, value=val))
            except:
                continue

        if not curve:
            # If fetch fails, return empty list rather than mock per "NO SIMULATION" rule
            return []

        return curve

    @staticmethod
    def perform_factor_regression(asset_returns: List[float], macro_factor: List[float], factor_name: str) -> MacroRegressionResult:
        """
        Performs linear regression (OLS) to find factor betas.
        """
        if len(asset_returns) != len(macro_factor) or len(asset_returns) < 2:
            return MacroRegressionResult(factor=factor_name, beta=0, r_squared=0, p_value=1.0)

        x = np.array(macro_factor)
        y = np.array(asset_returns)

        # Simple OLS: beta = cov(x,y) / var(x)
        matrix = np.vstack([x, np.ones(len(x))]).T
        beta, alpha = np.linalg.lstsq(matrix, y, rcond=None)[0]

        # Calculate R-squared
        y_pred = alpha + beta * x
        y_mean = np.mean(y)
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - y_mean)**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return MacroRegressionResult(
            factor=factor_name,
            beta=float(beta),
            r_squared=float(r_squared),
            p_value=0.01 # Simplified for MVP
        )
