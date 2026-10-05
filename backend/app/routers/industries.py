from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()

class KeyDriver(BaseModel):
    name: str
    description: str
    typical_range: str
    importance: str  # "High", "Medium", "Low"
    why_important: str = ""  # Optional: explains why this driver matters
    example: str = ""  # Optional: real-world example

class IndustryProfile(BaseModel):
    sector: str
    description: str
    key_drivers: List[KeyDriver]
    key_metrics: List[str]
    typical_multiples: Dict[str, str]
    regulatory_considerations: List[str]

class CompanyProfile(BaseModel):
    data_status: str = "illustrative_example_not_current_market_data"
    ticker: str
    name: str
    market_cap: float
    description: str
    key_metrics: Dict[str, Any]

@router.get("/sectors")
async def list_sectors():
    """Returns available industry sectors"""
    return {
        "sectors": [
            {"id": "real_estate", "name": "Real Estate & REITs"},
            {"id": "technology", "name": "Technology & Software"},
            {"id": "energy", "name": "Energy & Utilities"},
            {"id": "healthcare", "name": "Healthcare & Biotech"},
            {"id": "financials", "name": "Financial Services"},
            {"id": "industrials", "name": "Industrials & Manufacturing"},
            {"id": "consumer", "name": "Consumer & Retail"}
        ]
    }

@router.get("/sectors/{sector_id}/profile", response_model=IndustryProfile)
async def get_sector_profile(sector_id: str):
    """Returns detailed industry analysis for a sector"""

    profiles = {
        "real_estate": IndustryProfile(
            sector="Real Estate & REITs",
            description="Real Estate Investment Trusts and property companies. Focus on income generation through rental operations and property appreciation.",
            key_drivers=[
                KeyDriver(
                    name="FFO/Share Growth",
                    description="Funds From Operations growth drives REIT valuation",
                    typical_range="3-8% annually",
                    importance="High",
                    why_important="Nareit FFO is a supplemental operating-performance measure that adjusts GAAP net income for real-estate depreciation and specified gains, losses and impairments. It is not cash flow and does not imply that property values always rise.",
                    example=""
                ),
                KeyDriver(
                    name="Occupancy Rate",
                    description="Percentage of properties leased",
                    typical_range="92-98%",
                    importance="High",
                    why_important="Occupancy affects rental revenue. Its effect on FFO depends on rents, lease terms, operating costs and financing; there is no fixed occupancy-to-FFO multiplier.",
                    example=""
                ),
                KeyDriver(
                    name="Cap Rate Compression",
                    description="Declining cap rates increase NAV",
                    typical_range="4-7%",
                    importance="High",
                    why_important="Property value equals NOI divided by the cap rate. At unchanged NOI, moving from 6% to 5.5% raises property value by about 9.1%. The equity NAV effect also depends on debt and other claims.",
                    example="Illustration: unchanged NOI divided by 4.5% gives a property value one-third higher than the same NOI divided by 6%."
                ),
                KeyDriver(
                    name="Same-Store NOI Growth",
                    description="Net operating income growth from a comparable set of existing properties",
                    typical_range="2-5% annually",
                    importance="Medium",
                    why_important="Isolates organic growth by excluding acquisitions. Shows management's ability to increase rents and reduce expenses at mature properties.",
                    example=""
                ),
                KeyDriver(
                    name="Interest Rate Environment",
                    description="Higher rates can increase financing costs and put upward pressure on cap rates, reducing value at unchanged NOI. Growth expectations, risk premiums and financing terms also matter.",
                    typical_range="Link to 10-year Treasury + spread",
                    importance="High"
                ),
                KeyDriver(
                    name="Development Pipeline",
                    description="New properties under construction. Drives future growth but increases risk.",
                    typical_range="5-15% of GAV (Gross Asset Value)",
                    importance="Medium"
                ),
                KeyDriver(
                    name="Leverage (Debt/GAV)",
                    description="Amount of debt relative to total asset value. Amplifies returns but increases risk.",
                    typical_range="30-50% for investment-grade REITs",
                    importance="Medium"
                )
            ],
            key_metrics=[
                "FFO (Funds From Operations)",
                "AFFO (Adjusted Funds From Operations)",
                "NAV per Share (Net Asset Value)",
                "Dividend Yield",
                "Payout Ratio (Dividends / FFO)",
                "Debt / EBITDA",
                "Interest Coverage",
                "Occupancy Rate",
                "Rent per Square Foot"
            ],
            typical_multiples={
                "P/FFO": "12-20x",
                "P/AFFO": "14-22x",
                "Price/NAV": "0.8-1.2x (premium/discount to NAV)",
                "Dividend Yield": "3-6%"
            },
            regulatory_considerations=[
                "Must distribute 90% of taxable income as dividends",
                "At least 75% of assets in real estate",
                "At least 75% of income from rents/mortgages/property sales",
                "No more than 25% of assets in non-qualifying securities"
            ]
        ),
        "technology": IndustryProfile(
            sector="Technology & Software",
            description="Software, cloud services, and technology platforms. Focus on recurring revenue, scalability, and network effects.",
            key_drivers=[
                KeyDriver(
                    name="ARR Growth (Annual Recurring Revenue)",
                    description="Growth in subscription-based revenue. Key indicator of business momentum.",
                    typical_range="20-50% YoY for high-growth SaaS",
                    importance="High"
                ),
                KeyDriver(
                    name="Net Revenue Retention (NRR)",
                    description="Revenue retained from existing customers including upsells/cross-sells minus churn.",
                    typical_range="110-130% for best-in-class SaaS",
                    importance="High"
                ),
                KeyDriver(
                    name="Customer Acquisition Cost (CAC) Payback",
                    description="Months to recover the cost of acquiring a customer through gross margin.",
                    typical_range="12-18 months",
                    importance="High"
                ),
                KeyDriver(
                    name="LTV/CAC Ratio",
                    description="Lifetime Value of customer relative to acquisition cost. Measures unit economics.",
                    typical_range="3x+ for healthy businesses",
                    importance="High"
                ),
                KeyDriver(
                    name="Rule of 40",
                    description="Revenue Growth % + FCF Margin % should exceed 40% for quality SaaS.",
                    typical_range=">40% is excellent",
                    importance="Medium"
                )
            ],
            key_metrics=[
                "ARR (Annual Recurring Revenue)",
                "Net Revenue Retention",
                "Gross Margin (should be 70-80%+)",
                "CAC (Customer Acquisition Cost)",
                "LTV (Lifetime Value)",
                "Churn Rate",
                "Magic Number (ARR growth / S&M spend)"
            ],
            typical_multiples={
                "EV/Revenue": "5-15x for high-growth SaaS",
                "EV/ARR": "Similar to Revenue for subscription",
                "P/E": "Often not profitable; use growth metrics"
            },
            regulatory_considerations=[
                "Data privacy regulations (GDPR, CCPA)",
                "Cybersecurity requirements",
                "Export controls for certain technologies"
            ]
        ),
        "energy": IndustryProfile(
            sector="Energy & Utilities",
            description="Oil & gas exploration/production, midstream, utilities, and renewable energy. Capital-intensive with commodity exposure.",
            key_drivers=[
                KeyDriver(
                    name="Commodity Prices (Oil, Gas, Power)",
                    description="Primary revenue driver. Prices set by global supply/demand.",
                    typical_range="Highly volatile; WTI $60-$100/bbl typical range",
                    importance="High"
                ),
                KeyDriver(
                    name="Production Growth & Reserve Replacement",
                    description="Ability to grow production and replace depleting reserves.",
                    typical_range="0-10% production growth; >100% reserve replacement",
                    importance="High"
                ),
                KeyDriver(
                    name="Lifting Costs & Break-Even Prices",
                    description="Cost to extract and produce hydrocarbons. Lower is better.",
                    typical_range="$20-$50/bbl for shale; varies by basin",
                    importance="High"
                ),
                KeyDriver(
                    name="Regulatory & ESG Pressures",
                    description="Emissions regulations, carbon pricing, renewable mandates.",
                    typical_range="Varies by jurisdiction",
                    importance="Medium"
                )
            ],
            key_metrics=[
                "Production volumes (BOE/d)",
                "Proved reserves (1P, 2P, 3P)",
                "Finding & Development costs",
                "EBITDAX (EBITDA + exploration)",
                "Free Cash Flow",
                "Net Debt / EBITDAX"
            ],
            typical_multiples={
                "EV/EBITDAX": "3-6x",
                "EV/Production ($/BOE/d)": "Varies widely by basin",
                "P/CF": "4-8x"
            },
            regulatory_considerations=[
                "Environmental permits",
                "Carbon pricing/emissions trading",
                "Renewable portfolio standards",
                "Flaring/methane regulations"
            ]
        )
    }

    if sector_id not in profiles:
        raise HTTPException(404, "Educational notes for this sector are not available yet.")
    return profiles[sector_id]

@router.get("/sectors/{sector_id}/companies", response_model=List[CompanyProfile])
async def get_sector_companies(sector_id: str):
    """Returns key companies in the sector"""

    # This would ideally pull from real-time data
    # For now, returning mock data for demonstration

    companies_db = {
        "real_estate": [
            CompanyProfile(
                ticker="PLD",
                name="Prologis Inc",
                market_cap=120000,
                description="Largest logistics REIT. Owns 1B+ sq ft of warehouses globally.",
                key_metrics={
                    "ffo_per_share": 5.20,
                    "affo_per_share": 4.95,
                    "dividend_yield": 0.028,
                    "occupancy": 0.973,
                    "p_ffo": 22.5
                }
            ),
            CompanyProfile(
                ticker="AMT",
                name="American Tower Corp",
                market_cap=95000,
                description="Telecom tower REIT. Infrastructure play on 5G buildout.",
                key_metrics={
                    "ffo_per_share": 10.80,
                    "dividend_yield": 0.032,
                    "tenant_billings": 11200,
                    "towers_owned": 225000
                }
            ),
            CompanyProfile(
                ticker="EQIX",
                name="Equinix Inc",
                market_cap=78000,
                description="Data center REIT. Critical infrastructure for cloud/internet.",
                key_metrics={
                    "ffo_per_share": 28.50,
                    "affo_per_share": 26.20,
                    "dividend_yield": 0.019,
                    "p_ffo": 27.8
                }
            )
        ],
        "technology": [
            CompanyProfile(
                ticker="MSFT",
                name="Microsoft Corporation",
                market_cap=3000000,
                description="Cloud, productivity software, gaming. Azure is key growth driver.",
                key_metrics={
                    "arr_growth": 0.25,
                    "gross_margin": 0.69,
                    "fcf_margin": 0.32,
                    "cloud_revenue_pct": 0.45
                }
            ),
            CompanyProfile(
                ticker="CRM",
                name="Salesforce Inc",
                market_cap=250000,
                description="CRM software leader. Enterprise SaaS pioneer.",
                key_metrics={
                    "arr": 35000,
                    "nrr": 1.12,
                    "gross_margin": 0.76,
                    "rule_of_40": 45
                }
            )
        ]
    }

    return companies_db.get(sector_id, [])
from app.engine.reit_engine import REITEngine

@router.get("/reit/{ticker}/analytics")
def get_reit_analytics(ticker: str, example: bool = False):
    if not example: raise HTTPException(501,"Company-specific REIT disclosures are not connected. Example schedules require example=true.")
    try:
        return REITEngine.get_portfolio_analytics(ticker)
    except Exception as e:
        return {"error": str(e)}
