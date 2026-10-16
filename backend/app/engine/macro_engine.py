import numpy as np
from typing import List, Dict, Optional
from pydantic import BaseModel
from scipy.stats import linregress

class YieldCurvePoint(BaseModel):
    tenor: str
    value: float

class MacroRegressionResult(BaseModel):
    factor: str
    beta: float
    r_squared: float
    p_value: Optional[float]

class MacroEngine:
    @staticmethod
    def get_yield_curve_data() -> List[YieldCurvePoint]:
        """
        Read the latest available daily Yahoo yield-index closes.
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
            # Missing observations produce no curve points.
            return []

        return curve

    @staticmethod
    def perform_factor_regression(asset_returns: List[float], macro_factor: List[float], factor_name: str) -> MacroRegressionResult:
        """
        Fit OLS with an intercept to caller-aligned observations.
        The two-sided slope p-value assumes independent, normally distributed
        residuals. It is unavailable with two observations or constant returns.
        This legacy helper is not connected to the current application routes.
        """
        if len(asset_returns) != len(macro_factor) or len(asset_returns) < 2:
            raise ValueError("Regression requires at least two aligned observations")

        x = np.asarray(macro_factor, dtype=float)
        y = np.asarray(asset_returns, dtype=float)
        if x.ndim != 1 or y.ndim != 1 or not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("Regression observations must be finite one-dimensional values")
        if np.ptp(x) == 0:
            raise ValueError("The regression factor must vary")

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
            p_value=float(linregress(x, y).pvalue) if len(x) > 2 and ss_tot > 0 else None
        )
