from typing import List, Dict, Optional
from pydantic import BaseModel

class LeaseExpiry(BaseModel):
    year: int
    pct_of_portfolio: float
    rent_at_risk: float

class PropertyConcentration(BaseModel):
    region: str
    property_count: int
    pct_of_noi: float

class DebtMaturity(BaseModel):
    year: int
    amount: float
    type: str # "Fixed", "Floating"

class REITEngine:
    @staticmethod
    def get_portfolio_analytics(ticker: str) -> Dict:
        """
        Returns mock portfolio analytics for REITs.
        Structured for mapping to geographic heatmaps and walls.
        """
        return {
            "lease_expiry_schedule": [
                LeaseExpiry(year=2024, pct_of_portfolio=0.05, rent_at_risk=15.0),
                LeaseExpiry(year=2025, pct_of_portfolio=0.12, rent_at_risk=35.0),
                LeaseExpiry(year=2026, pct_of_portfolio=0.08, rent_at_risk=25.0),
                LeaseExpiry(year=2027, pct_of_portfolio=0.15, rent_at_risk=45.0),
                LeaseExpiry(year=2028, pct_of_portfolio=0.20, rent_at_risk=60.0),
                LeaseExpiry(year=2029, pct_of_portfolio=0.40, rent_at_risk=120.0) # Long WALT
            ],
            "geographic_concentration": [
                PropertyConcentration(region="US-CA", property_count=15, pct_of_noi=0.25),
                PropertyConcentration(region="US-TX", property_count=10, pct_of_noi=0.18),
                PropertyConcentration(region="US-NY", property_count=8, pct_of_noi=0.22),
                PropertyConcentration(region="US-FL", property_count=12, pct_of_noi=0.15),
                PropertyConcentration(region="International", property_count=20, pct_of_noi=0.20)
            ],
            "debt_maturity_wall": [
                DebtMaturity(year=2024, amount=250.0, type="Fixed"),
                DebtMaturity(year=2025, amount=100.0, type="Fixed"),
                DebtMaturity(year=2026, amount=500.0, type="Floating"),
                DebtMaturity(year=2027, amount=300.0, type="Fixed"),
                DebtMaturity(year=2028, amount=800.0, type="Fixed")
            ],
            "operating_metrics": {
                "same_store_noi_growth": 0.035,
                "occupancy_rate": 0.965,
                "unencumbered_assets_pct": 0.82
            }
        }
